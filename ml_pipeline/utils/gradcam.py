"""
BoneVision Grad-CAM Utility (ML Pipeline version)
Used during training pipeline for generating sample visualisations.
"""
import logging
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class GradCAM:
    """Gradient-weighted Class Activation Mapping for PyTorch models."""

    def __init__(self, model, target_layer):
        self.model = model
        self.activations: Optional["torch.Tensor"] = None
        self.gradients: Optional["torch.Tensor"] = None
        self._fwd = target_layer.register_forward_hook(self._save_act)
        self._bwd = target_layer.register_full_backward_hook(self._save_grad)

    def _save_act(self, module, inp, out):
        self.activations = out.detach()

    def _save_grad(self, module, grad_inp, grad_out):
        self.gradients = grad_out[0].detach()

    def generate_heatmap(self, input_tensor, class_idx: Optional[int] = None) -> np.ndarray:
        """
        Generate Grad-CAM heatmap for the given input tensor.

        Args:
            input_tensor: [1, C, H, W] tensor.
            class_idx: Target class. None → use argmax.

        Returns:
            Float32 numpy array [H, W] in [0, 1].
        """
        self.model.eval()
        input_tensor = input_tensor.clone().requires_grad_(True)
        output = self.model(input_tensor)

        if class_idx is None:
            class_idx = int(output.argmax(dim=1).item())

        self.model.zero_grad()
        output[0, class_idx].backward()

        weights = self.gradients.mean(dim=[2, 3])[0]
        activations = self.activations[0]
        cam = torch.einsum("c,chw->hw", weights, activations)
        cam = F.relu(cam).cpu().numpy()

        cam -= cam.min()
        if cam.max() > 1e-8:
            cam /= cam.max()
        return cam.astype(np.float32)

    def overlay_heatmap(
        self, heatmap: np.ndarray, original_bgr: np.ndarray, alpha: float = 0.5
    ) -> np.ndarray:
        """
        Blend Grad-CAM heatmap over original BGR image.

        Args:
            heatmap: [H, W] float in [0,1].
            original_bgr: Original image in BGR (OpenCV format).
            alpha: Heatmap blend weight.

        Returns:
            BGR numpy array of the overlay.
        """
        h, w = original_bgr.shape[:2]
        hm_resized = cv2.resize(heatmap, (w, h))
        hm_uint8 = (hm_resized * 255).astype(np.uint8)
        colored = cv2.applyColorMap(hm_uint8, cv2.COLORMAP_JET)
        gray = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2GRAY)
        gray_bgr = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        blended = (alpha * colored + (1 - alpha) * gray_bgr).astype(np.uint8)
        return blended

    def remove_hooks(self):
        self._fwd.remove()
        self._bwd.remove()


def get_target_layer(model, arch_name: str):
    """Return the last convolutional layer for Grad-CAM by architecture."""
    arch = arch_name.lower()
    if "efficientnet" in arch:
        return model.features[-1]
    elif "mobilenet" in arch:
        return model.features[-1]
    elif "densenet" in arch:
        return model.features.denseblock4
    elif "resnet" in arch:
        return model.layer4[-1]
    else:
        # Generic: find the last Conv2d layer
        last_conv = None
        for m in model.modules():
            if isinstance(m, torch.nn.Conv2d):
                last_conv = m
        if last_conv is None:
            raise ValueError(f"Cannot find conv layer for arch: {arch_name}")
        return last_conv
