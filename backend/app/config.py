"""
BoneVision Backend Configuration
Centralises all settings, paths, and thresholds.
"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


# Absolute path to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # App metadata
    APP_NAME: str = "BoneVision API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Demo mode: True until real trained model weights are present
    DEMO_MODE: bool = True

    # Model artifact paths (relative to backend/)
    MODEL_PATH: str = "model_artifacts/model.pth"
    MODEL_CONFIG_PATH: str = "model_artifacts/model_config.json"
    PREPROCESSING_CONFIG_PATH: str = "model_artifacts/preprocessing_config.json"
    METRICS_PATH: str = "model_artifacts/metrics.json"

    # Inference thresholds
    # max(softmax) below this value → return UNCERTAIN status
    CONFIDENCE_THRESHOLD: float = 0.45
    INPUT_SIZE: int = 224

    # Device: auto-detect (cuda → mps → cpu)
    DEVICE: str = "auto"

    # Upload limits
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png"]
    MIN_IMAGE_DIM: int = 64  # pixels, reject images smaller than this

    # CORS — allow the Vite dev server and any production origin
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

    # Medical disclaimer appended to every response
    DISCLAIMER: str = (
        "This is an AI-assisted screening tool and NOT a substitute for "
        "professional medical diagnosis. All results must be reviewed and "
        "confirmed by a qualified radiologist or healthcare professional."
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    def abs_path(self, relative: str) -> Path:
        """Resolve a path relative to the backend directory."""
        return BACKEND_DIR / relative

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
