"""
BoneVision Image Preprocessing Service
Applies the EXACT same preprocessing pipeline used during model training.
Config is loaded from model_artifacts/preprocessing_config.json so that
training and inference are always in sync.
"""
import json
import logging
from io import BytesIO
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# Lazy import torch to allow the app to start in demo mode even if torch
# is not installed (though it is listed in requirements.txt).
try:
    import torch
    import torchvision.transforms as T
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not found — preprocessing will run in numpy-only mode.")


def load_preprocessing_config(config_path: Path) -> dict:
    """
    Load preprocessing parameters from the JSON config saved during training.

    Returns a dict with keys: input_size, mean, std, clahe.
    Falls back to ImageNet defaults if the file is missing.
    """
    if config_path.exists():
        with open(config_path, "r") as f:
            cfg = json.load(f)
        logger.info("Loaded preprocessing config from %s", config_path)
        return cfg
    else:
        logger.warning(
            "preprocessing_config.json not found at %s — using ImageNet defaults.",
            config_path,
        )
        return {
            "input_size": 224,
            "mean": [0.485, 0.456, 0.406],
            "std": [0.229, 0.224, 0.225],
            "clahe": {"clip_limit": 2.0, "tile_grid_size": [8, 8]},
        }


def apply_clahe(pil_image: Image.Image, clahe_cfg: dict) -> Image.Image:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalisation) to
    improve contrast in X-ray images — applied per-channel on the L channel
    of the LAB colour space.

    Args:
        pil_image: Input PIL image (RGB).
        clahe_cfg: Dict with 'clip_limit' and 'tile_grid_size'.

    Returns:
        PIL image with enhanced contrast.
    """
    clip_limit = clahe_cfg.get("clip_limit", 2.0)
    tile_grid_size = tuple(clahe_cfg.get("tile_grid_size", [8, 8]))

    # Convert PIL → OpenCV BGR
    cv_img = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    # Convert to LAB and apply robust exposure normalization + CLAHE on L channel
    lab = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)

    # Rectification for Drawback #1: Photometric Exposure Standardization
    # Normalizes scanner tube kVp/mAs exposure variations by stretching 1st to 99th percentiles
    p1, p99 = np.percentile(l_ch, (1, 99))
    if p99 > p1:
        l_norm = np.clip((l_ch.astype(np.float32) - p1) / (p99 - p1) * 255.0, 0, 255).astype(np.uint8)
    else:
        l_norm = l_ch

    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=tile_grid_size)
    l_enhanced = clahe.apply(l_norm)

    lab_enhanced = cv2.merge([l_enhanced, a_ch, b_ch])
    result_bgr = cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR)
    result_rgb = cv2.cvtColor(result_bgr, cv2.COLOR_BGR2RGB)

    return Image.fromarray(result_rgb)


def preprocess_image(image_bytes: bytes, config: dict):
    """
    Full preprocessing pipeline — identical to training pipeline.

    Steps:
      1. Open image with PIL, convert to RGB.
      2. Apply CLAHE contrast enhancement.
      3. Resize to config['input_size'] × config['input_size'].
      4. Convert to tensor (C, H, W) and normalise with training mean/std.

    Args:
        image_bytes: Raw image bytes from upload.
        config: Dict from load_preprocessing_config().

    Returns:
        torch.Tensor of shape [1, 3, H, W] if torch is available,
        otherwise a numpy array [1, H, W, 3] for demo/fallback use.
    """
    size = config.get("input_size", 224)
    mean = config.get("mean", [0.485, 0.456, 0.406])
    std = config.get("std", [0.229, 0.224, 0.225])
    clahe_cfg = config.get("clahe", {"clip_limit": 2.0, "tile_grid_size": [8, 8]})

    # 1. Open + convert to RGB
    pil_img = Image.open(BytesIO(image_bytes)).convert("RGB")

    # 2. CLAHE contrast enhancement
    pil_img = apply_clahe(pil_img, clahe_cfg)

    # 3. Resize
    pil_img = pil_img.resize((size, size), Image.LANCZOS)

    if TORCH_AVAILABLE:
        # 4. ToTensor + Normalise
        transform = T.Compose([
            T.ToTensor(),                          # [0,255] uint8 → [0,1] float
            T.Normalize(mean=mean, std=std),       # ImageNet normalisation
        ])
        tensor = transform(pil_img).unsqueeze(0)  # [1, 3, H, W]
        logger.debug("Preprocessed image to tensor shape: %s", tensor.shape)
        return tensor
    else:
        # Fallback: return normalised numpy array
        arr = np.array(pil_img, dtype=np.float32) / 255.0
        arr = (arr - np.array(mean)) / np.array(std)
        return arr[np.newaxis]  # [1, H, W, 3]
