import os
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from src.monitoring.repository import PredictionRepository
from src.monitoring.metrics import MonitoringMetricsService
from src.monitoring.drift import DataDriftDetector
from src.monitoring.collector import metrics_collector
from src.features.player_prediction_features import PLAYER_FEATURE_CONTRACT
from src.utils.logging import logger, log_event

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
    Evaluates multi-dimensional production model health across performance, drift, and calibration,
    as well as artifact integrity, readiness, and shadow isolation.
    """
    def __init__(
        self,
        repository: Optional[PredictionRepository] = None,
        metrics_service: Optional[MonitoringMetricsService] = None,
        drift_detector: Optional[DataDriftDetector] = None,
        base_dir: Optional[str] = None
    ):
        self.base_dir = base_dir or os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.repo = repository or PredictionRepository()
        self.metrics_service = metrics_service or MonitoringMetricsService(self.repo)
        self.drift_detector = drift_detector or DataDriftDetector(repository=self.repo)

    def check_liveness(self) -> Dict[str, Any]:
        """
        Instantaneous process liveness check. Performs zero I/O or heavy computation.
        """
        return {
            "status": "healthy",
            "service": "Lakers in 5 Prediction Service",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def check_database_health(self) -> Dict[str, Any]:
        """
        Tests database / repository connectivity and returns structured health report.
        """
        log_event(logger, "database_check_started", level=10)
        try:
            from sqlalchemy import text
            db_status = "healthy"
            db_type = "parquet_fallback"
            if self.repo.engine is not None:
                with self.repo.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                db_type = self.repo.engine.dialect.name
            
            log_event(logger, "database_check_completed", level=10, db_type=db_type, status=db_status)
            return {
                "status": "healthy",
                "backend": db_type,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }
        except Exception as e:
            log_event(logger, "database_check_failed", level=40, error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

    def check_model_health(self) -> Dict[str, Any]:
        """
        Validates artifact integrity, metadata contracts, and loading state for
        both Production (PlayerSuite-v1.0) and Frozen Shadow (PlayerSuite-v1.1-c1-shadow).
        """
        prod_models_dir = os.path.join(self.base_dir, "models")
        shadow_models_dir = os.path.join(self.base_dir, "models", "experimental", "c1_role_stratified")

        # 1. Validate Production Models
        prod_health: Dict[str, Any] = {"status": "healthy", "version": "PlayerSuite-v1.0", "artifacts": {}}
        required_prod_files = [
            "player_minutes_model.joblib",
            "player_points_model.joblib",
            "player_rebounds_model.joblib",
            "player_assists_model.joblib",
            "player_models_metadata.json"
        ]
        
        prod_missing = []
        for fname in required_prod_files:
            fpath = os.path.join(prod_models_dir, fname)
            exists = os.path.exists(fpath)
            prod_health["artifacts"][fname] = {"exists": exists}
            if not exists:
                prod_missing.append(fname)

        if prod_missing:
            prod_health["status"] = "unhealthy"
            prod_health["error"] = f"Missing required production artifacts: {prod_missing}"
            metrics_collector.set_gauge("models_loaded", 0.0)
        else:
            # Check metadata contract
            meta_path = os.path.join(prod_models_dir, "player_models_metadata.json")
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                feat_contract = meta.get("feature_contract") or meta.get("features", [])
                if len(feat_contract) != 24:
                    prod_health["status"] = "unhealthy"
                    prod_health["error"] = f"Expected 24 features in metadata, got {len(feat_contract)}."
                else:
                    prod_health["feature_contract_version"] = meta.get("feature_schema_version", "PLAYER_FEATURE_CONTRACT_V1")
                    metrics_collector.set_gauge("models_loaded", 1.0)
            except Exception as e:
                prod_health["status"] = "unhealthy"
                prod_health["error"] = f"Failed to parse production metadata: {e}"
                metrics_collector.set_gauge("models_loaded", 0.0)

        # 2. Validate Frozen Shadow Model
        shadow_health: Dict[str, Any] = {"status": "healthy", "version": "PlayerSuite-v1.1-c1-shadow", "artifacts": {}}
        required_shadow_files = [
            "shadow_points_model.joblib",
            "shadow_minutes_model.joblib",
            "shadow_rebounds_model.joblib",
            "shadow_assists_model.joblib",
            "shadow_models_metadata.json"
        ]
        
        shadow_missing = []
        for fname in required_shadow_files:
            fpath = os.path.join(shadow_models_dir, fname)
            exists = os.path.exists(fpath)
            shadow_health["artifacts"][fname] = {"exists": exists}
            if not exists:
                shadow_missing.append(fname)

        if shadow_missing:
            shadow_health["status"] = "degraded"
            shadow_health["error"] = f"Shadow artifacts missing: {shadow_missing}"
            metrics_collector.set_gauge("shadow_model_available", 0.0)
        else:
            meta_path = os.path.join(shadow_models_dir, "shadow_models_metadata.json")
            try:
                with open(meta_path, "r") as f:
                    meta = json.load(f)
                if meta.get("model_version") != "PlayerSuite-v1.1-c1-shadow":
                    shadow_health["status"] = "degraded"
                    shadow_health["error"] = f"Shadow model version mismatch: {meta.get('model_version')}"
                    metrics_collector.set_gauge("shadow_model_available", 0.0)
                else:
                    shadow_health["roles"] = list(meta.get("role_definitions", {}).keys()) or ["star", "starter", "bench"]
                    metrics_collector.set_gauge("shadow_model_available", 1.0)
            except Exception as e:
                shadow_health["status"] = "degraded"
                shadow_health["error"] = f"Failed to parse shadow metadata: {e}"
                metrics_collector.set_gauge("shadow_model_available", 0.0)

        # Overall System Status calculation
        if prod_health["status"] == "unhealthy":
            overall_status = "unhealthy"
        elif shadow_health["status"] == "degraded":
            overall_status = "degraded"
        else:
            overall_status = "healthy"

        return {
            "status": overall_status,
            "production": prod_health,
            "shadow": shadow_health,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

    def check_readiness(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Serving readiness probe. Verifies that critical production components are available.
        Fails if production models are missing. Shadow degradation does NOT fail readiness.
        """
        model_diag = self.check_model_health()
        db_diag = self.check_database_health()

        is_prod_ready = model_diag.get("production", {}).get("status") == "healthy"
        is_ready = is_prod_ready

        status_str = "healthy" if is_ready and model_diag["status"] == "healthy" else ("degraded" if is_ready else "unhealthy")

        report = {
            "ready": is_ready,
            "status": status_str,
            "models": model_diag,
            "database": db_diag,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        return is_ready, report

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
        anomalies = pred_drift.get("anomaly_flags", []) if pred_drift else []
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
