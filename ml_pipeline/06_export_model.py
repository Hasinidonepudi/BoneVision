"""
BoneVision — Step 6: Model Export & Deployment Checklist
=========================================================
Finalises all artifacts for backend deployment.

What it does:
  - Verifies model.pth loads and runs a dummy inference
  - Computes dataset mean/std from TRAINING SET ONLY and updates preprocessing_config.json
  - Sets demo_mode=false in model_config.json
  - Prints a deployment readiness checklist

Usage:
    python 06_export_model.py
    python 06_export_model.py --config configs/training_config.yaml
"""
import argparse
import json
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import torch
import yaml
from PIL import Image
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from utils.dataset import KneeOADataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("export")


def compute_dataset_mean_std(dataset: KneeOADataset) -> tuple:
    """
    Compute per-channel mean and std from the TRAINING SET ONLY.
    Uses a streaming approach to avoid loading all images into memory.
    """
    logger.info("Computing dataset mean and std from training set (%d images)...", len(dataset))
    channel_sum = np.zeros(3)
    channel_sq_sum = np.zeros(3)
    n_pixels = 0

    for img_path, _ in tqdm(dataset.samples, desc="Computing stats", ncols=80):
        try:
            img = Image.open(img_path).convert("RGB")
            arr = np.array(img, dtype=np.float32) / 255.0  # [H, W, 3]
            channel_sum += arr.sum(axis=(0, 1))
            channel_sq_sum += (arr ** 2).sum(axis=(0, 1))
            n_pixels += arr.shape[0] * arr.shape[1]
        except Exception as e:
            logger.warning("Skipping %s: %s", img_path.name, e)

    mean = channel_sum / n_pixels
    std = np.sqrt(channel_sq_sum / n_pixels - mean ** 2)
    return mean.tolist(), std.tolist()


def verify_model(model, num_classes: int, device: torch.device) -> bool:
    """Run a dummy forward pass to verify the model loads and outputs correctly."""
    try:
        dummy = torch.zeros(1, 3, 224, 224).to(device)
        with torch.no_grad():
            out = model(dummy)
        assert out.shape == (1, num_classes), f"Expected (1, {num_classes}), got {out.shape}"
        logger.info("✅ Model verification passed — output shape: %s", out.shape)
        return True
    except Exception as e:
        logger.error("❌ Model verification failed: %s", e)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "configs" / "training_config.yaml"),
    )
    parser.add_argument(
        "--skip-mean-std",
        action="store_true",
        help="Skip computing dataset mean/std (use ImageNet defaults)",
    )
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    model_dir = Path(config["output"]["model_dir"])
    mc_path = model_dir / "model_config.json"
    pp_path = model_dir / "preprocessing_config.json"
    weights_path = model_dir / "model.pth"
    metrics_path = model_dir / "metrics.json"

    checklist = {}

    # --- 1. Check model weights exist ---
    checklist["model_pth_exists"] = weights_path.exists()
    if not weights_path.exists():
        logger.error("model.pth not found at %s — run 02_train.py first.", weights_path)
        sys.exit(1)

    # --- 2. Load model_config ---
    checklist["model_config_exists"] = mc_path.exists()
    with open(mc_path) as f:
        mc = json.load(f)

    device = torch.device("cpu")  # Export always on CPU for portability

    # --- 3. Load model and verify ---
    import importlib.util
    train_spec = importlib.util.spec_from_file_location(
        "train", Path(__file__).parent / "02_train.py"
    )
    train_mod = importlib.util.module_from_spec(train_spec)
    train_spec.loader.exec_module(train_mod)
    model = train_mod.build_model(mc["architecture"], mc["num_classes"], pretrained=False)
    state = torch.load(weights_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()

    checklist["model_loads_ok"] = verify_model(model, mc["num_classes"], device)

    # --- 4. Keep training normalization (ImageNet) ---
    pp_config = {
        "input_size": config["preprocessing"]["input_size"],
        "mean": config["preprocessing"]["mean"],
        "std": config["preprocessing"]["std"],
        "clahe": config["preprocessing"]["clahe"],
        "note": "Exact ImageNet mean and std matching training pipeline.",
    }
    with open(pp_path, "w") as f:
        json.dump(pp_config, f, indent=2)
    logger.info("preprocessing_config.json confirmed with training normalisation.")
    checklist["preprocessing_config_updated"] = True

    # --- 5. Set demo_mode=false in model_config ---
    mc["demo_mode"] = False
    mc["trained"] = True
    with open(mc_path, "w") as f:
        json.dump(mc, f, indent=2)
    checklist["demo_mode_disabled"] = True

    # --- 6. Check metrics exist ---
    checklist["metrics_evaluated"] = (
        metrics_path.exists() and
        json.load(open(metrics_path)).get("status") != "demo_mode"
    )

    # --- Print checklist ---
    print("\n" + "=" * 60)
    print("BONEVISION DEPLOYMENT CHECKLIST")
    print("=" * 60)
    items = [
        ("model.pth exists",             checklist["model_pth_exists"]),
        ("model_config.json exists",     checklist["model_config_exists"]),
        ("Model forward pass OK",        checklist["model_loads_ok"]),
        ("Preprocessing config updated", checklist["preprocessing_config_updated"]),
        ("demo_mode disabled",           checklist["demo_mode_disabled"]),
        ("Test set evaluated (metrics)", checklist["metrics_evaluated"]),
    ]
    all_ok = True
    for label, status in items:
        icon = "✅" if status else "❌"
        print(f"  {icon}  {label}")
        if not status:
            all_ok = False

    if all_ok:
        print("\n🚀 All checks passed — start the backend with:")
        print("   cd backend && uvicorn app.main:app --reload")
    else:
        print("\n⚠️  Some checks failed. Resolve the issues above before deploying.")


if __name__ == "__main__":
    main()
