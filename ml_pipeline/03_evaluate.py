"""
BoneVision — Step 3: Final Test Set Evaluation
================================================
⚠️  WARNING: Only run this ONCE after training is complete.
This script touches the HELD-OUT TEST SET for the first and only time.
Do NOT run this multiple times to tune thresholds — that leaks the test set.

What it outputs:
  - Accuracy, Precision, Recall/Sensitivity, Specificity, F1, ROC-AUC, PR-AUC
  - Per-class metrics
  - Confusion matrix (saved as image)
  - ROC curves (saved as image)
  - PR curves (saved as image)
  - backend/model_artifacts/metrics.json

Usage:
    python 03_evaluate.py
    python 03_evaluate.py --config configs/training_config.yaml
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
from torch.utils.data import DataLoader
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from utils.dataset import KneeOADataset
from utils.metrics import (
    compute_all_metrics,
    plot_confusion_matrix,
    plot_roc_curves,
    plot_pr_curves,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("evaluate")


def load_model(model_dir: Path, config: dict):
    """Load the trained model from model_artifacts/."""
    mc_path = model_dir / "model_config.json"
    weights_path = model_dir / "model.pth"

    if not mc_path.exists():
        logger.error("model_config.json not found at %s. Run 02_train.py first.", mc_path)
        sys.exit(1)
    if not weights_path.exists():
        logger.error("model.pth not found at %s. Run 02_train.py first.", weights_path)
        sys.exit(1)

    with open(mc_path) as f:
        mc = json.load(f)

    arch_name = mc["architecture"]
    num_classes = mc["num_classes"]

    # Import build_model from training script
    from utils.dataset import KneeOADataset  # noqa
    import importlib.util
    train_spec = importlib.util.spec_from_file_location(
        "train", Path(__file__).parent / "02_train.py"
    )
    train_mod = importlib.util.module_from_spec(train_spec)
    train_spec.loader.exec_module(train_mod)
    model = train_mod.build_model(arch_name, num_classes, pretrained=False)

    state = torch.load(weights_path, map_location="cpu", weights_only=True)
    model.load_state_dict(state)
    model.eval()
    logger.info("Loaded model: %s", arch_name)
    return model, mc


@torch.no_grad()
def run_inference(model, loader: DataLoader, device: torch.device):
    """Run model over entire dataloader, collect probs and labels."""
    all_probs = []
    all_labels = []
    for images, labels in tqdm(loader, desc="Evaluating", ncols=80):
        images = images.to(device)
        outputs = model(images)
        probs = torch.softmax(outputs, dim=1).cpu().numpy()
        all_probs.append(probs)
        all_labels.append(labels.numpy())
    return np.concatenate(all_probs, axis=0), np.concatenate(all_labels, axis=0)


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

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info("Device: %s", device)

    # Load model
    model, mc = load_model(model_dir, config)
    model = model.to(device)

    class_names = config["dataset"]["classes"]
    temperature = float(mc.get("temperature", 1.0))
    logger.info("Temperature scaling factor: %.3f", temperature)

    # ⚠️ TEST SET — touched here for the first and only time
    logger.info("Loading TEST SET (held-out)...")
    test_ds = KneeOADataset(config["dataset"]["root"], "test", config, is_training=False)
    test_loader = DataLoader(
        test_ds,
        batch_size=config["training"]["batch_size"],
        shuffle=False,
        num_workers=0,
    )
    logger.info("Test set: %d images", len(test_ds))

    # Run inference
    y_pred_proba, y_true = run_inference(model, test_loader, device)

    # Apply temperature scaling
    import torch.nn.functional as F
    logits = torch.log(torch.tensor(y_pred_proba + 1e-8))
    calibrated = F.softmax(logits / temperature, dim=1).numpy()

    # Compute all metrics
    logger.info("Computing metrics...")
    metrics = compute_all_metrics(y_true, calibrated, class_names)
    metrics["architecture"] = mc["architecture"]
    metrics["model_version"] = mc.get("model_name", "bonevision-v1.0")
    metrics["temperature"] = temperature
    metrics["evaluation_split"] = "test"
    metrics["status"] = "evaluated"

    # Print report
    print("\n" + "=" * 60)
    print("BONEVISION TEST SET EVALUATION RESULTS")
    print("=" * 60)
    print(f"Model        : {metrics['model_version']}")
    print(f"Architecture : {metrics['architecture']}")
    print(f"Test samples : {metrics['n_samples']}")
    print("-" * 60)
    print(f"Accuracy     : {metrics['accuracy']:.4f}")
    print(f"Macro Prec.  : {metrics['macro_precision']:.4f}")
    print(f"Macro Recall : {metrics['macro_recall']:.4f}")
    print(f"Macro F1     : {metrics['macro_f1']:.4f}")
    print(f"ROC-AUC      : {metrics['roc_auc_macro']:.4f}")
    print(f"PR-AUC       : {metrics['pr_auc_macro']:.4f}")
    print("\nPer-class metrics:")
    for cls, m in metrics["per_class"].items():
        print(
            f"  {cls:<15} | Prec={m['precision']:.3f} | "
            f"Recall={m['recall_sensitivity']:.3f} | "
            f"Spec={m['specificity']:.3f} | F1={m['f1_score']:.3f}"
        )
    print("\nClassification Report:")
    print(metrics["classification_report"])

    # Save metrics.json
    metrics_path = model_dir / "metrics.json"
    # Remove non-serialisable classification_report from saved metrics
    save_metrics = {k: v for k, v in metrics.items() if k != "classification_report"}
    save_metrics["classification_report_text"] = metrics["classification_report"]
    with open(metrics_path, "w") as f:
        json.dump(save_metrics, f, indent=2)
    logger.info("Metrics saved to: %s", metrics_path)

    # Save plots
    plot_confusion_matrix(
        metrics["confusion_matrix"], class_names,
        reports_dir / "confusion_matrix.png", title="Test Set Confusion Matrix"
    )
    plot_roc_curves(y_true, calibrated, class_names, reports_dir / "roc_curves.png")
    plot_pr_curves(y_true, calibrated, class_names, reports_dir / "pr_curves.png")

    logger.info("✅ Evaluation complete. Next step: run 04_calibrate.py (if not already done)")


if __name__ == "__main__":
    main()
