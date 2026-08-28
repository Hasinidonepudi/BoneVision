"""
BoneVision — Step 1: Data Validation
=====================================
Run this FIRST before any training.

What it does:
  - Counts images per class per split
  - Detects corrupt / unreadable image files
  - Flags images below minimum dimension threshold
  - Identifies pre-augmented images (_aug_ in filename)
  - Prints a full class-balance report
  - Saves a text report to outputs/data_validation_report.txt

Usage:
    python 01_data_validation.py
    python 01_data_validation.py --config configs/training_config.yaml
"""
import argparse
import logging
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import yaml
from PIL import Image, UnidentifiedImageError

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger("data_validation")

MIN_DIM = 64  # Reject images smaller than this in any dimension


def validate_dataset(config: dict) -> dict:
    root = Path(config["dataset"]["root"])
    classes = config["dataset"]["classes"]
    splits = config["dataset"]["splits"]
    reports_dir = Path(config["output"]["reports_dir"])
    reports_dir.mkdir(parents=True, exist_ok=True)

    lines = ["=" * 60, "BoneVision Data Validation Report", "=" * 60, ""]
    total_corrupt = 0
    total_small = 0
    total_aug = 0
    summary = {}

    for split in splits:
        lines.append(f"\n--- Split: {split.upper()} ---")
        split_total = 0
        split_corrupt = 0
        split_small = 0
        split_aug = 0

        for cls in classes:
            cls_dir = root / split / cls
            if not cls_dir.exists():
                logger.warning("Missing directory: %s", cls_dir)
                lines.append(f"  {cls}: MISSING DIRECTORY")
                continue

            img_files = [
                p for p in sorted(cls_dir.iterdir())
                if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".bmp"}
            ]

            corrupt = []
            small = []
            aug_count = 0

            for img_path in img_files:
                # Check for pre-augmented
                if "_aug" in img_path.stem.lower():
                    aug_count += 1

                # Check for zero-byte
                if img_path.stat().st_size == 0:
                    corrupt.append(img_path.name)
                    continue

                # Try to open
                try:
                    with Image.open(img_path) as img:
                        img.verify()
                    with Image.open(img_path) as img:
                        w, h = img.size
                    if w < MIN_DIM or h < MIN_DIM:
                        small.append((img_path.name, w, h))
                except (UnidentifiedImageError, Exception) as e:
                    corrupt.append(img_path.name)

            count = len(img_files)
            split_total += count
            split_corrupt += len(corrupt)
            split_small += len(small)
            split_aug += aug_count

            line = (
                f"  {cls:<15} {count:>5} images"
                f"  | pre-aug: {aug_count}"
                f"  | corrupt: {len(corrupt)}"
                f"  | too-small: {len(small)}"
            )
            lines.append(line)
            logger.info(line.strip())

            if corrupt:
                lines.append(f"    ⚠️  Corrupt files: {corrupt[:5]}{'...' if len(corrupt)>5 else ''}")
            if small:
                lines.append(f"    ⚠️  Too-small files: {[f'{n} ({w}x{h})' for n,w,h in small[:3]]}")

        lines.append(
            f"  SPLIT TOTAL: {split_total} images | "
            f"corrupt: {split_corrupt} | small: {split_small} | pre-aug: {split_aug}"
        )
        summary[split] = {
            "total": split_total,
            "corrupt": split_corrupt,
            "small": split_small,
            "pre_augmented": split_aug,
        }
        total_corrupt += split_corrupt
        total_small += split_small
        total_aug += split_aug

    lines += [
        "",
        "=" * 60,
        "OVERALL SUMMARY",
        "=" * 60,
        f"  Total corrupt images : {total_corrupt}",
        f"  Total too-small images: {total_small}",
        f"  Total pre-aug images  : {total_aug}",
    ]

    if total_corrupt == 0 and total_small == 0:
        lines.append("  ✅ Dataset looks clean — ready for training.")
    else:
        lines.append("  ⚠️  Please remove or fix flagged files before training.")

    report_text = "\n".join(lines)
    print(report_text)

    report_path = reports_dir / "data_validation_report.txt"
    report_path.write_text(report_text, encoding="utf-8")
    logger.info("Report saved to: %s", report_path)
    return summary


def main():
    parser = argparse.ArgumentParser(description="BoneVision data validation")
    parser.add_argument(
        "--config",
        default=str(Path(__file__).parent / "configs" / "training_config.yaml"),
        help="Path to training_config.yaml",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error("Config file not found: %s", config_path)
        sys.exit(1)

    with open(config_path) as f:
        config = yaml.safe_load(f)

    validate_dataset(config)


if __name__ == "__main__":
    main()
