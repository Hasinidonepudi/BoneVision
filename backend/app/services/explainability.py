"""
BoneVision Explainability Service — Grad-CAM
Generates class activation heatmaps to highlight which regions of
the X-ray influenced the model's prediction.

In demo mode, returns a synthetic radial Gaussian heatmap that visually
approximates where a real Grad-CAM would activate on a knee X-ray.
"""
import base64
import logging
from io import BytesIO
from typing import Optional

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


# ---------------------------------------------------------------------------
# Real Grad-CAM (used when model is loaded)
# ---------------------------------------------------------------------------

class GradCAM:
    """
    Gradient-weighted Class Activation Mapping.
    Hooks into the target convolutional layer to compute gradients and
    activations, then combines them into a spatial importance heatmap.
    """

    def __init__(self, model, target_layer):
        """
        Args:
            model: PyTorch model in eval() mode.
            target_layer: The nn.Module layer to hook (last conv layer).
        """
        self.model = model
        self.activations: Optional[torch.Tensor] = None
        self.gradients: Optional[torch.Tensor] = None

        # Register forward hook to capture activations
        self._fwd_handle = target_layer.register_forward_hook(self._save_activation)
        # Register backward hook to capture gradients
        self._bwd_handle = target_layer.register_full_backward_hook(self._save_gradient)

    def _save_activation(self, module, input, output):
        self.activations = output.detach()

    def _save_gradient(self, module, grad_input, grad_output):
        self.gradients = grad_output[0].detach()

    def generate(self, input_tensor, class_idx: Optional[int] = None) -> np.ndarray:
        """
        Compute the Grad-CAM heatmap for a given input.

        Args:
            input_tensor: Preprocessed tensor of shape [1, 3, H, W].
            class_idx: Class to explain. If None, uses argmax (predicted class).

        Returns:
            Heatmap as numpy float32 array, values in [0, 1], shape [H, W].
        """
        self.model.eval()
        input_tensor = input_tensor.requires_grad_(True)

        # Forward pass
        output = self.model(input_tensor)  # [1, num_classes]

        if class_idx is None:
            class_idx = output.argmax(dim=1).item()

        # Zero gradients, backward on selected class score
        self.model.zero_grad()
        score = output[0, class_idx]
        score.backward()

        # Global average pool the gradients over spatial dims
        # gradients: [1, C, H, W] → weights: [C]
        weights = self.gradients.mean(dim=[2, 3])[0]  # [C]

        # Weighted sum of activation maps
        activations = self.activations[0]  # [C, h, w]
        cam = torch.einsum("c,chw->hw", weights, activations)

        # Apply ReLU (keep only positive influence)
        cam = F.relu(cam)

        # Normalise to [0, 1]
        cam = cam.cpu().numpy()
        cam -= cam.min()
        if cam.max() > 0:
            cam /= cam.max()

        return cam  # [h, w], float32

    def remove_hooks(self):
        """Call after inference to avoid memory leaks."""
        self._fwd_handle.remove()
        self._bwd_handle.remove()


def get_target_layer(model, arch_name: str):
    """
    Return the last convolutional layer for Grad-CAM, per architecture.
    """
    arch = arch_name.lower()
    if "efficientnet" in arch:
        return model.features[-1]
    elif "densenet" in arch:
        return model.features.denseblock4
    elif "resnet" in arch or "mobilenet" in arch:
        return model.layer4[-1] if hasattr(model, "layer4") else model.features[-1]
    else:
        # Generic fallback: last module that has parameters
        last_conv = None
        for module in model.modules():
            if isinstance(module, torch.nn.Conv2d):
                last_conv = module
        if last_conv is None:
            raise ValueError(f"Cannot find a target conv layer for arch: {arch_name}")
        return last_conv


# ---------------------------------------------------------------------------
# Heatmap → image overlay helpers
# ---------------------------------------------------------------------------

def heatmap_to_overlay(
    heatmap: np.ndarray,
    original_pil: Image.Image,
    alpha: float = 0.5,
) -> Image.Image:
    """
    Blend a float heatmap [0,1] over the original grayscale X-ray.

    Args:
        heatmap: float32 numpy array in [0, 1], any spatial size.
        original_pil: Original PIL image (RGB or L).
        alpha: Weight of the heatmap overlay (0=original only, 1=heatmap only).

    Returns:
        PIL RGB image with coloured heatmap blended over the X-ray.
    """
    # Resize heatmap to match original image
    w, h = original_pil.size
    heatmap_resized = cv2.resize(heatmap, (w, h))

    # Apply jet colormap (0→blue cool, 1→red hot)
    heatmap_uint8 = (heatmap_resized * 255).astype(np.uint8)
    colored = cv2.applyColorMap(heatmap_uint8, cv2.COLORMAP_JET)  # BGR
    colored_rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)

    # Convert original to grayscale then back to RGB for blending
    gray = np.array(original_pil.convert("L"))
    gray_rgb = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

    # Blend
    blended = (alpha * colored_rgb + (1 - alpha) * gray_rgb).astype(np.uint8)
    return Image.fromarray(blended)


def image_to_base64(pil_image: Image.Image) -> str:
    """Encode a PIL image to a base64 PNG string (for JSON transport)."""
    buf = BytesIO()
    pil_image.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


# ---------------------------------------------------------------------------
# Demo Grad-CAM — synthetic radial Gaussian heatmap
# ---------------------------------------------------------------------------

def generate_demo_heatmap(image_bytes: bytes, image_size: int = 224) -> str:
    """
    Generate a synthetic Grad-CAM-like heatmap for demo mode.
    Creates a Gaussian blob centred around the knee joint area
    (approximately 45% from top, 50% from left) to mimic where a real
    model would activate on a knee X-ray.

    Args:
        image_bytes: Raw bytes of the uploaded image.
        image_size: Target size for display.

    Returns:
        Base64-encoded PNG overlay string.
    """
    # Open original for blending
    pil_img = Image.open(BytesIO(image_bytes)).convert("RGB").resize(
        (image_size, image_size), Image.LANCZOS
    )

    # Build synthetic heatmap: sum of two Gaussian blobs
    H, W = image_size, image_size
    y_c, x_c = int(H * 0.45), int(W * 0.50)   # primary blob (knee joint)
    y_c2, x_c2 = int(H * 0.35), int(W * 0.52)  # secondary blob (upper joint)

    yy, xx = np.mgrid[0:H, 0:W]

    sigma1 = image_size * 0.18
    sigma2 = image_size * 0.10

    blob1 = np.exp(-((xx - x_c) ** 2 + (yy - y_c) ** 2) / (2 * sigma1 ** 2))
    blob2 = np.exp(-((xx - x_c2) ** 2 + (yy - y_c2) ** 2) / (2 * sigma2 ** 2))

    heatmap = (0.7 * blob1 + 0.3 * blob2).astype(np.float32)
    heatmap /= heatmap.max()

    overlay = heatmap_to_overlay(heatmap, pil_img, alpha=0.45)
    return image_to_base64(overlay)
