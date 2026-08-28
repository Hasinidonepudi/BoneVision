"""
BoneVision Image Validation Service
Validates uploaded files before processing.
Checks: extension, MIME type (via PIL), file size, image dimensions.
"""
import logging
from pathlib import Path
from io import BytesIO

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from app.config import settings

logger = logging.getLogger(__name__)


def validate_upload(file: UploadFile, file_bytes: bytes) -> tuple[bool, str]:
    """
    Validate an uploaded image file.

    Args:
        file: The FastAPI UploadFile object (for metadata).
        file_bytes: Raw file content already read into memory.

    Returns:
        (is_valid, error_message) — error_message is empty string when valid.
    """
    # --- 1. Check file extension ---
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in settings.ALLOWED_EXTENSIONS:
        msg = (
            f"Unsupported file type '{suffix}'. "
            f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
        logger.warning("Validation failed (extension): %s", msg)
        return False, msg

    # --- 2. Check file size ---
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(file_bytes) == 0:
        return False, "Uploaded file is empty."
    if len(file_bytes) > max_bytes:
        msg = (
            f"File size {len(file_bytes) / (1024*1024):.1f} MB exceeds "
            f"the {settings.MAX_FILE_SIZE_MB} MB limit."
        )
        logger.warning("Validation failed (size): %s", msg)
        return False, msg

    # --- 3. Verify it is a real image (MIME-level check via PIL) ---
    try:
        img = Image.open(BytesIO(file_bytes))
        img.verify()  # Detects truncated / corrupt files
    except UnidentifiedImageError:
        msg = "File could not be identified as a valid image."
        logger.warning("Validation failed (PIL identify): %s", msg)
        return False, msg
    except Exception as exc:
        msg = f"Image appears to be corrupt or unreadable: {exc}"
        logger.warning("Validation failed (PIL verify): %s", msg)
        return False, msg

    # Re-open after verify (verify() closes the file handle)
    try:
        img = Image.open(BytesIO(file_bytes))
        width, height = img.size
    except Exception as exc:
        return False, f"Could not read image dimensions: {exc}"

    # --- 4. Check minimum dimensions ---
    min_dim = settings.MIN_IMAGE_DIM
    if width < min_dim or height < min_dim:
        msg = (
            f"Image dimensions {width}×{height} px are too small. "
            f"Minimum required: {min_dim}×{min_dim} px."
        )
        logger.warning("Validation failed (dimensions): %s", msg)
        return False, msg

    logger.info(
        "Validation passed: '%s' (%d bytes, %dx%d px)",
        file.filename,
        len(file_bytes),
        width,
        height,
    )
    return True, ""
