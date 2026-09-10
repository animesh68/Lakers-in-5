"""
Evaluation and Calibration Metrics Module for Lakers in 5.
Computes Log Loss, Brier Score, ROC-AUC, Accuracy, ECE, MAE, RMSE, and calibration curves.
"""

from typing import Dict, Any, Tuple, Optional, List
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    log_loss,
    brier_score_loss,
    mean_absolute_error,
    mean_squared_error,
)
from sklearn.calibration import calibration_curve

def compute_expected_calibration_error(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> float:
    """
    Computes Expected Calibration Error (ECE) across n_bins probability buckets.
    ECE = sum_{b=1}^B ( |B_b| / N ) * | acc(B_b) - conf(B_b) |
    """
    y_true = np.asarray(y_true).astype(int)
    y_prob = np.clip(np.asarray(y_prob).astype(float), 0.0, 1.0)
    
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n_samples = len(y_true)
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        if i == n_bins - 1:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
            
        bin_size = np.sum(in_bin)
        if bin_size > 0:
            bin_acc = np.mean(y_true[in_bin])
            bin_conf = np.mean(y_prob[in_bin])
            ece += (bin_size / n_samples) * np.abs(bin_acc - bin_conf)
            
    return float(ece)


def compute_calibration_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    n_bins: int = 10
) -> pd.DataFrame:
    """
    Generates calibration table showing probability bin, count, predicted mean, and actual win rate.
    """
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy="uniform")
    
    bin_boundaries = np.linspace(0.0, 1.0, n_bins + 1)
    bins_data = []
    
    for i in range(n_bins):
        bin_lower = bin_boundaries[i]
        bin_upper = bin_boundaries[i + 1]
        
        if i == n_bins - 1:
            in_bin = (y_prob >= bin_lower) & (y_prob <= bin_upper)
        else:
            in_bin = (y_prob >= bin_lower) & (y_prob < bin_upper)
            
        count = int(np.sum(in_bin))
        if count > 0:
            actual_rate = float(np.mean(y_true[in_bin]))
            pred_mean = float(np.mean(y_prob[in_bin]))
        else:
            actual_rate = np.nan
            pred_mean = (bin_lower + bin_upper) / 2.0
            
        bins_data.append({
            "bin_range": f"{bin_lower:.1f}-{bin_upper:.1f}",
            "sample_count": count,
            "mean_predicted_prob": pred_mean,
            "actual_win_rate": actual_rate,
            "calibration_gap": abs(pred_mean - actual_rate) if pd.notna(actual_rate) else np.nan
        })
        
    return pd.DataFrame(bins_data)


def evaluate_classification_predictions(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    y_pred: Optional[np.ndarray] = None
) -> Dict[str, float]:
    """
    Calculates comprehensive classification metrics:
    - Log Loss (primary)
    - Brier Score (secondary)
    - ROC-AUC
    - Accuracy
    - Expected Calibration Error (ECE)
    """
    y_true = np.asarray(y_true).astype(int)
    
    if y_prob.ndim == 2:
        prob_pos = y_prob[:, 1]
    else:
        prob_pos = y_prob
        
    prob_pos = np.clip(prob_pos, 1e-15, 1.0 - 1e-15)
    
    if y_pred is None:
        y_pred = (prob_pos >= 0.5).astype(int)
    else:
        y_pred = np.asarray(y_pred).astype(int)
        
    acc = accuracy_score(y_true, y_pred)
    
    # Check if ROC-AUC is computable (both classes present)
    if len(np.unique(y_true)) > 1:
        roc_auc = roc_auc_score(y_true, prob_pos)
    else:
        roc_auc = np.nan
        
    ll = log_loss(y_true, prob_pos, labels=[0, 1])
    brier = brier_score_loss(y_true, prob_pos, pos_label=1)
    ece = compute_expected_calibration_error(y_true, prob_pos)
    
    return {
        "accuracy": float(acc),
        "roc_auc": float(roc_auc),
        "log_loss": float(ll),
        "brier_score": float(brier),
        "ece": float(ece)
    }


def evaluate_regression_predictions(
    y_true: np.ndarray,
    y_pred: np.ndarray
) -> Dict[str, float]:
    """
    Calculates regression metrics:
    - MAE (primary)
    - RMSE (secondary)
    - Mean Error / Bias
    """
    y_true = np.asarray(y_true).astype(float)
    y_pred = np.asarray(y_pred).astype(float)
    
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    rmse = float(np.sqrt(mse))
    bias = float(np.mean(y_pred - y_true))
    
    return {
        "mae": float(mae),
        "rmse": float(rmse),
        "bias": float(bias)
    }
