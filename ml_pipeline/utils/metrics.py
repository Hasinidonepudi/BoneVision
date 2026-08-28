"""
BoneVision Metrics Utility
Computes and visualises all evaluation metrics for the trained model.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional

import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server use
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    average_precision_score,
    roc_curve,
    precision_recall_curve,
)

logger = logging.getLogger(__name__)


def compute_specificity(y_true: np.ndarray, y_pred: np.ndarray, class_idx: int) -> float:
    """
    Compute specificity (True Negative Rate) for one class in a multi-class setting.
    Specificity = TN / (TN + FP)

    Args:
        y_true: 1-D array of true class indices.
        y_pred: 1-D array of predicted class indices.
        class_idx: Class to compute specificity for.
    """
    binary_true = (y_true == class_idx).astype(int)
    binary_pred = (y_pred == class_idx).astype(int)
    tn = int(((binary_true == 0) & (binary_pred == 0)).sum())
    fp = int(((binary_true == 0) & (binary_pred == 1)).sum())
    return tn / (tn + fp) if (tn + fp) > 0 else 0.0


def compute_all_metrics(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    class_names: List[str],
) -> dict:
    """
    Compute the full set of evaluation metrics.

    Args:
        y_true: 1-D int array of true class indices, shape [N].
        y_pred_proba: Float array of predicted probabilities, shape [N, C].
        class_names: List of class label strings.

    Returns:
        Dict with all metrics suitable for JSON serialisation.
    """
    y_pred = y_pred_proba.argmax(axis=1)
    n_classes = len(class_names)

    # Overall accuracy
    accuracy = float(accuracy_score(y_true, y_pred))

    # Macro-averaged metrics
    macro_precision = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    macro_recall    = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    macro_f1        = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    # ROC-AUC (macro OvR)
    try:
        roc_auc = float(roc_auc_score(y_true, y_pred_proba, multi_class="ovr", average="macro"))
    except Exception:
        roc_auc = None

    # PR-AUC (macro average precision)
    from sklearn.preprocessing import label_binarize
    y_bin = label_binarize(y_true, classes=list(range(n_classes)))
    pr_auc_scores = []
    for i in range(n_classes):
        try:
            pr_auc_scores.append(float(average_precision_score(y_bin[:, i], y_pred_proba[:, i])))
        except Exception:
            pr_auc_scores.append(None)
    pr_auc = float(np.mean([s for s in pr_auc_scores if s is not None])) if pr_auc_scores else None

    # Per-class metrics
    per_class = {}
    for i, cls in enumerate(class_names):
        binary_true = (y_true == i).astype(int)
        binary_pred = (y_pred == i).astype(int)
        tp = int(((binary_true == 1) & (binary_pred == 1)).sum())
        tn = int(((binary_true == 0) & (binary_pred == 0)).sum())
        fp = int(((binary_true == 0) & (binary_pred == 1)).sum())
        fn = int(((binary_true == 1) & (binary_pred == 0)).sum())

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec  = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0

        per_class[cls] = {
            "precision": round(prec, 4),
            "recall_sensitivity": round(rec, 4),
            "specificity": round(spec, 4),
            "f1_score": round(f1, 4),
            "support": int((y_true == i).sum()),
        }

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred).tolist()

    # Text classification report
    report = classification_report(y_true, y_pred, target_names=class_names, zero_division=0)

    return {
        "accuracy": round(accuracy, 4),
        "macro_precision": round(macro_precision, 4),
        "macro_recall": round(macro_recall, 4),
        "macro_f1": round(macro_f1, 4),
        "roc_auc_macro": round(roc_auc, 4) if roc_auc is not None else None,
        "pr_auc_macro": round(pr_auc, 4) if pr_auc is not None else None,
        "per_class": per_class,
        "confusion_matrix": cm,
        "classification_report": report,
        "n_samples": int(len(y_true)),
    }


def plot_confusion_matrix(
    cm: List[List[int]],
    class_names: List[str],
    save_path: Path,
    title: str = "Confusion Matrix",
):
    """Save a colour-coded confusion matrix heatmap."""
    cm_arr = np.array(cm)
    fig, ax = plt.subplots(figsize=(7, 6))
    im = ax.imshow(cm_arr, interpolation="nearest", cmap="Blues")
    plt.colorbar(im, ax=ax)
    ax.set(
        xticks=np.arange(len(class_names)),
        yticks=np.arange(len(class_names)),
        xticklabels=class_names,
        yticklabels=class_names,
        title=title,
        ylabel="True Label",
        xlabel="Predicted Label",
    )
    plt.setp(ax.get_xticklabels(), rotation=30, ha="right")
    thresh = cm_arr.max() / 2.0
    for i in range(cm_arr.shape[0]):
        for j in range(cm_arr.shape[1]):
            ax.text(j, i, format(cm_arr[i, j], "d"),
                    ha="center", va="center",
                    color="white" if cm_arr[i, j] > thresh else "black")
    fig.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    logger.info("Confusion matrix saved: %s", save_path)


def plot_roc_curves(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    class_names: List[str],
    save_path: Path,
):
    """Save multi-class ROC curves (one-vs-rest)."""
    from sklearn.preprocessing import label_binarize
    y_bin = label_binarize(y_true, classes=list(range(len(class_names))))

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#3b82f6", "#f59e0b", "#ef4444"]
    for i, (cls, color) in enumerate(zip(class_names, colors)):
        fpr, tpr, _ = roc_curve(y_bin[:, i], y_pred_proba[:, i])
        auc = roc_auc_score(y_bin[:, i], y_pred_proba[:, i])
        ax.plot(fpr, tpr, color=color, lw=2, label=f"{cls} (AUC={auc:.3f})")
    ax.plot([0, 1], [0, 1], "k--", lw=1, label="Random")
    ax.set(xlabel="False Positive Rate", ylabel="True Positive Rate",
           title="ROC Curves (One-vs-Rest)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    logger.info("ROC curves saved: %s", save_path)


def plot_pr_curves(
    y_true: np.ndarray,
    y_pred_proba: np.ndarray,
    class_names: List[str],
    save_path: Path,
):
    """Save multi-class Precision-Recall curves."""
    from sklearn.preprocessing import label_binarize
    y_bin = label_binarize(y_true, classes=list(range(len(class_names))))

    fig, ax = plt.subplots(figsize=(8, 6))
    colors = ["#3b82f6", "#f59e0b", "#ef4444"]
    for i, (cls, color) in enumerate(zip(class_names, colors)):
        prec, rec, _ = precision_recall_curve(y_bin[:, i], y_pred_proba[:, i])
        ap = average_precision_score(y_bin[:, i], y_pred_proba[:, i])
        ax.plot(rec, prec, color=color, lw=2, label=f"{cls} (AP={ap:.3f})")
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision-Recall Curves")
    ax.legend(loc="upper right")
    fig.tight_layout()
    save_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(save_path, dpi=150)
    plt.close(fig)
    logger.info("PR curves saved: %s", save_path)
