"""
BoneVision Dataset Preprocessor
================================
Applies CLAHE contrast enhancement to ALL images in the dataset and saves them
to a new preprocessed directory. This makes training faster (no CLAHE at every epoch)
and ensures 100% consistent preprocessing between training and inference.

Output structure mirrors input:
  C:/Users/heman/Downloads/archive_preprocessed/Knee Osteoarthritis Classification/
    train/Normal/, train/Osteopenia/, train/Osteoporosis/
    val/Normal/,   val/Osteopenia/,   val/Osteoporosis/
    test/Normal/,  test/Osteopenia/,  test/Osteoporosis/

After running this, update training_config.yaml:
  dataset.root: "C:/Users/heman/Downloads/archive_preprocessed/Knee Osteoarthritis Classification"
"""
import sys
import logging
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import cv2
import numpy as np
from PIL import Image
from tqdm import tqdm

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
SRC_ROOT = Path("C:/Users/heman/Downloads/archive_extracted/Knee Osteoarthritis Classification")
DST_ROOT = Path("C:/Users/heman/Downloads/archive_preprocessed/Knee Osteoarthritis Classification")

CLASSES = ["Normal", "Osteopenia", "Osteoporosis"]
SPLITS  = ["train", "val", "test"]

CLAHE_CLIP_LIMIT    = 2.0
CLAHE_TILE_GRID     = (8, 8)
INPUT_SIZE          = 224          # resize to 224×224 during preprocessing
VALID_EXTS          = {".jpg", ".jpeg", ".png", ".bmp"}
SAVE_QUALITY        = 95           # JPEG quality (1-95)

# ── CLAHE helper ─────────────────────────────────────────────────────────────

def apply_clahe(pil_img: Image.Image) -> Image.Image:
    """Apply CLAHE on the L channel of LAB colour space."""
    cv_img = cv2.cvtColor(np.array(pil_img.convert("RGB")), cv2.COLOR_RGB2BGR)
    lab    = cv2.cvtColor(cv_img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe  = cv2.createCLAHE(clipLimit=CLAHE_CLIP_LIMIT, tileGridSize=CLAHE_TILE_GRID)
    lab_enhanced = cv2.merge([clahe.apply(l), a, b])
    result_rgb = cv2.cvtColor(
        cv2.cvtColor(lab_enhanced, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2RGB
    )
    return Image.fromarray(result_rgb)


def process_one(src_path: Path, dst_path: Path) -> bool:
    """Load → CLAHE → Resize → Save one image. Returns True on success."""
    try:
        img = Image.open(src_path).convert("RGB")
        img = apply_clahe(img)
        img = img.resize((INPUT_SIZE, INPUT_SIZE), Image.LANCZOS)
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        # Save as JPEG regardless of original extension for consistency
        img.save(dst_path.with_suffix(".jpeg"), format="JPEG", quality=SAVE_QUALITY)
        return True
    except Exception as e:
        logger.error("Failed %s: %s", src_path.name, e)
        return False


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    logger.info("Source  : %s", SRC_ROOT)
    logger.info("Dest    : %s", DST_ROOT)
    logger.info("CLAHE   : clip_limit=%.1f  tile_grid=%s", CLAHE_CLIP_LIMIT, CLAHE_TILE_GRID)
    logger.info("Resize  : %dx%d", INPUT_SIZE, INPUT_SIZE)
    logger.info("")

    # Collect all (src, dst) pairs
    pairs = []
    for split in SPLITS:
        for cls in CLASSES:
            src_dir = SRC_ROOT / split / cls
            dst_dir = DST_ROOT / split / cls
            if not src_dir.exists():
                logger.warning("Missing: %s — skipped.", src_dir)
                continue
            for f in src_dir.iterdir():
                if f.suffix.lower() in VALID_EXTS:
                    dst_file = dst_dir / f.name
                    pairs.append((f, dst_file))

    total = len(pairs)
    logger.info("Total images to process: %d", total)

    ok = 0
    fail = 0

    # Parallel processing with 4 workers for speed
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(process_one, src, dst): (src, dst) for src, dst in pairs}
        with tqdm(total=total, desc="Preprocessing", unit="img") as pbar:
            for fut in as_completed(futures):
                if fut.result():
                    ok += 1
                else:
                    fail += 1
                pbar.update(1)
                pbar.set_postfix(ok=ok, fail=fail)

    logger.info("")
    logger.info("=" * 60)
    logger.info("DONE — %d/%d images preprocessed successfully.", ok, total)
    if fail:
        logger.warning("FAILED: %d images (check errors above).", fail)
    logger.info("=" * 60)
    logger.info("")
    logger.info("Next step: Update training_config.yaml dataset.root to:")
    logger.info("  %s", DST_ROOT)
    logger.info("Then retrain: py 02_train.py")


if __name__ == "__main__":
    main()
