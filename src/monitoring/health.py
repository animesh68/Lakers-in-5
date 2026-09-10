"""
Model Health Diagnostic & Retraining Decision Engine for Lakers in 5.
Evaluates production health (HEALTHY, WARNING, CRITICAL) and deterministic
retraining advisory decisions with explicit, documented operational heuristics.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.monitoring.repository import PredictionRepository
from src.monitoring.metrics import MonitoringMetricsService
from src.monitoring.drift import DataDriftDetector
from src.utils.logging import logger

# Operational Health Thresholds
LOG_LOSS_WARNING_THRESHOLD = 0.630
LOG_LOSS_CRITICAL_THRESHOLD = 0.660

MAE_WARNING_THRESHOLD = 11.2
MAE_CRITICAL_THRESHOLD = 12.5

ECE_WARNING_THRESHOLD = 0.050
ECE_CRITICAL_THRESHOLD = 0.090

DRIFT_HIGH_WARNING_COUNT = 3
DRIFT_HIGH_CRITICAL_COUNT = 5

MIN_SAMPLES_FOR_EVALUATION = 15
MIN_SAMPLES_FOR_RETRAIN_TRIGGER = 50

class ModelHealthService:
    """
    Evaluates multi-dimensional production model health across performance, drift, and calibration.
    """
    def __init__(
        self,
        repository: Optional[PredictionRepository] = None,
        metrics_service: Optional[MonitoringMetricsService] = None,
        drift_detector: Optional[DataDriftDetector] = None
    ):
        self.repo = repository or PredictionRepository()
        self.metrics_service = metrics_service or MonitoringMetricsService(self.repo)
        self.drift_detector = drift_detector or DataDriftDetector(repository=self.repo)

    def evaluate_health(self, window: str = "30d") -> Dict[str, Any]:
        """
        Produces a comprehensive model health diagnostic report.
        Status: 'HEALTHY' | 'WARNING' | 'CRITICAL'
        """
        perf = self.metrics_service.compute_performance_metrics(window=window)
        drift = self.drift_detector.compute_feature_drift(window=window)
        pred_drift = self.drift_detector.compute_prediction_drift(window=window)

        reasons = []
        status = "HEALTHY"

        clf_metrics = perf.get("classification", {})
        reg_metrics = perf.get("regression", {})
        sample_count = perf.get("sample_count", 0)

        # Performance checks (only evaluate if sufficient sample size exists)
        if sample_count >= MIN_SAMPLES_FOR_EVALUATION:
            ll = clf_metrics.get("log_loss")
            if ll is not None:
                if ll > LOG_LOSS_CRITICAL_THRESHOLD:
                    status = "CRITICAL"
                    reasons.append(f"Classification log loss ({ll:.4f}) exceeds critical threshold ({LOG_LOSS_CRITICAL_THRESHOLD}).")
                elif ll > LOG_LOSS_WARNING_THRESHOLD:
                    if status != "CRITICAL":
                        status = "WARNING"
                    reasons.append(f"Classification log loss ({ll:.4f}) elevated above warning threshold ({LOG_LOSS_WARNING_THRESHOLD}).")

            mae = reg_metrics.get("mae")
            if mae is not None:
                if mae > MAE_CRITICAL_THRESHOLD:
                    status = "CRITICAL"
                    reasons.append(f"Margin MAE ({mae:.2f} pts) exceeds critical threshold ({MAE_CRITICAL_THRESHOLD} pts).")
                elif mae > MAE_WARNING_THRESHOLD:
                    if status != "CRITICAL":
                        status = "WARNING"
                    reasons.append(f"Margin MAE ({mae:.2f} pts) elevated above warning threshold ({MAE_WARNING_THRESHOLD} pts).")

            ece = clf_metrics.get("ece")
            if ece is not None:
                if ece > ECE_CRITICAL_THRESHOLD:
                    status = "CRITICAL"
                    reasons.append(f"Expected Calibration Error ({ece:.4f}) exceeds critical threshold ({ECE_CRITICAL_THRESHOLD}).")
                elif ece > ECE_WARNING_THRESHOLD:
                    if status != "CRITICAL":
                        status = "WARNING"
                    reasons.append(f"Expected Calibration Error ({ece:.4f}) elevated above warning threshold ({ECE_WARNING_THRESHOLD}).")
        else:
            reasons.append(f"Low evaluation sample size ({sample_count} completed games in {window} window). Baseline healthy.")

        # Data drift checks
        high_drift = drift.get("features_high_drift", 0)
        mod_drift = drift.get("features_moderate_drift", 0)

        if high_drift >= DRIFT_HIGH_CRITICAL_COUNT:
            status = "CRITICAL"
            reasons.append(f"{high_drift} features exhibiting significant drift (PSI > 0.25).")
        elif high_drift >= DRIFT_HIGH_WARNING_COUNT or mod_drift >= 8:
            if status != "CRITICAL":
                status = "WARNING"
            reasons.append(f"{high_drift} high drift and {mod_drift} moderate drift features detected.")

        # Output distribution anomalies
        anomalies = pred_drift.get("anomaly_flags", [])
        for anom in anomalies:
            if status != "CRITICAL":
                status = "WARNING"
            reasons.append(f"Prediction distribution anomaly detected: {anom}.")

        if not reasons:
            reasons.append("All performance, calibration, and drift metrics within nominal operating ranges.")

        return {
            "status": status,
            "window": window,
            "sample_count": sample_count,
            "evaluated_at": datetime.utcnow().isoformat() + "Z",
            "reasons": reasons,
            "performance": perf,
            "feature_drift": {
                "features_high_drift": high_drift,
                "features_moderate_drift": mod_drift,
                "features_low_drift": drift.get("features_low_drift", 0),
            },
            "prediction_distribution": pred_drift
        }


class RetrainingDecisionEngine:
    """
    Evaluates whether retraining should be recommended to ML engineers.
    Strictly a decision-support advisory service — NEVER executes automatic model deployment.
    """
    def __init__(
        self,
        repository: Optional[PredictionRepository] = None,
        health_service: Optional[ModelHealthService] = None
    ):
        self.repo = repository or PredictionRepository()
        self.health_service = health_service or ModelHealthService(repository=self.repo)

    def evaluate_retraining_decision(
        self,
        window: str = "season",
        baseline_log_loss: float = 0.6191,
        baseline_mae: float = 10.386
    ) -> Dict[str, Any]:
        """
        Determines retraining recommendation based on completed sample size, degradation, and drift.
        Returns 'RETRAIN_RECOMMENDED' or 'NO_RETRAIN_NEEDED'.
        """
        health = self.health_service.evaluate_health(window=window)
        perf = health.get("performance", {})
        sample_count = perf.get("sample_count", 0)

        reasons = []
        triggers = []

        clf = perf.get("classification", {})
        reg = perf.get("regression", {})
        drift = health.get("feature_drift", {})

        current_ll = clf.get("log_loss")
        current_mae = reg.get("mae")
        current_ece = clf.get("ece")
        high_drift_count = drift.get("features_high_drift", 0)

        # Condition 1: Sample size check
        if sample_count < MIN_SAMPLES_FOR_RETRAIN_TRIGGER:
            return {
                "decision": "NO_RETRAIN_NEEDED",
                "status": "sample_size_insufficient",
                "sample_count": sample_count,
                "min_sample_threshold": MIN_SAMPLES_FOR_RETRAIN_TRIGGER,
                "reasons": [
                    f"Insufficient new completed games ({sample_count}/{MIN_SAMPLES_FOR_RETRAIN_TRIGGER}) to warrant retraining."
                ],
                "evaluated_at": datetime.utcnow().isoformat() + "Z",
                "is_automatic_retrain": False
            }

        # Condition 2: Performance degradation
        if current_ll is not None and current_ll > (baseline_log_loss + 0.020):
            triggers.append(
                f"Classification log loss degraded to {current_ll:.4f} (baseline: {baseline_log_loss:.4f}, delta: +{current_ll - baseline_log_loss:.4f})."
            )

        if current_mae is not None and current_mae > (baseline_mae + 1.0):
            triggers.append(
                f"Margin MAE degraded to {current_mae:.2f} pts (baseline: {baseline_mae:.2f} pts, delta: +{current_mae - baseline_mae:.2f} pts)."
            )

        # Condition 3: Calibration decay
        if current_ece is not None and current_ece > 0.060:
            triggers.append(
                f"Probability calibration error (ECE: {current_ece:.4f}) elevated significantly above baseline (0.026)."
            )

        # Condition 4: High feature drift
        if high_drift_count >= 4:
            triggers.append(
                f"{high_drift_count} core input features exhibit significant population drift (PSI > 0.25)."
            )

        if triggers:
            decision = "RETRAIN_RECOMMENDED"
            reasons = [
                f"Sufficient completed sample volume reached ({sample_count} games)."
            ] + triggers
        else:
            decision = "NO_RETRAIN_NEEDED"
            reasons = [
                f"Completed sample size of {sample_count} games reached.",
                "Model performance remains within acceptable tolerance of development baselines.",
                "Feature drift and calibration metrics remain healthy."
            ]

        return {
            "decision": decision,
            "sample_count": sample_count,
            "min_sample_threshold": MIN_SAMPLES_FOR_RETRAIN_TRIGGER,
            "reasons": reasons,
            "metrics": {
                "current_log_loss": current_ll,
                "baseline_log_loss": baseline_log_loss,
                "current_mae": current_mae,
                "baseline_mae": baseline_mae,
                "current_ece": current_ece,
                "high_drift_features": high_drift_count
            },
            "evaluated_at": datetime.utcnow().isoformat() + "Z",
            "is_automatic_retrain": False
        }
