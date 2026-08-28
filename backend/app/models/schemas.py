"""
BoneVision Pydantic Schemas
Defines all request/response models for safe, typed API communication.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Literal


class ClassPrediction(BaseModel):
    """Probability for a single class."""
    class_name: str = Field(..., alias="class", description="Class label")
    probability: float = Field(..., ge=0.0, le=1.0, description="Softmax probability")

    model_config = {"populate_by_name": True}


class AnalysisResponse(BaseModel):
    """
    Full response returned by POST /api/v1/analyze.
    Designed to be safe: never forces a diagnosis, always includes disclaimer.
    """
    status: Literal["NORMAL", "ABNORMAL", "UNCERTAIN"] = Field(
        ..., description="High-level screening status"
    )
    predicted_class: str = Field(..., description="Top predicted class label")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Max softmax probability")
    predictions: List[ClassPrediction] = Field(
        ..., description="Per-class probability breakdown"
    )
    gradcam_heatmap: Optional[str] = Field(
        None, description="Base64-encoded PNG heatmap overlay (null in demo mode)"
    )
    requires_review: bool = Field(
        ..., description="True when confidence is below threshold or status is UNCERTAIN"
    )
    disclaimer: str = Field(..., description="Mandatory medical disclaimer")
    model_version: str = Field(..., description="Model identifier string")
    inference_time_ms: float = Field(..., description="Server-side inference time in ms")
    demo_mode: bool = Field(False, description="True when using mock predictions")
    warnings: List[str] = Field(default_factory=list, description="Non-fatal warnings")


class HealthResponse(BaseModel):
    """Response for GET /api/v1/health."""
    status: str
    model_loaded: bool
    demo_mode: bool
    version: str


class ModelInfoResponse(BaseModel):
    """Response for GET /api/v1/model-info."""
    classes: List[str]
    model_version: str
    confidence_threshold: float
    metrics: Optional[dict] = None
    demo_mode: bool
    architecture: Optional[str] = None
