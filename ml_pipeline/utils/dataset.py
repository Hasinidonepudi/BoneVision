"""
BoneVision Dataset Utility
PyTorch Dataset class for the Knee Osteoarthritis Classification dataset.
Handles CLAHE preprocessing and appropriate augmentation.
"""
import logging
from pathlib import Path
from typing import List, Tuple, Optional

import cv2
import numpy as np
from PIL import Image

import torch
from torch.utils.data import Dataset
import torchvision.transforms as T

logger = logging.getLogger(__name__)


def apply_clahe(pil_image: Image.Image, clip_limit: float = 2.0,
                tile_grid_size: Tuple[int, int] = (8, 8)) -> Image.Image:
    """
    Apply CLAHE contrast enhancement on the L channel of LAB colour space.
    Improves contrast in X-ray images without changing overall brightness.
    """
    cv_img = cv2.cvtColor(np.array(pil_image.convert("RGB")), cv2.COLOR_RGB2BGR)
    lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_enhanced = clahe.apply(l_ch)
    lab_enhanced = cv2.merge([l_enhanced, a_ch, b_ch])
    result = cv2.cvtColor(cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2RGB)
    return Image.fromarray(result)


def get_transforms(config: dict, is_training: bool = False) -> T.Compose:
    """
    Build torchvision transform pipeline.
    CLAHE is applied separately in __getitem__ before this.

    Args:
        config: preprocessing config dict (input_size, mean, std, augmentation).
        is_training: If True, include data augmentation transforms.

    Returns:
        A composed torchvision transform.
    """
    size = config["preprocessing"]["input_size"]
    mean = config["preprocessing"]["mean"]
    std = config["preprocessing"]["std"]
    aug = config.get("augmentation", {})

    base = [T.Resize((size, size))]

    if is_training:
        if aug.get("horizontal_flip", True):
            base.append(T.RandomHorizontalFlip(p=0.5))
        rot = aug.get("rotation_degrees", 10)
        if rot > 0:
            base.append(T.RandomRotation(degrees=rot))
        bj = aug.get("brightness_jitter", 0.2)
        cj = aug.get("contrast_jitter", 0.2)
        if bj > 0 or cj > 0:
            base.append(T.ColorJitter(brightness=bj, contrast=cj))
        blur_k = aug.get("gaussian_blur_kernel", 3)
        blur_s = aug.get("gaussian_blur_sigma", [0.1, 2.0])
        if blur_k > 0:
            base.append(T.RandomApply([T.GaussianBlur(kernel_size=blur_k, sigma=blur_s)], p=0.3))

    base += [T.ToTensor(), T.Normalize(mean=mean, std=std)]
    return T.Compose(base)


class KneeOADataset(Dataset):
    """
    PyTorch Dataset for the Knee Osteoarthritis Classification dataset.

    Folder structure expected:
        root/
          train/Normal/, train/Osteopenia/, train/Osteoporosis/
          val/Normal/,   val/Osteopenia/,   val/Osteoporosis/
          test/Normal/,  test/Osteopenia/,  test/Osteoporosis/

    Augmentation is ONLY applied during training, and NOT to files
    whose name contains '_aug' (already pre-augmented).
    """

    VALID_EXTS = {".jpg", ".jpeg", ".png", ".bmp"}

    def __init__(self, root_dir: str, split: str, config: dict,
                 is_training: bool = False):
        """
        Args:
            root_dir: Path to the dataset root directory.
            split: One of 'train', 'val', 'test'.
            config: Full training_config dict (loaded from YAML).
            is_training: Enable augmentation when True.
        """
        self.root = Path(root_dir) / split
        self.split = split
        self.is_training = is_training
        self.config = config

        clahe_cfg = config["preprocessing"]["clahe"]
        self.clahe_clip = clahe_cfg["clip_limit"]
        self.clahe_tile = tuple(clahe_cfg["tile_grid_size"])

        # Build class → index mapping from config (preserves order)
        class_names: List[str] = config["dataset"]["classes"]
        self.class_to_idx = {c: i for i, c in enumerate(class_names)}
        self.idx_to_class = {i: c for c, i in self.class_to_idx.items()}

        # Discover all samples
        self.samples: List[Tuple[Path, int]] = self._collect_samples()

        # Transforms (no augmentation for _aug files even in training)
        self.transform = get_transforms(config, is_training=False)   # base
        self.train_transform = get_transforms(config, is_training=True)  # with aug

        logger.info(
            "KneeOADataset | split=%s | samples=%d | augment=%s",
            split, len(self.samples), is_training,
        )

    def _collect_samples(self) -> List[Tuple[Path, int]]:
        samples = []
        for class_name, idx in self.class_to_idx.items():
            class_dir = self.root / class_name
            if not class_dir.exists():
                logger.warning("Class directory not found: %s", class_dir)
                continue
            for img_path in sorted(class_dir.iterdir()):
                if img_path.suffix.lower() in self.VALID_EXTS:
                    samples.append((img_path, idx))
        return samples

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, int]:
        img_path, label = self.samples[idx]

        # Load image
        try:
            pil_img = Image.open(img_path).convert("RGB")
        except Exception as e:
            logger.error("Failed to open image %s: %s", img_path, e)
            # Return a black image as fallback to avoid crashing the loader
            pil_img = Image.new("RGB", (224, 224), color=0)

        # Apply CLAHE contrast enhancement
        try:
            pil_img = apply_clahe(pil_img, self.clahe_clip, self.clahe_tile)
        except Exception as e:
            logger.warning("CLAHE failed for %s: %s — skipping CLAHE.", img_path.name, e)

        # Choose transform: skip augmentation for pre-augmented files
        is_pre_aug = "_aug" in img_path.stem.lower()
        if self.is_training and not is_pre_aug:
            tensor = self.train_transform(pil_img)
        else:
            tensor = self.transform(pil_img)

        return tensor, label

    def get_class_weights(self) -> torch.Tensor:
        """
        Compute inverse-frequency class weights for loss balancing.
        (Useful even on balanced datasets as a safety check.)
        """
        counts = torch.zeros(len(self.class_to_idx))
        for _, label in self.samples:
            counts[label] += 1
        total = counts.sum()
        weights = total / (len(counts) * counts)
        return weights
