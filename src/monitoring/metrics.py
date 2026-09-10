"""
Monitoring Metrics & Performance Engine for Lakers in 5.
Calculates time-windowed classification, regression, and probability calibration metrics
over completed production predictions.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta, date
import numpy as np
import pandas as pd

from src.monitoring.repository import PredictionRepository
from src.monitoring.store import PredictionRecord
from src.models.evaluation import (
    evaluate_classification_predictions,
    evaluate_regression_predictions,
    compute_calibration_curve,
    compute_expected_calibration_error,
)
from src.utils.logging import logger

VALID_WINDOWS = ["7d", "30d", "season", "all_time"]

class MonitoringMetricsService:
    """
    Computes rolling performance and calibration benchmarks across specified time windows.
    """
    def __init__(self, repository: Optional[PredictionRepository] = None):
        self.repo = repository or PredictionRepository()

    def get_window_cutoff(self, window: str, ref_date: Optional[datetime] = None) -> Optional[datetime]:
        """Calculates start datetime cutoff for a given window name."""
        now = ref_date or datetime.utcnow()
        if window == "7d":
            return now - timedelta(days=7)
        elif window == "30d":
            return now - timedelta(days=30)
        elif window == "season":
            # Current NBA season boundary: if now is after Oct, season starts Oct 1 of same year, else Oct 1 of prev year
            year = now.year if now.month >= 10 else now.year - 1
            return datetime(year, 10, 1)
        elif window == "all_time":
            return None
        else:
            raise ValueError(f"Invalid window '{window}'. Must be one of {VALID_WINDOWS}.")

    def compute_performance_metrics(
        self,
        window: str = "30d",
        team: Optional[str] = None,
        model_version: Optional[str] = None,
        ref_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Computes full classification and regression performance metrics for the selected window.
        """
        if window not in VALID_WINDOWS:
            raise ValueError(f"Invalid window '{window}'. Must be one of {VALID_WINDOWS}.")

        cutoff = self.get_window_cutoff(window, ref_date=ref_date)
        start_date_str = cutoff.strftime("%Y-%m-%d") if cutoff else None

        all_preds = self.repo.get_predictions(
            start_date=start_date_str,
            team=team,
            model_version=model_version,
            limit=50000
        )

        completed_preds = [p for p in all_preds if p.status == "completed" and p.actual_home_win is not None]
        pending_preds = [p for p in all_preds if p.status == "pending"]

        total_count = len(all_preds)
        completed_count = len(completed_preds)
        pending_count = len(pending_preds)

        if completed_count == 0:
            return {
                "window": window,
                "sample_count": 0,
                "total_predictions": total_count,
                "completed_predictions": 0,
                "pending_predictions": pending_count,
                "coverage_rate": 0.0 if total_count == 0 else 0.0,
                "classification": {
                    "accuracy": None,
                    "log_loss": None,
                    "brier_score": None,
                    "roc_auc": None,
                    "ece": None,
                },
                "regression": {
                    "mae": None,
                    "rmse": None,
                    "bias": None,
                },
                "summary": {
                    "mean_home_win_prob": None,
                    "mean_confidence": None,
                    "home_win_rate_predicted": None,
                    "home_win_rate_actual": None,
                }
            }

        # Extract numpy arrays
        y_true_win = np.array([p.actual_home_win for p in completed_preds], dtype=int)
        y_prob_win = np.array([p.home_win_probability for p in completed_preds], dtype=float)
        
        y_true_margin = np.array([p.actual_home_margin for p in completed_preds], dtype=float)
        y_pred_margin = np.array([p.predicted_home_margin for p in completed_preds], dtype=float)

        clf_metrics = evaluate_classification_predictions(y_true_win, y_prob_win)
        reg_metrics = evaluate_regression_predictions(y_true_margin, y_pred_margin)

        mean_prob = float(np.mean(y_prob_win))
        mean_conf = float(np.mean(np.maximum(y_prob_win, 1.0 - y_prob_win)))
        pred_home_win_rate = float(np.mean(y_prob_win >= 0.5))
        actual_home_win_rate = float(np.mean(y_true_win))

        return {
            "window": window,
            "sample_count": completed_count,
            "total_predictions": total_count,
            "completed_predictions": completed_count,
            "pending_predictions": pending_count,
            "coverage_rate": float(completed_count / total_count) if total_count > 0 else 1.0,
            "classification": clf_metrics,
            "regression": reg_metrics,
            "summary": {
                "mean_home_win_prob": mean_prob,
                "mean_confidence": mean_conf,
                "home_win_rate_predicted": pred_home_win_rate,
                "home_win_rate_actual": actual_home_win_rate,
            }
        }

    def compute_calibration_table(
        self,
        window: str = "season",
        n_bins: int = 10,
        ref_date: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Generates decile calibration table for the given window.
        """
        cutoff = self.get_window_cutoff(window, ref_date=ref_date)
        start_date_str = cutoff.strftime("%Y-%m-%d") if cutoff else None

        preds = self.repo.get_predictions(start_date=start_date_str, status="completed", limit=50000)
        valid = [p for p in preds if p.actual_home_win is not None]

        if not valid:
            bin_bounds = np.linspace(0.0, 1.0, n_bins + 1)
            return pd.DataFrame([
                {
                    "bin_range": f"{bin_bounds[i]:.1f}-{bin_bounds[i+1]:.1f}",
                    "sample_count": 0,
                    "mean_predicted_prob": (bin_bounds[i] + bin_bounds[i+1]) / 2.0,
                    "actual_win_rate": np.nan,
                    "calibration_gap": np.nan
                }
                for i in range(n_bins)
            ])

        y_true = np.array([p.actual_home_win for p in valid], dtype=int)
        y_prob = np.array([p.home_win_probability for p in valid], dtype=float)

        return compute_calibration_curve(y_true, y_prob, n_bins=n_bins)
