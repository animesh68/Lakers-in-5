"""
Data Drift & Prediction Distribution Monitoring for Lakers in 5.
Computes Population Stability Index (PSI), mean/std shifts, missingness rates,
and output distribution shifts between reference training features and current production data.
"""

import os
import json
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from src.monitoring.repository import PredictionRepository
from src.inference.feature_service import MODEL_FEATURE_CONTRACT
from src.utils.logging import logger

PSI_THRESHOLD_LOW = 0.10
PSI_THRESHOLD_MODERATE = 0.25

def calculate_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    epsilon: float = 1e-4
) -> float:
    """
    Computes Population Stability Index (PSI) between reference (expected) and current (actual) feature arrays.
    PSI = sum((Actual_b - Expected_b) * ln(Actual_b / Expected_b))
    """
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]
    
    if len(expected) == 0 or len(actual) == 0:
        return 0.0

    # Determine quantile bins from reference distribution
    percentiles = np.linspace(0, 100, num_bins + 1)
    bin_edges = np.percentile(expected, percentiles)
    # Ensure strictly increasing bins
    bin_edges = np.unique(bin_edges)
    if len(bin_edges) < 2:
        return 0.0

    bin_edges[0] = -np.inf
    bin_edges[-1] = np.inf

    expected_counts, _ = np.histogram(expected, bins=bin_edges)
    actual_counts, _ = np.histogram(actual, bins=bin_edges)

    expected_pct = expected_counts / len(expected)
    actual_pct = actual_counts / len(actual)

    # Apply smoothing epsilon
    expected_pct = np.clip(expected_pct, epsilon, None)
    actual_pct = np.clip(actual_pct, epsilon, None)

    # Normalize after clipping
    expected_pct = expected_pct / np.sum(expected_pct)
    actual_pct = actual_pct / np.sum(actual_pct)

    psi_val = np.sum((actual_pct - expected_pct) * np.log(actual_pct / expected_pct))
    return float(np.maximum(0.0, psi_val))


class DataDriftDetector:
    """
    Compares recent production feature distributions against historical training distributions.
    """
    def __init__(
        self,
        reference_features_path: Optional[str] = None,
        repository: Optional[PredictionRepository] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.ref_path = reference_features_path or os.path.join(
            base_dir, "data", "features", "game_features.parquet"
        )
        self.repo = repository or PredictionRepository()
        self._reference_df: Optional[pd.DataFrame] = None
        self._reference_stats: Dict[str, Dict[str, float]] = {}

    def _load_reference_data(self) -> pd.DataFrame:
        """Loads and caches reference historical feature distributions."""
        if self._reference_df is None:
            if os.path.exists(self.ref_path):
                df = pd.read_parquet(self.ref_path)
                # Filter to development seasons (e.g., 2015-2024)
                dev_df = df[df["season"].isin(range(2015, 2025))]
                if dev_df.empty:
                    dev_df = df
                cols = [c for c in MODEL_FEATURE_CONTRACT if c in dev_df.columns]
                self._reference_df = dev_df[cols]
                
                # Precompute summary stats
                for c in cols:
                    vals = self._reference_df[c].dropna().values
                    self._reference_stats[c] = {
                        "mean": float(np.mean(vals)) if len(vals) > 0 else 0.0,
                        "std": float(np.std(vals)) if len(vals) > 0 else 1.0,
                        "missing_rate": float(self._reference_df[c].isna().mean())
                    }
            else:
                logger.warning(f"Reference features parquet not found at {self.ref_path}")
                self._reference_df = pd.DataFrame(columns=MODEL_FEATURE_CONTRACT)
        return self._reference_df

    def compute_feature_drift(
        self,
        current_features_df: Optional[pd.DataFrame] = None,
        window: str = "30d"
    ) -> Dict[str, Any]:
        """
        Calculates drift metrics (PSI, mean shift, std shift, missing rate shift) for all features.
        If current_features_df is None, pulls feature vectors from persisted predictions.
        """
        ref_df = self._load_reference_data()
        
        if current_features_df is None:
            # Extract feature snapshots from predictions in repository
            preds = self.repo.get_predictions(limit=5000)
            feature_rows = []
            for p in preds:
                if p.features_json:
                    try:
                        feature_rows.append(json.loads(p.features_json))
                    except Exception:
                        pass
            if feature_rows:
                current_features_df = pd.DataFrame(feature_rows)
            else:
                current_features_df = pd.DataFrame(columns=MODEL_FEATURE_CONTRACT)

        features_report = []
        high_drift_count = 0
        moderate_drift_count = 0
        low_drift_count = 0

        for col in MODEL_FEATURE_CONTRACT:
            if col not in ref_df.columns:
                continue

            ref_vals = ref_df[col].dropna().values
            ref_stat = self._reference_stats.get(col, {"mean": 0.0, "std": 1.0, "missing_rate": 0.0})

            if not current_features_df.empty and col in current_features_df.columns:
                curr_series = current_features_df[col]
                curr_vals = curr_series.dropna().values
                curr_mean = float(np.mean(curr_vals)) if len(curr_vals) > 0 else ref_stat["mean"]
                curr_std = float(np.std(curr_vals)) if len(curr_vals) > 0 else ref_stat["std"]
                curr_missing = float(curr_series.isna().mean())
                
                psi = calculate_psi(ref_vals, curr_vals) if len(curr_vals) >= 5 else 0.0
            else:
                curr_mean = ref_stat["mean"]
                curr_std = ref_stat["std"]
                curr_missing = ref_stat["missing_rate"]
                psi = 0.0

            ref_std = ref_stat["std"] if ref_stat["std"] > 1e-9 else 1.0
            mean_shift = (curr_mean - ref_stat["mean"]) / ref_std
            std_shift = curr_std / ref_std
            missing_shift = abs(curr_missing - ref_stat["missing_rate"])

            if psi > PSI_THRESHOLD_MODERATE:
                status = "high"
                high_drift_count += 1
            elif psi >= PSI_THRESHOLD_LOW:
                status = "moderate"
                moderate_drift_count += 1
            else:
                status = "low"
                low_drift_count += 1

            features_report.append({
                "feature": col,
                "psi": round(psi, 4),
                "mean_shift": round(mean_shift, 4),
                "std_shift": round(std_shift, 4),
                "missing_rate_shift": round(missing_shift, 4),
                "status": status,
                "ref_mean": round(ref_stat["mean"], 4),
                "curr_mean": round(curr_mean, 4),
            })

        # Sort features by highest PSI
        features_report.sort(key=lambda x: x["psi"], reverse=True)

        return {
            "window": window,
            "sample_size": len(current_features_df),
            "features_high_drift": high_drift_count,
            "features_moderate_drift": moderate_drift_count,
            "features_low_drift": low_drift_count,
            "total_features_evaluated": len(features_report),
            "features": features_report
        }

    def compute_prediction_drift(self, window: str = "30d") -> Dict[str, Any]:
        """
        Monitors the output distribution of home_win_probability and predicted_home_margin.
        Detects anomalies like extreme concentration or probability collapse toward 0.5.
        """
        preds = self.repo.get_predictions(limit=5000)
        if not preds:
            return {
                "sample_size": 0,
                "win_prob_mean": 0.5,
                "win_prob_std": 0.0,
                "margin_mean": 0.0,
                "margin_std": 0.0,
                "entropy": 1.0,
                "anomaly_flags": []
            }

        probs = np.array([p.home_win_probability for p in preds], dtype=float)
        margins = np.array([p.predicted_home_margin for p in preds], dtype=float)

        p_mean = float(np.mean(probs))
        p_std = float(np.std(probs))
        m_mean = float(np.mean(margins))
        m_std = float(np.std(margins))

        # Approximate binary entropy
        p_clipped = np.clip(probs, 1e-6, 1.0 - 1e-6)
        entropies = -(p_clipped * np.log2(p_clipped) + (1.0 - p_clipped) * np.log2(1.0 - p_clipped))
        mean_entropy = float(np.mean(entropies))

        anomalies = []
        if p_std < 0.05 and len(probs) >= 20:
            anomalies.append("PROBABILITY_COLLAPSE_NEAR_MEAN")
        if (p_mean < 0.40 or p_mean > 0.70) and len(probs) >= 20:
            anomalies.append("EXTREME_HOME_WIN_BIAS")
        if abs(m_mean) > 8.0 and len(margins) >= 20:
            anomalies.append("EXTREME_MARGIN_SHIFT")

        return {
            "sample_size": len(preds),
            "win_prob_mean": round(p_mean, 4),
            "win_prob_std": round(p_std, 4),
            "margin_mean": round(m_mean, 4),
            "margin_std": round(m_std, 4),
            "entropy": round(mean_entropy, 4),
            "anomaly_flags": anomalies
        }
