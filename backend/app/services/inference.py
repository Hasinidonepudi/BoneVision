"""
BoneVision Inference Service
Core prediction engine with demo mode and real model support.

Demo mode: returns realistic, hash-deterministic mock predictions with a
  synthetic Grad-CAM heatmap. No model weights required.

Real mode: loads trained PyTorch weights, runs forward pass, applies
  temperature-scaled softmax, applies confidence threshold for UNCERTAIN
  flagging, and generates a real Grad-CAM heatmap.
"""
import hashlib
import json
import logging
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from app.config import settings
from app.models.schemas import AnalysisResponse, ClassPrediction
from app.services.preprocessing import load_preprocessing_config, preprocess_image
from app.services.explainability import (
    GradCAM,
    generate_demo_heatmap,
    get_target_layer,
    heatmap_to_overlay,
    image_to_base64,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional torch import
# ---------------------------------------------------------------------------
try:
    import torch
    import torch.nn.functional as F
    import torchvision.models as tvm
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning(
        "PyTorch not available — BoneVision will run in demo mode only."
    )

# ---------------------------------------------------------------------------
# Demo prediction palette
# ---------------------------------------------------------------------------
_DEMO_OUTCOMES = [
    # (predicted_class, probabilities dict, status)
    ("Normal",       {"Normal": 0.88, "Osteopenia": 0.08, "Osteoporosis": 0.04}, "NORMAL"),
    ("Osteopenia",   {"Normal": 0.09, "Osteopenia": 0.83, "Osteoporosis": 0.08}, "ABNORMAL"),
    ("Osteoporosis", {"Normal": 0.05, "Osteopenia": 0.13, "Osteoporosis": 0.82}, "ABNORMAL"),
    # Uncertain outcome (confidence below threshold)
    ("Uncertain",    {"Normal": 0.37, "Osteopenia": 0.34, "Osteoporosis": 0.29}, "UNCERTAIN"),
]


def _hash_bytes(data: bytes) -> int:
    """Deterministic integer hash of image bytes — keeps demo results consistent."""
    digest = hashlib.md5(data).hexdigest()
    return int(digest, 16)


def load_model_config(config_path: Path) -> dict:
    """Load model_config.json. Falls back to safe defaults."""
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return {
        "model_name": "bonevision-demo-v1.0",
        "architecture": "efficientnet_b0",
        "num_classes": 3,
        "classes": ["Normal", "Osteopenia", "Osteoporosis"],
        "confidence_threshold": 0.60,
        "temperature": 1.0,
        "trained": False,
        "demo_mode": True,
    }


def load_metrics(metrics_path: Path) -> Optional[dict]:
    """Load evaluation metrics if they exist."""
    if metrics_path.exists():
        with open(metrics_path) as f:
            data = json.load(f)
        if data.get("status") == "demo_mode":
            return None
        return data
    return None


# ---------------------------------------------------------------------------
# Main inference class
# ---------------------------------------------------------------------------

class BoneVisionModel:
    """
    Encapsulates the full BoneVision inference pipeline.
    Supports demo mode (no weights needed) and real model mode.
    """

    def __init__(self):
        self.model = None
        self.arch_name: str = "efficientnet_b0"
        self.classes = ["Normal", "Osteopenia", "Osteoporosis"]
        self.temperature: float = 1.0
        self.demo_mode: bool = True

        # Resolve paths relative to backend/
        self.model_config = load_model_config(
            settings.abs_path(settings.MODEL_CONFIG_PATH)
        )
        self.preprocessing_config = load_preprocessing_config(
            settings.abs_path(settings.PREPROCESSING_CONFIG_PATH)
        )
        self.metrics = load_metrics(
            settings.abs_path(settings.METRICS_PATH)
        )

        # Apply config
        self.classes = self.model_config.get("classes", self.classes)
        self.arch_name = self.model_config.get("architecture", self.arch_name)
        self.temperature = float(self.model_config.get("temperature", 1.0))
        self.model_version = self.model_config.get("model_name", "bonevision-demo-v1.0")

    def load_model(self):
        """
        Attempt to load trained model weights.
        Falls back to demo mode gracefully if weights are missing or
        PyTorch is unavailable.
        """
        model_path = settings.abs_path(settings.MODEL_PATH)

        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available → demo mode activated.")
            self.demo_mode = True
            return

        if not model_path.exists():
            logger.warning(
                "Model weights not found at %s → demo mode activated. "
                "Run the ML pipeline to train and export a model.",
                model_path,
            )
            self.demo_mode = True
            return

        if self.model_config.get("demo_mode", True):
            logger.info("model_config.json indicates demo_mode=true → demo mode activated.")
            self.demo_mode = True
            return

        # --- Load real model ---
        try:
            self.model = self._build_model(self.arch_name, len(self.classes))
            state = torch.load(model_path, map_location="cpu", weights_only=True)
            self.model.load_state_dict(state)
            self.model.eval()
            self.demo_mode = False
            logger.info(
                "Loaded BoneVision model: arch=%s, classes=%s, temperature=%.3f",
                self.arch_name,
                self.classes,
                self.temperature,
            )
        except Exception as exc:
            logger.error("Failed to load model weights: %s → falling back to demo mode.", exc)
            self.model = None
            self.demo_mode = True

    def _build_model(self, arch_name: str, num_classes: int):
        """Reconstruct model architecture and replace classifier head."""
        arch = arch_name.lower()
        if "efficientnet_b0" in arch:
            model = tvm.efficientnet_b0(weights=None)
            model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, num_classes)
        elif "efficientnet_b3" in arch:
            model = tvm.efficientnet_b3(weights=None)
            model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, num_classes)
        elif "mobilenet" in arch:
            model = tvm.mobilenet_v3_large(weights=None)
            model.classifier[-1] = torch.nn.Linear(model.classifier[-1].in_features, num_classes)
        elif "densenet121" in arch:
            model = tvm.densenet121(weights=None)
            model.classifier = torch.nn.Linear(model.classifier.in_features, num_classes)
        elif "resnet50" in arch:
            model = tvm.resnet50(weights=None)
            model.fc = torch.nn.Linear(model.fc.in_features, num_classes)
        else:
            raise ValueError(f"Unknown architecture: {arch_name}")
        return model

    # -----------------------------------------------------------------------
    # Public predict interface
    # -----------------------------------------------------------------------

    def predict(self, image_bytes: bytes) -> dict:
        """
        Run inference on raw image bytes.
        Returns a dict matching the AnalysisResponse schema.
        """
        t_start = time.perf_counter()

        if self.demo_mode or self.model is None:
            result = self._demo_predict(image_bytes)
        else:
            result = self._real_predict(image_bytes)

        result["inference_time_ms"] = round((time.perf_counter() - t_start) * 1000, 1)
        return result

    # -----------------------------------------------------------------------
    # Demo prediction
    # -----------------------------------------------------------------------

    def _demo_predict(self, image_bytes: bytes) -> dict:
        """
        Return a deterministic mock prediction based on MD5 hash of the
        image bytes. The same image always returns the same demo result.
        10% probability of UNCERTAIN outcome.
        """
        seed = _hash_bytes(image_bytes)
        rng = np.random.default_rng(seed % (2**32))

        # 10% chance of uncertain
        weights = [0.30, 0.30, 0.30, 0.10]  # Normal, Osteopenia, Osteoporosis, Uncertain
        outcome_idx = rng.choice(len(_DEMO_OUTCOMES), p=weights)
        predicted_class, probs_dict, status = _DEMO_OUTCOMES[outcome_idx]

        # Add small noise so it looks realistic
        noise = rng.uniform(-0.02, 0.02, size=len(self.classes))
        raw = np.array([probs_dict.get(c, 0.0) for c in self.classes]) + noise
        raw = np.clip(raw, 0.001, 1.0)
        raw /= raw.sum()
        confidence = float(raw.max())

        if status == "UNCERTAIN":
            predicted_class = self.classes[int(raw.argmax())]

        # Generate demo heatmap
        gradcam_b64 = None
        try:
            gradcam_b64 = generate_demo_heatmap(image_bytes)
        except Exception as e:
            logger.warning("Demo heatmap generation failed: %s", e)

        requires_review = (status == "UNCERTAIN") or (confidence < settings.CONFIDENCE_THRESHOLD)

        return {
            "status": status,
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "predictions": [
                {"class": cls, "probability": round(float(p), 4)}
                for cls, p in zip(self.classes, raw.tolist())
            ],
            "gradcam_heatmap": gradcam_b64,
            "requires_review": requires_review,
            "disclaimer": settings.DISCLAIMER,
            "model_version": self.model_version,
            "inference_time_ms": 0.0,  # filled by caller
            "demo_mode": True,
            "warnings": [
                "Demo mode: predictions are illustrative only and not from a trained model."
            ],
        }

    # -----------------------------------------------------------------------
    # Real model prediction
    # -----------------------------------------------------------------------

    def _real_predict(self, image_bytes: bytes) -> dict:
        """Run inference with the loaded PyTorch model."""
        # 1. Preprocess
        input_tensor = preprocess_image(image_bytes, self.preprocessing_config)

        # 2. Forward pass (no grad for efficiency)
        with torch.no_grad():
            logits = self.model(input_tensor)  # [1, num_classes]

        # 3. Temperature scaling calibration
        calibrated_logits = logits / self.temperature
        probs = F.softmax(calibrated_logits, dim=1)[0].cpu().numpy()  # [num_classes]

        confidence = float(probs.max())
        pred_idx = int(probs.argmax())
        predicted_class = self.classes[pred_idx]

        # 4. Confidence threshold → UNCERTAIN if too low
        if confidence < settings.CONFIDENCE_THRESHOLD:
            status = "UNCERTAIN"
        elif predicted_class == "Normal":
            status = "NORMAL"
        else:
            status = "ABNORMAL"

        requires_review = status == "UNCERTAIN"

        # 5. Grad-CAM
        gradcam_b64 = None
        try:
            target_layer = get_target_layer(self.model, self.arch_name)
            cam = GradCAM(self.model, target_layer)
            heatmap = cam.generate(input_tensor, class_idx=pred_idx)
            cam.remove_hooks()

            original_pil = Image.open(BytesIO(image_bytes)).convert("RGB")
            overlay = heatmap_to_overlay(heatmap, original_pil)
            gradcam_b64 = image_to_base64(overlay)
        except Exception as e:
            logger.warning("Grad-CAM generation failed: %s", e)

        return {
            "status": status,
            "predicted_class": predicted_class,
            "confidence": round(confidence, 4),
            "predictions": [
                {"class": cls, "probability": round(float(p), 4)}
                for cls, p in zip(self.classes, probs.tolist())
            ],
            "gradcam_heatmap": gradcam_b64,
            "requires_review": requires_review,
            "disclaimer": settings.DISCLAIMER,
            "model_version": self.model_version,
            "inference_time_ms": 0.0,
            "demo_mode": False,
            "warnings": [],
        }


# ---------------------------------------------------------------------------
# Global singleton — loaded at startup
# ---------------------------------------------------------------------------
model_instance = BoneVisionModel()
