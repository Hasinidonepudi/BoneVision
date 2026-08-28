"""
BoneVision — Step 5: Grad-CAM Sample Visualisations
====================================================
Generates Grad-CAM heatmap overlays for sample images from each class.
Run after training to visually inspect what the model is attending to.

What it outputs:
  - outputs/gradcam_samples/Normal_1.png, Normal_2.png, Normal_3.png
  - outputs/gradcam_samples/Osteopenia_1.png, ...
  - outputs/gradcam_samples/Osteoporosis_1.png, ...

Usage:
    python 05_gradcam_samples.py
    python 05_gradcam_samples.py --config configs/training_config.yaml --n 3
"""
import argparse
import json
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import cv2
import numpy as np
import torch
import yaml
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from utils.dataset import KneeOADataset, apply_clahe, get_transforms
from utils.gradcam import GradCAM, get_target_layer

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("gradcam_samples")


@torch.no_grad()
def find_correct_predictions(model, dataset, class_idx, n, device, config):
    """
    Find N correctly predicted samples for a given class.
    Returns list of (input_tensor, original_pil_image).
    """
    found = []
    transform = get_transforms(config, is_training=False)

    for img_path, label in dataset.samples:
        if label != class_idx:
            continue
        if len(found) >= n:
            break

        try:
            pil_img = Image.open(img_path).convert("RGB")
            pil_clahe = apply_clahe(pil_img,
                                    dataset.clahe_clip,
                                    dataset.clahe_tile)
            tensor = transform(pil_clahe).unsqueeze(0).to(device)

            output = model(tensor)
            pred = output.argmax(dim=1).item()
            if pred == class_idx:
                found.append((tensor, pil_img, img_path.name))
        except Exception as e:
            logger.warning("Skipping %s: %s", img_path.name, e)

    if len(found) < n:
        logger.warning(
            "Only found %d/%d correctly predicted samples for class %d",
            len(found), n, class_idx
        )
    return found


def generate_sample_overlays(model, arch_name, dataset, class_names, output_dir, n, device, config):
    """Generate Grad-CAM overlays for N samples of each class."""
    output_dir.mkdir(parents=True, exist_ok=True)
    target_layer = get_target_layer(model, arch_name)

    for class_idx, class_name in enumerate(class_names):
        logger.info("Generating Grad-CAM for class: %s", class_name)
        samples = find_correct_predictions(model, dataset, class_idx, n, device, config)

        for i, (tensor, pil_orig, fname) in enumerate(samples, start=1):
            try:
                # Enable grad for Grad-CAM
                tensor_g = tensor.clone().requires_grad_(True)
                cam = GradCAM(model, target_layer)
                heatmap = cam.generate_heatmap(tensor_g, class_idx=class_idx)
                cam.remove_hooks()

                # Build overlay
                w, h = pil_orig.size
                orig_bgr = cv2.cvtColor(np.array(pil_orig), cv2.COLOR_RGB2BGR)
                hm_resized = cv2.resize(heatmap, (w, h))
                hm_uint8 = (hm_resized * 255).astype(np.uint8)
                colored = cv2.applyColorMap(hm_uint8, cv2.COLORMAP_JET)
                gray = cv2.cvtColor(orig_bgr, cv2.COLOR_BGR2GRAY)
                gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
                overlay = (0.5 * colored + 0.5 * gray_bgr).astype(np.uint8)

                # Side-by-side: original | heatmap
                side_by_side = np.hstack([gray_bgr, overlay])

                # Add label text
                label_text = f"{class_name} — {fname}"
                cv2.putText(
                    side_by_side, label_text, (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2
                )
                cv2.putText(
                    side_by_side, "Original", (10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1
                )
                cv2.putText(
                    side_by_side, "Grad-CAM", (w + 10, h - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1
                )

                save_path = output_dir / f"{class_name}_{i}.png"
                cv2.imwrite(str(save_path), side_by_side)
                logger.info("  Saved: %s", save_path)

            except Exception as e:
                logger.error("Failed to generate Grad-CAM for %s sample %d: %s", class_name, i, e)

    logger.info("✅ Grad-CAM samples saved to: %s", output_dir)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "configs" / "training_config.yaml"),
    )
    parser.add_argument("--n", type=int, default=3, help="Samples per class")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    model_dir = Path(config["output"]["model_dir"])
    output_dir = Path(config["output"]["gradcam_dir"])

    mc_path = model_dir / "model_config.json"
    if not mc_path.exists():
        logger.error("model_config.json not found — run 02_train.py first.")
        sys.exit(1)
    with open(mc_path) as f:
        mc = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    import importlib.util
    train_spec = importlib.util.spec_from_file_location(
        "train", Path(__file__).parent / "02_train.py"
    )
    train_mod = importlib.util.module_from_spec(train_spec)
    train_spec.loader.exec_module(train_mod)
    model = train_mod.build_model(mc["architecture"], mc["num_classes"], pretrained=False)
    state = torch.load(model_dir / "model.pth", map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model = model.to(device).eval()

    test_ds = KneeOADataset(config["dataset"]["root"], "test", config, is_training=False)
    class_names = config["dataset"]["classes"]

    generate_sample_overlays(
        model, mc["architecture"], test_ds, class_names, output_dir, args.n, device, config
    )


if __name__ == "__main__":
    main()
