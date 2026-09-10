"""
Comprehensive Test Suite for Phase 5 Monitoring, Prediction Logging & Dashboard.
Tests persistence, feature hashing, outcome ingestion, metrics, calibration, drift (PSI),
model health, retraining recommendation governance, FastAPI endpoints, and dashboard loaders.
"""

import os
import uuid
from datetime import datetime, date, timedelta
import pytest
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from src.monitoring.store import PredictionRecord
from src.monitoring.repository import PredictionRepository
from src.monitoring.outcomes import OutcomeIngestionService
from src.monitoring.metrics import MonitoringMetricsService
from src.monitoring.drift import DataDriftDetector, calculate_psi
from src.monitoring.health import ModelHealthService, RetrainingDecisionEngine
from src.inference.predictor import GamePredictor, compute_feature_hash
from src.inference.api import app
from src.dashboard.app import load_recent_predictions, load_next_lakers_game


@pytest.fixture
def temp_repo(tmp_path):
    """Fixture providing a PredictionRepository isolated in a temporary directory."""
    return PredictionRepository(fallback_dir=str(tmp_path / "monitoring_test"), use_db=False)


def test_deterministic_feature_hashing():
    """Verifies that feature hashing is deterministic and independent of dictionary insertion order."""
    feat1 = {
        "home_elo": 1550.0,
        "away_elo": 1500.0,
        "elo_difference": 150.0,
        "home_win_pct_5": 0.6,
        "away_win_pct_5": 0.4
    }
    # Same data, reversed insertion order
    feat2 = {
        "away_win_pct_5": 0.4000000001,
        "home_win_pct_5": 0.6,
        "elo_difference": 150.0,
        "away_elo": 1500.0,
        "home_elo": 1550.0
    }
    hash1 = compute_feature_hash(feat1)
    hash2 = compute_feature_hash(feat2)
    assert hash1 == hash2, "Identical features in different key orders must produce identical SHA-256 hashes"

    # Perturbed data produces different hash
    feat3 = dict(feat1)
    feat3["home_elo"] = 1600.0
    hash3 = compute_feature_hash(feat3)
    assert hash1 != hash3, "Different feature values must produce different hashes"


def test_prediction_persistence_and_retrieval(temp_repo):
    """Tests saving and retrieving prediction records from repository."""
    rec = PredictionRecord(
        prediction_id=str(uuid.uuid4()),
        game_id="TEST-001",
        game_date="2026-10-21",
        home_team="Los Angeles Lakers",
        away_team="Golden State Warriors",
        home_team_id="1610612747",
        away_team_id="1610612744",
        model_version="Test-Classifier / Test-Regressor",
        classifier_model_version="Test-Classifier",
        regressor_model_version="Test-Regressor",
        home_win_probability=0.72,
        away_win_probability=0.28,
        predicted_home_margin=6.5,
        feature_schema_version="v1",
        feature_snapshot_hash="test_hash_123456",
        status="pending"
    )
    saved = temp_repo.save_prediction(rec)
    assert saved.prediction_id == rec.prediction_id

    # Retrieve by ID
    fetched = temp_repo.get_prediction_by_id(rec.prediction_id)
    assert fetched is not None
    assert fetched.home_team == "Los Angeles Lakers"
    assert fetched.home_win_probability == 0.72
    assert fetched.status == "pending"

    # Query with filters
    results = temp_repo.get_predictions(team="Lakers", status="pending")
    assert len(results) >= 1
    assert results[0].prediction_id == rec.prediction_id


def test_persistence_idempotency(temp_repo):
    """Verifies that saving an existing prediction_id updates fields without duplicating records."""
    pid = str(uuid.uuid4())
    rec1 = PredictionRecord(
        prediction_id=pid,
        game_id="TEST-IDEM",
        game_date="2026-10-21",
        home_team="Los Angeles Lakers",
        away_team="Phoenix Suns",
        home_team_id="1610612747",
        away_team_id="1610612756",
        model_version="Model-v1",
        classifier_model_version="Clf-v1",
        regressor_model_version="Reg-v1",
        home_win_probability=0.55,
        away_win_probability=0.45,
        predicted_home_margin=2.0,
        feature_snapshot_hash="hash_a",
        status="pending"
    )
    temp_repo.save_prediction(rec1)

    # Save again with updated margin
    rec2 = rec1.model_copy(update={"predicted_home_margin": 3.5, "status": "completed"})
    temp_repo.save_prediction(rec2)

    all_preds = temp_repo.get_predictions(limit=100)
    matching = [p for p in all_preds if p.prediction_id == pid]
    assert len(matching) == 1, "Idempotent save must not duplicate records"
    assert matching[0].predicted_home_margin == 3.5
    assert matching[0].status == "completed"


def test_outcome_ingestion(temp_repo):
    """Tests settling completed games vs leaving future scheduled games pending."""
    # 1. Prediction for a real historical game (Denver vs Lakers on 2023-10-24)
    rec_completed = PredictionRecord(
        prediction_id=str(uuid.uuid4()),
        game_id="22300061",
        game_date="2023-10-24",
        home_team="Denver Nuggets",
        away_team="Los Angeles Lakers",
        home_team_id="1610612743",
        away_team_id="1610612747",
        model_version="Model-v1",
        classifier_model_version="Clf-v1",
        regressor_model_version="Reg-v1",
        home_win_probability=0.60,
        away_win_probability=0.40,
        predicted_home_margin=4.0,
        feature_snapshot_hash="hist_hash",
        status="pending"
    )
    # 2. Prediction for a future game in 2026
    rec_future = PredictionRecord(
        prediction_id=str(uuid.uuid4()),
        game_id="FUTURE-999",
        game_date="2026-12-25",
        home_team="Los Angeles Lakers",
        away_team="Boston Celtics",
        home_team_id="1610612747",
        away_team_id="1610612738",
        model_version="Model-v1",
        classifier_model_version="Clf-v1",
        regressor_model_version="Reg-v1",
        home_win_probability=0.52,
        away_win_probability=0.48,
        predicted_home_margin=1.0,
        feature_snapshot_hash="future_hash",
        status="pending"
    )

    temp_repo.save_prediction(rec_completed)
    temp_repo.save_prediction(rec_future)

    outcome_svc = OutcomeIngestionService(repository=temp_repo)
    res = outcome_svc.update_pending_outcomes()

    # Verify future game remains pending
    fut_fetched = temp_repo.get_prediction_by_id(rec_future.prediction_id)
    assert fut_fetched.status == "pending"
    assert fut_fetched.actual_home_score is None

    # Verify completed game (if found in lakehouse) is completed
    if res.get("updated_count", 0) > 0:
        comp_fetched = temp_repo.get_prediction_by_id(rec_completed.prediction_id)
        assert comp_fetched.status == "completed"
        assert comp_fetched.actual_home_score is not None
        assert comp_fetched.actual_home_win in [0, 1]


def test_monitoring_metrics_synthetic(temp_repo):
    """Tests rolling performance metrics calculation on synthetic known predictions."""
    metrics_svc = MonitoringMetricsService(repository=temp_repo)

    now = datetime.utcnow()
    for i in range(10):
        actual_win = 1 if i % 2 == 0 else 0
        pred_prob = 0.70 if actual_win == 1 else 0.30
        actual_margin = 8.0 if actual_win == 1 else -6.0
        pred_margin = 6.0 if actual_win == 1 else -4.0

        rec = PredictionRecord(
            prediction_id=f"SYNTH-{i}",
            game_date=(now - timedelta(days=i)).strftime("%Y-%m-%d"),
            home_team="Team A",
            away_team="Team B",
            home_team_id="1",
            away_team_id="2",
            model_version="TestModel",
            classifier_model_version="TestClf",
            regressor_model_version="TestReg",
            home_win_probability=pred_prob,
            away_win_probability=1.0 - pred_prob,
            predicted_home_margin=pred_margin,
            feature_snapshot_hash="hash",
            status="completed",
            actual_home_score=108 if actual_win == 1 else 94,
            actual_away_score=100 if actual_win == 1 else 100,
            actual_home_win=actual_win,
            actual_home_margin=actual_margin,
            prediction_created_at=now - timedelta(days=i)
        )
        temp_repo.save_prediction(rec)

    metrics_7d = metrics_svc.compute_performance_metrics(window="7d", ref_date=now)
    assert metrics_7d["sample_count"] <= 8
    assert metrics_7d["classification"]["accuracy"] == 1.0
    assert metrics_7d["regression"]["mae"] == 2.0

    metrics_all = metrics_svc.compute_performance_metrics(window="all_time", ref_date=now)
    assert metrics_all["sample_count"] == 10
    assert metrics_all["classification"]["accuracy"] == 1.0


def test_calibration_monitoring(temp_repo):
    """Tests decile calibration curve generator."""
    metrics_svc = MonitoringMetricsService(repository=temp_repo)
    
    probs = np.linspace(0.05, 0.95, 20)
    for i, p in enumerate(probs):
        win = 1 if p >= 0.5 else 0
        rec = PredictionRecord(
            prediction_id=f"CALIB-{i}",
            game_date="2026-10-21",
            home_team="Team A",
            away_team="Team B",
            home_team_id="1",
            away_team_id="2",
            model_version="TestModel",
            classifier_model_version="TestClf",
            regressor_model_version="TestReg",
            home_win_probability=float(p),
            away_win_probability=float(1.0 - p),
            predicted_home_margin=0.0,
            feature_snapshot_hash="hash",
            status="completed",
            actual_home_win=win,
            actual_home_margin=0.0
        )
        temp_repo.save_prediction(rec)

    cal_table = metrics_svc.compute_calibration_table(window="all_time", n_bins=10)
    assert isinstance(cal_table, pd.DataFrame)
    assert len(cal_table) == 10
    assert "mean_predicted_prob" in cal_table.columns
    assert "actual_win_rate" in cal_table.columns


def test_drift_detection_psi():
    """Tests PSI computation on stable and shifted distributions."""
    np.random.seed(42)
    ref = np.random.normal(0.0, 1.0, 1000)
    stable_curr = np.random.normal(0.0, 1.0, 1000)
    shifted_curr = np.random.normal(2.5, 1.5, 1000)

    psi_stable = calculate_psi(ref, stable_curr)
    psi_shifted = calculate_psi(ref, shifted_curr)

    assert psi_stable < 0.10, f"Stable distribution should have PSI < 0.10, got {psi_stable}"
    assert psi_shifted > 0.25, f"Heavily shifted distribution should have PSI > 0.25, got {psi_shifted}"


def test_model_health_and_retraining_decision(temp_repo):
    """Tests healthy vs degraded states producing expected health status and retraining advice."""
    health_svc = ModelHealthService(repository=temp_repo)
    retrain_engine = RetrainingDecisionEngine(repository=temp_repo, health_service=health_svc)

    # Empty / low sample size -> Healthy baseline with NO_RETRAIN_NEEDED
    health_res = health_svc.evaluate_health(window="all_time")
    assert health_res["status"] == "HEALTHY"

    retrain_res = retrain_engine.evaluate_retraining_decision(window="all_time")
    assert retrain_res["decision"] == "NO_RETRAIN_NEEDED"
    assert retrain_res["is_automatic_retrain"] is False


def test_fastapi_monitoring_endpoints():
    """Tests all FastAPI /monitoring/* endpoints via TestClient."""
    client = TestClient(app)

    # 1. Service health
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"

    # 2. Model health diagnostic
    res = client.get("/monitoring/health?window=30d")
    assert res.status_code == 200
    assert "status" in res.json()

    # 3. Performance
    res = client.get("/monitoring/performance?window=30d")
    assert res.status_code == 200
    assert "classification" in res.json()

    # 4. Calibration
    res = client.get("/monitoring/calibration?window=season")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 5. Drift
    res = client.get("/monitoring/drift?window=30d")
    assert res.status_code == 200
    assert "feature_drift" in res.json()

    # 6. Predictions list
    res = client.get("/monitoring/predictions?limit=10")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # 7. Retraining decision
    res = client.get("/monitoring/retraining-decision?window=season")
    assert res.status_code == 200
    assert res.json()["decision"] in ["NO_RETRAIN_NEEDED", "RETRAIN_RECOMMENDED"]
    assert res.json()["is_automatic_retrain"] is False


def test_dashboard_data_loaders(temp_repo):
    """Tests dashboard helper functions headlessly without launching a browser."""
    predictor = GamePredictor(repository=temp_repo)
    
    # Load next Lakers game
    lakers_pred = load_next_lakers_game(predictor, as_of_date="2026-10-20")
    assert lakers_pred is not None
    assert "Lakers" in lakers_pred.matchup
    assert 0.0 <= lakers_pred.lakers_win_probability <= 1.0

    # Load recent predictions table
    df = load_recent_predictions(temp_repo)
    assert isinstance(df, pd.DataFrame)


def test_retraining_decision_triggers(temp_repo):
    """Verifies that the retraining engine fires triggers under each degradation condition when sample size >= 50."""
    health_svc = ModelHealthService(repository=temp_repo)
    retrain_engine = RetrainingDecisionEngine(repository=temp_repo, health_service=health_svc)

    now = datetime.utcnow()
    # Populate 50 completed games with degraded performance (low accuracy, high log loss)
    for i in range(50):
        rec = PredictionRecord(
            prediction_id=f"DEG-{i}",
            game_date=(now - timedelta(days=i)).strftime("%Y-%m-%d"),
            home_team="Team A",
            away_team="Team B",
            home_team_id="1",
            away_team_id="2",
            model_version="DegradedModel",
            classifier_model_version="DegClf",
            regressor_model_version="DegReg",
            home_win_probability=0.90,  # Overconfident
            away_win_probability=0.10,
            predicted_home_margin=15.0,  # Highly inaccurate
            feature_snapshot_hash="deg_hash",
            status="completed",
            actual_home_win=0,  # Always loses -> high log loss and high MAE
            actual_home_margin=-10.0,
            actual_home_score=90,
            actual_away_score=100,
            prediction_created_at=now - timedelta(days=i)
        )
        temp_repo.save_prediction(rec)

    decision_res = retrain_engine.evaluate_retraining_decision(window="all_time")
    assert decision_res["decision"] == "RETRAIN_RECOMMENDED"
    assert decision_res["sample_count"] == 50
    assert len(decision_res["reasons"]) > 1
    assert decision_res["is_automatic_retrain"] is False


def test_drift_edge_cases_constant_and_empty():
    """Tests that calculate_psi gracefully handles zero samples and constant distributions."""
    empty_arr = np.array([])
    normal_arr = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert calculate_psi(empty_arr, normal_arr) == 0.0
    assert calculate_psi(normal_arr, empty_arr) == 0.0

    # Single constant value
    constant_arr = np.array([5.0] * 50)
    assert calculate_psi(constant_arr, constant_arr) == 0.0

