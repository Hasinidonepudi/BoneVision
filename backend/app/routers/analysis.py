"""
BoneVision API Router — Analysis Endpoints
POST /api/v1/analyze  — Upload X-ray and receive screening result
GET  /api/v1/health   — Liveness / readiness check
GET  /api/v1/model-info — Class labels, metrics, version info
"""
import json
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.config import settings
from app.models.schemas import AnalysisResponse, ClassPrediction, HealthResponse, ModelInfoResponse
from app.services.inference import model_instance
from app.services.validation import validate_upload

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["analysis"])


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    summary="Analyze a knee X-ray image",
    description=(
        "Upload a JPEG/PNG knee X-ray. Returns predicted screening status "
        "(Normal / Abnormal / Uncertain), per-class probabilities, confidence score, "
        "and a Grad-CAM heatmap overlay. "
        "⚠️ This is an AI screening tool — results require clinical confirmation."
    ),
)
async def analyze_image(file: UploadFile = File(...)):
    """Main endpoint: validate → preprocess → infer → return structured result."""

    # --- Read file bytes ---
    try:
        file_bytes = await file.read()
    except Exception as exc:
        logger.error("Failed to read uploaded file: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not read the uploaded file.",
        )

    # --- Validate ---
    is_valid, error_msg = validate_upload(file, file_bytes)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=error_msg,
        )

    # --- Run inference ---
    try:
        raw_result = model_instance.predict(file_bytes)
    except Exception as exc:
        logger.exception("Inference failed for file '%s': %s", file.filename, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Inference failed. Please try again or contact support.",
        )

    # --- Build typed response ---
    predictions = [
        ClassPrediction(**{"class": p["class"], "probability": p["probability"]})
        for p in raw_result["predictions"]
    ]

    response = AnalysisResponse(
        status=raw_result["status"],
        predicted_class=raw_result["predicted_class"],
        confidence=raw_result["confidence"],
        predictions=predictions,
        gradcam_heatmap=raw_result.get("gradcam_heatmap"),
        requires_review=raw_result["requires_review"],
        disclaimer=raw_result["disclaimer"],
        model_version=raw_result["model_version"],
        inference_time_ms=raw_result["inference_time_ms"],
        demo_mode=raw_result.get("demo_mode", False),
        warnings=raw_result.get("warnings", []),
    )

    logger.info(
        "Analysis complete: file='%s', status=%s, class='%s', confidence=%.3f, demo=%s",
        file.filename,
        response.status,
        response.predicted_class,
        response.confidence,
        response.demo_mode,
    )
    return response


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
)
async def health_check():
    """Returns API liveness status and model load state."""
    return HealthResponse(
        status="ok",
        model_loaded=(model_instance.model is not None),
        demo_mode=model_instance.demo_mode,
        version=settings.APP_VERSION,
    )


@router.get(
    "/model-info",
    response_model=ModelInfoResponse,
    summary="Model metadata and evaluation metrics",
)
async def model_info():
    """Returns class labels, model version, confidence threshold, and test-set metrics."""
    metrics = None
    metrics_path = settings.abs_path(settings.METRICS_PATH)
    if metrics_path.exists():
        with open(metrics_path) as f:
            data = json.load(f)
        if data.get("status") != "demo_mode":
            metrics = data

    return ModelInfoResponse(
        classes=model_instance.classes,
        model_version=model_instance.model_version,
        confidence_threshold=settings.CONFIDENCE_THRESHOLD,
        metrics=metrics,
        demo_mode=model_instance.demo_mode,
        architecture=model_instance.arch_name,
    )
