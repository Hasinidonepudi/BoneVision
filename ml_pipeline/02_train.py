"""
BoneVision — Step 2: Multi-Architecture Training
==================================================
Trains EfficientNet-B0 and MobileNetV3-Large with transfer learning.
Selects the best model based on VALIDATION AUC (not training accuracy).
The test set is NEVER touched here.

What it outputs:
  - checkpoints/{arch}_best.pth  — best checkpoint per architecture
  - backend/model_artifacts/model.pth — best overall model (ready for API)
  - backend/model_artifacts/model_config.json — updated with winning arch

Usage:
    python 02_train.py
    python 02_train.py --config configs/training_config.yaml
    python 02_train.py --arch efficientnet_b0  # train single arch
"""
import argparse
import json
import logging
import random
import shutil
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import numpy as np
import yaml
from tqdm import tqdm

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
import torchvision.models as tvm
from sklearn.metrics import roc_auc_score

# Add ml_pipeline to path for utils imports
sys.path.insert(0, str(Path(__file__).parent))
from utils.dataset import KneeOADataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("train")


# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
def set_seeds(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.deterministic = True


# ---------------------------------------------------------------------------
# Model construction
# ---------------------------------------------------------------------------
def build_model(arch_name: str, num_classes: int, pretrained: bool = True) -> nn.Module:
    """
    Load a pretrained backbone and replace the final classifier layer.
    All ImageNet pretrained weights are used as a starting point.
    """
    arch = arch_name.lower()
    weights_arg = "DEFAULT" if pretrained else None

    if "efficientnet_b0" in arch:
        model = tvm.efficientnet_b0(weights=weights_arg)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)

    elif "mobilenet_v3_large" in arch or "mobilenet" in arch:
        model = tvm.mobilenet_v3_large(weights=weights_arg)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)

    elif "efficientnet_b3" in arch:
        model = tvm.efficientnet_b3(weights=weights_arg)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)

    elif "resnet50" in arch:
        model = tvm.resnet50(weights=weights_arg)
        model.fc = nn.Linear(model.fc.in_features, num_classes)

    else:
        raise ValueError(f"Unsupported architecture: {arch_name}")

    return model


def freeze_backbone(model: nn.Module, arch_name: str):
    """Freeze all parameters except the classification head."""
    arch = arch_name.lower()
    if "efficientnet" in arch or "mobilenet" in arch:
        for param in model.features.parameters():
            param.requires_grad = False
    elif "resnet" in arch:
        for name, param in model.named_parameters():
            if "fc" not in name:
                param.requires_grad = False
    logger.info("  Backbone frozen (head-only training for warm-up epochs).")


def unfreeze_backbone(model: nn.Module):
    """Unfreeze all parameters for full fine-tuning."""
    for param in model.parameters():
        param.requires_grad = True
    logger.info("  Backbone unfrozen — full fine-tuning.")


# ---------------------------------------------------------------------------
# Single epoch routines
# ---------------------------------------------------------------------------
def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    optimizer: torch.optim.Optimizer,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, float]:
    model.train()
    total_loss = 0.0
    correct = 0
    total = 0

    for images, labels in tqdm(loader, desc="  Train", leave=False, ncols=80):
        images, labels = images.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(images)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        total_loss += loss.item() * images.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += images.size(0)

    return {"loss": total_loss / total, "accuracy": correct / total}


@torch.no_grad()
def validate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
    num_classes: int,
) -> Dict[str, float]:
    model.eval()
    total_loss = 0.0
    correct = 0
    total = 0
    all_probs = []
    all_labels = []

    for images, labels in tqdm(loader, desc="  Val  ", leave=False, ncols=80):
        images, labels = images.to(device), labels.to(device)
        outputs = model(images)
        loss = criterion(outputs, labels)

        total_loss += loss.item() * images.size(0)
        probs = torch.softmax(outputs, dim=1)
        preds = probs.argmax(dim=1)
        correct += (preds == labels).sum().item()
        total += images.size(0)

        all_probs.append(probs.cpu().numpy())
        all_labels.append(labels.cpu().numpy())

    all_probs = np.concatenate(all_probs, axis=0)
    all_labels = np.concatenate(all_labels, axis=0)

    try:
        auc = float(roc_auc_score(all_labels, all_probs, multi_class="ovr", average="macro"))
    except Exception:
        auc = 0.0

    return {
        "loss": total_loss / total,
        "accuracy": correct / total,
        "auc": auc,
    }


# ---------------------------------------------------------------------------
# Full training loop for one architecture
# ---------------------------------------------------------------------------
def train_architecture(
    arch_name: str,
    config: dict,
    train_loader: DataLoader,
    val_loader: DataLoader,
    device: torch.device,
    checkpoints_dir: Path,
) -> Dict:
    """Train one architecture end-to-end with early stopping."""

    num_classes = len(config["dataset"]["classes"])
    epochs = config["training"]["epochs"]
    patience = config["training"]["early_stopping_patience"]
    freeze_epochs = next(
        (a.get("freeze_backbone_epochs", 0)
         for a in config["architectures"] if a["name"] == arch_name),
        0,
    )
    pretrained = next(
        (a.get("pretrained", True)
         for a in config["architectures"] if a["name"] == arch_name),
        True,
    )

    logger.info("\n%s", "=" * 60)
    logger.info("Training: %s | pretrained=%s | freeze_epochs=%d",
                arch_name, pretrained, freeze_epochs)
    logger.info("Device: %s | Epochs: %d | Patience: %d", device, epochs, patience)
    logger.info("=" * 60)

    model = build_model(arch_name, num_classes, pretrained=pretrained).to(device)

    # Warm-up: freeze backbone for first N epochs
    if freeze_epochs > 0:
        freeze_backbone(model, arch_name)

    criterion = nn.CrossEntropyLoss()
    opt_cfg = config["optimizer"]
    optimizer = torch.optim.AdamW(
        filter(lambda p: p.requires_grad, model.parameters()),
        lr=opt_cfg["lr"],
        weight_decay=opt_cfg["weight_decay"],
    )
    sch_cfg = config["scheduler"]
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
        optimizer, T_max=epochs, eta_min=sch_cfg["eta_min"]
    )

    best_val_auc = 0.0
    best_epoch = 0
    patience_counter = 0
    ckpt_path = checkpoints_dir / f"{arch_name}_best.pth"
    checkpoints_dir.mkdir(parents=True, exist_ok=True)

    # Header row
    logger.info(
        "%-6s | %-10s | %-10s | %-10s | %-10s | %-10s",
        "Epoch", "Train Loss", "Train Acc", "Val Loss", "Val Acc", "Val AUC",
    )
    logger.info("-" * 65)

    for epoch in range(1, epochs + 1):
        # Unfreeze backbone after warm-up
        if epoch == freeze_epochs + 1 and freeze_epochs > 0:
            unfreeze_backbone(model)
            # Rebuild optimizer with all params
            optimizer = torch.optim.AdamW(
                model.parameters(), lr=opt_cfg["lr"], weight_decay=opt_cfg["weight_decay"]
            )
            scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(
                optimizer, T_max=epochs - freeze_epochs, eta_min=sch_cfg["eta_min"]
            )

        t0 = time.time()
        train_m = train_one_epoch(model, train_loader, optimizer, criterion, device)
        val_m = validate(model, val_loader, criterion, device, num_classes)
        scheduler.step()

        logger.info(
            "%-6d | %-10.4f | %-10.4f | %-10.4f | %-10.4f | %-10.4f  [%.1fs]",
            epoch,
            train_m["loss"], train_m["accuracy"],
            val_m["loss"], val_m["accuracy"], val_m["auc"],
            time.time() - t0,
        )

        # Early stopping on val AUC
        if val_m["auc"] > best_val_auc:
            best_val_auc = val_m["auc"]
            best_epoch = epoch
            patience_counter = 0
            torch.save(model.state_dict(), ckpt_path)
            logger.info("  ✅ New best val_auc=%.4f — checkpoint saved.", best_val_auc)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(
                    "  Early stopping at epoch %d (no improvement for %d epochs).",
                    epoch, patience,
                )
                break

    logger.info(
        "\n%s best result: epoch=%d, val_auc=%.4f", arch_name, best_epoch, best_val_auc
    )
    return {
        "arch_name": arch_name,
        "best_val_auc": best_val_auc,
        "best_epoch": best_epoch,
        "checkpoint_path": str(ckpt_path),
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser(description="BoneVision training")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "configs" / "training_config.yaml"),
    )
    parser.add_argument("--arch", default=None, help="Train a single architecture only")
    args = parser.parse_args()

    with open(args.config) as f:
        config = yaml.safe_load(f)

    set_seeds(config["seed"])

    # Device selection
    if torch.cuda.is_available():
        device = torch.device("cuda")
        logger.info("Using GPU: %s", torch.cuda.get_device_name(0))
    else:
        device = torch.device("cpu")
        logger.info(
            "⚠️  No GPU detected — training on CPU.\n"
            "   Estimated time per architecture: ~60–120 minutes.\n"
            "   EfficientNet-B0 and MobileNetV3-Large are selected for CPU efficiency."
        )

    # Datasets & loaders
    logger.info("Loading datasets...")
    train_ds = KneeOADataset(config["dataset"]["root"], "train", config, is_training=True)
    val_ds   = KneeOADataset(config["dataset"]["root"], "val",   config, is_training=False)

    # Log class distribution
    weights = train_ds.get_class_weights()
    logger.info("Class weights (inverse freq): %s", dict(zip(config["dataset"]["classes"], weights.tolist())))

    bs = config["training"]["batch_size"]
    nw = config["training"]["num_workers"]
    pm = config["training"].get("pin_memory", False)

    train_loader = DataLoader(train_ds, batch_size=bs, shuffle=True, num_workers=nw, pin_memory=pm)
    val_loader   = DataLoader(val_ds,   batch_size=bs, shuffle=False, num_workers=nw, pin_memory=pm)

    logger.info("Train: %d images | Val: %d images", len(train_ds), len(val_ds))

    # Architectures to train
    arch_cfgs = config["architectures"]
    if args.arch:
        arch_cfgs = [a for a in arch_cfgs if a["name"] == args.arch]
        if not arch_cfgs:
            logger.error("Architecture '%s' not found in config.", args.arch)
            sys.exit(1)

    checkpoints_dir = Path(config["output"]["checkpoints_dir"])
    results = []

    for arch_cfg in arch_cfgs:
        result = train_architecture(
            arch_cfg["name"], config, train_loader, val_loader, device, checkpoints_dir
        )
        results.append(result)

    # Summary comparison table
    logger.info("\n%s", "=" * 60)
    logger.info("ARCHITECTURE COMPARISON")
    logger.info("=" * 60)
    logger.info("%-25s | %-12s | %-10s", "Architecture", "Best Val AUC", "Best Epoch")
    logger.info("-" * 55)
    for r in results:
        logger.info("%-25s | %-12.4f | %-10d", r["arch_name"], r["best_val_auc"], r["best_epoch"])

    # Select winner
    best = max(results, key=lambda x: x["best_val_auc"])
    logger.info("\n🏆 Best architecture: %s (val_auc=%.4f)", best["arch_name"], best["best_val_auc"])

    # Copy best checkpoint to model_artifacts
    model_dir = Path(config["output"]["model_dir"])
    model_dir.mkdir(parents=True, exist_ok=True)
    dest = model_dir / "model.pth"
    shutil.copy2(best["checkpoint_path"], dest)
    logger.info("Best model weights → %s", dest)

    # Update model_config.json
    config_path = model_dir / "model_config.json"
    if config_path.exists():
        with open(config_path) as f:
            mc = json.load(f)
    else:
        mc = {}

    mc.update({
        "model_name": f"bonevision-v1.0-{best['arch_name']}",
        "architecture": best["arch_name"],
        "num_classes": len(config["dataset"]["classes"]),
        "classes": config["dataset"]["classes"],
        "confidence_threshold": config["inference"]["confidence_threshold"],
        "temperature": 1.0,  # will be updated by calibration script
        "trained": True,
        "demo_mode": False,
        "best_val_auc": round(best["best_val_auc"], 4),
        "best_epoch": best["best_epoch"],
        "dataset": "Knee Osteoarthritis Classification",
        "seed": config["seed"],
    })

    with open(config_path, "w") as f:
        json.dump(mc, f, indent=2)
    logger.info("model_config.json updated.")
    logger.info("\n✅ Training complete. Next step: run 03_evaluate.py")


if __name__ == "__main__":
    main()
