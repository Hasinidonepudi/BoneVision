"""
BoneVision — Step 4: Probability Calibration (Temperature Scaling)
===================================================================
Calibrates model confidence using Temperature Scaling on the VALIDATION set.
This makes predicted probabilities more reliable (not overconfident).

What it does:
  - Finds optimal temperature T that minimises NLL on val set
  - Applies: calibrated_prob = softmax(logits / T)
  - Plots reliability diagram before and after calibration
  - Saves T to backend/model_artifacts/model_config.json
  - Reports Expected Calibration Error (ECE) before and after

Usage:
    python 04_calibrate.py
    python 04_calibrate.py --config configs/training_config.yaml
"""
import argparse
import json
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn.functional as F
import yaml
from scipy.optimize import minimize_scalar
from torch.utils.data import DataLoader
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from utils.dataset import KneeOADataset

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("calibrate")


def expected_calibration_error(
    probs: np.ndarray, labels: np.ndarray, n_bins: int = 10
) -> float:
    """
    Compute Expected Calibration Error (ECE).
    Lower is better (0 = perfectly calibrated).
    """
    confidences = probs.max(axis=1)
    predictions = probs.argmax(axis=1)
    accuracies = (predictions == labels).astype(float)

    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(labels)

    for lo, hi in zip(bin_boundaries[:-1], bin_boundaries[1:]):
        mask = (confidences > lo) & (confidences <= hi)
        if mask.sum() == 0:
            continue
        avg_conf = confidences[mask].mean()
        avg_acc = accuracies[mask].mean()
        ece += (mask.sum() / n) * abs(avg_acc - avg_conf)

    return float(ece)


def plot_reliability_diagram(
    probs_before: np.ndarray,
    probs_after: np.ndarray,
    labels: np.ndarray,
    save_path: Path,
    n_bins: int = 10,
):
    """Plot reliability diagrams before and after calibration."""
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    for ax, probs, title in [
        (axes[0], probs_before, "Before Calibration"),
        (axes[1], probs_after, "After Temperature Scaling"),
    ]:
        confidences = probs.max(axis=1)
        predictions = probs.argmax(axis=1)
        accuracies = (predictions == labels).astype(float)

        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_accs, bin_centers = [], []
        for lo, hi in zip(bin_boundaries[:-1], bin_boundaries[1:]):
            mask = (confidences > lo) & (confidences <= hi)
            if mask.sum() > 0:
                bin_accs.append(accuracies[mask].mean())
                bin_centers.append((lo + hi) / 2.0)

        ece = expected_calibration_error(probs, labels, n_bins)
        ax.plot([0, 1], [0, 1], "k--", lw=1, label="Perfect calibration")
        if bin_centers:
            ax.bar(
                bin_centers,
                bin_accs, width=0.8 / n_bins, align="center",
                alpha=0.7, color="#3b82f6", label="Model"
            )
        ax.set(xlabel="Confidence", ylabel="Accuracy", title=f"{title}\nECE={ece:.4f}")
        ax.legend()

    fig.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    logger.info("Reliability diagram saved: %s", save_path)


@torch.no_grad()
def get_logits_and_labels(model, loader: DataLoader, device: torch.device):
    """Collect raw logits (before softmax) and true labels."""
    all_logits, all_labels = [], []
    for images, labels in tqdm(loader, desc="Collecting logits", ncols=80):
        images = images.to(device)
        logits = model(images)
        all_logits.append(logits.cpu())
        all_labels.append(labels)
    return torch.cat(all_logits, dim=0), torch.cat(all_labels, dim=0)


def find_optimal_temperature(logits: torch.Tensor, labels: torch.Tensor) -> float:
    """Find T that minimises NLL on validation set using scipy scalar minimisation."""
    labels_np = labels.numpy()

    def nll(T):
        T = max(T, 1e-3)  # Avoid division by zero
        scaled = F.softmax(logits / T, dim=1).numpy()
        # Clip for numerical stability
        scaled = np.clip(scaled, 1e-8, 1.0)
        nll_val = -np.mean(np.log(scaled[np.arange(len(labels_np)), labels_np]))
        return float(nll_val)

    result = minimize_scalar(nll, bounds=(0.1, 10.0), method="bounded")
    return float(result.x)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "configs" / "training_config.yaml"),
    )
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    model_dir = Path(config["output"]["model_dir"])
    reports_dir = Path(config["output"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Load model
    mc_path = model_dir / "model_config.json"
    if not mc_path.exists():
        logger.error("model_config.json not found — run 02_train.py first.")
        sys.exit(1)
    with open(mc_path) as f:
        mc = json.load(f)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Import build_model dynamically
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
    logger.info("Model loaded: %s", mc["architecture"])

    # Validation set (used for calibration — NOT test set)
    val_ds = KneeOADataset(config["dataset"]["root"], "val", config, is_training=False)
    val_loader = DataLoader(val_ds, batch_size=32, shuffle=False, num_workers=0)
    logger.info("Val set: %d images", len(val_ds))

    logits, labels = get_logits_and_labels(model, val_loader, device)

    # Before calibration
    probs_before = F.softmax(logits, dim=1).numpy()
    ece_before = expected_calibration_error(probs_before, labels.numpy())
    logger.info("ECE before calibration: %.4f", ece_before)

    # Find optimal temperature
    T = find_optimal_temperature(logits, labels)
    logger.info("Optimal temperature T = %.4f", T)

    # After calibration
    probs_after = F.softmax(logits / T, dim=1).numpy()
    ece_after = expected_calibration_error(probs_after, labels.numpy())
    logger.info("ECE after calibration : %.4f  (improvement: %.4f)", ece_after, ece_before - ece_after)

    # Plot reliability diagram
    plot_reliability_diagram(
        probs_before, probs_after, labels.numpy(),
        reports_dir / "reliability_diagram.png"
    )

    # Update model_config.json with temperature
    mc["temperature"] = round(T, 6)
    mc["ece_before_calibration"] = round(ece_before, 4)
    mc["ece_after_calibration"] = round(ece_after, 4)
    with open(mc_path, "w") as f:
        json.dump(mc, f, indent=2)
    logger.info("Temperature saved to model_config.json")

    print(f"\n✅ Calibration complete.")
    print(f"   Temperature T = {T:.4f}")
    print(f"   ECE: {ece_before:.4f} → {ece_after:.4f} (lower is better)")
    print(f"   Next step: run 03_evaluate.py (uses calibrated temperature)")


if __name__ == "__main__":
    main()
