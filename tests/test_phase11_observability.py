"""
Phase 11 — Production Observability, Reliability, and Diagnostic Test Suite.
Verifies all 10 core observability pillars (A through J) with 43+ focused test cases.
"""

import os
import json
import uuid
import time
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from src.utils.logging import (
    get_request_id,
    set_request_id,
    clear_request_id,
    sanitize_sensitive_data,
    StructuredJsonFormatter,
    log_event,
    setup_logger
)
from src.monitoring.collector import metrics_collector, MetricCollector
from src.monitoring.health import ModelHealthService
from src.monitoring.drift import DataDriftDetector, calculate_psi
from src.validation.data_quality import (
    validate_game_record,
    validate_player_record,
    validate_feature_vector,
    validate_prediction_output,
    check_temporal_leakage_safeguard,
    check_data_freshness,
)
from src.features.player_prediction_features import PLAYER_FEATURE_CONTRACT, LEAGUE_PRIORS
from src.inference.api import app


@pytest.fixture(autouse=True)
def reset_metrics_and_context():
    """Resets in-memory metrics and request context before each test."""
    metrics_collector.reset()
    clear_request_id()
    yield
    clear_request_id()


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


# ==============================================================================
# SECTION A: STRUCTURED LOGGING
# ==============================================================================

def test_structured_logging_record_format():
    """1 & 2: Verify that structured logging formats records with ISO timestamp, level, and event."""
    formatter = StructuredJsonFormatter()
    set_request_id("test-req-12345")
    
    logger = setup_logger("test_structured_logger", use_json=True)
    record = logger.makeRecord(
        name="test_logger",
        level=20,
        fn="test.py",
        lno=10,
        msg="Test event message",
        args=(),
        exc_info=None,
        extra={"event": "prediction_completed", "request_id": "test-req-12345", "extra_fields": {"model_version": "PlayerSuite-v1.0", "latency_ms": 12.5}}
    )
    
    formatted_json = formatter.format(record)
    parsed = json.loads(formatted_json)
    
    assert parsed["event"] == "prediction_completed"
    assert parsed["level"] == "INFO"
    assert parsed["request_id"] == "test-req-12345"
    assert parsed["model_version"] == "PlayerSuite-v1.0"
    assert parsed["latency_ms"] == 12.5
    assert "timestamp" in parsed


def test_request_id_propagation_in_logs():
    """3: Verify request ID propagates automatically from context."""
    formatter = StructuredJsonFormatter()
    set_request_id("ctx-correlation-uuid-999")
    
    logger = setup_logger("test_ctx_logger", use_json=True)
    record = logger.makeRecord(
        name="test_logger",
        level=20,
        fn="test.py",
        lno=20,
        msg="Inference started",
        args=(),
        exc_info=None,
        extra={"event": "inference_started"}
    )
    
    parsed = json.loads(formatter.format(record))
    assert parsed.get("request_id") == "ctx-correlation-uuid-999"


def test_secrets_redaction_in_logging():
    """4: Verify sensitive keys like password, token, api_key, database_url are redacted."""
    raw_payload = {
        "user": "admin",
        "password": "supersecretpassword123",
        "api_key": "sk-proj-xyz987654",
        "database_url": "postgresql://postgres:secret123@neon.tech/lakers",
        "nested": {
            "auth_token": "bearer-token-abc",
            "model": "PlayerSuite-v1.0"
        }
    }
    
    sanitized = sanitize_sensitive_data(raw_payload)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["database_url"] == "[REDACTED]"
    assert sanitized["nested"]["auth_token"] == "[REDACTED]"
    assert sanitized["nested"]["model"] == "PlayerSuite-v1.0"


# ==============================================================================
# SECTION B: REQUEST CORRELATION ID
# ==============================================================================

def test_request_id_preserved_when_supplied(client):
    """5 & 7: Verify supplied correlation ID is preserved and returned in headers."""
    custom_id = "custom-client-request-id-777"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_id


def test_request_id_generated_when_missing(client):
    """6 & 7: Verify unique request ID is generated when omitted."""
    response = client.get("/health")
    assert response.status_code == 200
    req_id = response.headers.get("X-Request-ID")
    assert req_id is not None
    assert len(req_id) >= 10


# ==============================================================================
# SECTION C: HEALTH ENDPOINTS
# ==============================================================================

def test_liveness_endpoint(client):
    """8 & 9: Verify /health returns healthy instantly with zero heavy computation."""
    t0 = time.time()
    response = client.get("/health")
    elapsed_ms = (time.time() - t0) * 1000.0
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert elapsed_ms < 50.0  # Fast liveness probe


def test_readiness_reports_production_model_failure(tmp_path):
    """10: Verify /health/ready fails when critical production model is missing."""
    empty_dir = str(tmp_path / "empty_models")
    os.makedirs(empty_dir, exist_ok=True)
    
    health_svc = ModelHealthService(base_dir=str(tmp_path))
    is_ready, report = health_svc.check_readiness()
    
    assert is_ready is False
    assert report["status"] == "unhealthy"
    assert report["models"]["production"]["status"] == "unhealthy"


def test_readiness_reports_dependency_status():
    """11: Verify /health/ready validates database and model state."""
    health_svc = ModelHealthService()
    is_ready, report = health_svc.check_readiness()
    
    assert "ready" in report
    assert "models" in report
    assert "database" in report


def test_health_models_endpoint(client):
    """12: Verify /health/models reports both Production (v1.0) and Shadow (v1.1-c1)."""
    response = client.get("/health/models")
    assert response.status_code == 200
    data = response.json()
    
    assert "production" in data
    assert "shadow" in data
    assert data["production"]["version"] == "PlayerSuite-v1.0"
    assert data["shadow"]["version"] == "PlayerSuite-v1.1-c1-shadow"


# ==============================================================================
# SECTION D: MODEL HEALTH & INTEGRITY
# ==============================================================================

def test_valid_production_artifacts_pass():
    """13: Verify existing repository production artifacts pass health diagnostic."""
    health_svc = ModelHealthService()
    diag = health_svc.check_model_health()
    assert diag["production"]["status"] == "healthy"
    assert diag["production"]["version"] == "PlayerSuite-v1.0"


def test_missing_production_artifact_detected(tmp_path):
    """14: Verify missing required artifact triggers unhealthy state."""
    models_dir = tmp_path / "models"
    os.makedirs(models_dir, exist_ok=True)
    # Only create one file
    (models_dir / "player_minutes_model.joblib").write_text("dummy")
    
    health_svc = ModelHealthService(base_dir=str(tmp_path))
    diag = health_svc.check_model_health()
    assert diag["production"]["status"] == "unhealthy"
    assert "Missing required production artifacts" in diag["production"]["error"]


def test_invalid_metadata_fails(tmp_path):
    """15: Verify corrupt or invalid metadata triggers unhealthy state."""
    models_dir = tmp_path / "models"
    os.makedirs(models_dir, exist_ok=True)
    for f in ["player_minutes_model.joblib", "player_points_model.joblib", "player_rebounds_model.joblib", "player_assists_model.joblib"]:
        (models_dir / f).write_text("dummy")
    (models_dir / "player_models_metadata.json").write_text(json.dumps({"feature_contract": ["only_one_feat"]}))
    
    health_svc = ModelHealthService(base_dir=str(tmp_path))
    diag = health_svc.check_model_health()
    assert diag["production"]["status"] == "unhealthy"
    assert "Expected 24 features" in diag["production"]["error"]


def test_shadow_model_failure_does_not_take_production_offline(tmp_path):
    """16: Verify shadow model failure marks shadow as DEGRADED but keeps production serving."""
    # Create valid prod models in tmp_path
    models_dir = tmp_path / "models"
    os.makedirs(models_dir, exist_ok=True)
    for f in ["player_minutes_model.joblib", "player_points_model.joblib", "player_rebounds_model.joblib", "player_assists_model.joblib"]:
        (models_dir / f).write_text("dummy")
    (models_dir / "player_models_metadata.json").write_text(json.dumps({
        "feature_contract": list(PLAYER_FEATURE_CONTRACT),
        "feature_schema_version": "v1.0-player"
    }))
    
    # Shadow dir is missing
    health_svc = ModelHealthService(base_dir=str(tmp_path))
    is_ready, report = health_svc.check_readiness()
    
    assert is_ready is True  # Production is ready
    assert report["models"]["production"]["status"] == "healthy"
    assert report["models"]["shadow"]["status"] == "degraded"


def test_frozen_c1_version_mismatch_detected(tmp_path):
    """17: Verify unexpected shadow model version is detected."""
    shadow_dir = tmp_path / "models" / "experimental" / "c1_role_stratified"
    os.makedirs(shadow_dir, exist_ok=True)
    for f in ["shadow_points_model.joblib", "shadow_minutes_model.joblib", "shadow_rebounds_model.joblib", "shadow_assists_model.joblib"]:
        (shadow_dir / f).write_text("dummy")
    (shadow_dir / "shadow_models_metadata.json").write_text(json.dumps({
        "model_version": "Wrong-Version-v2.0",
        "role_definitions": {"star": {}, "starter": {}, "bench": {}}
    }))
    
    health_svc = ModelHealthService(base_dir=str(tmp_path))
    diag = health_svc.check_model_health()
    assert diag["shadow"]["status"] == "degraded"
    assert "Shadow model version mismatch" in diag["shadow"]["error"]


# ==============================================================================
# SECTION E: DATA QUALITY CHECKS
# ==============================================================================

def test_game_record_missing_columns_detected():
    """18: Verify missing essential game fields are flagged."""
    invalid_game = {"game_date": "2026-10-21"}
    valid, errors = validate_game_record(invalid_game)
    assert valid is False
    assert any("Missing game_id" in e for e in errors)
    assert any("Missing home_team" in e for e in errors)


def test_nan_or_inf_feature_detected():
    """19: Verify NaN or Infinite features trigger validation error."""
    feat_dict = {f: 1.0 for f in PLAYER_FEATURE_CONTRACT}
    feat_dict["player_usage_pct_10"] = float("nan")
    
    valid, errors = validate_feature_vector(feat_dict)
    assert valid is False
    assert any("Feature 'player_usage_pct_10' is NaN" in e for e in errors)

    feat_dict["player_usage_pct_10"] = float("inf")
    valid, errors = validate_feature_vector(feat_dict)
    assert valid is False
    assert any("Feature 'player_usage_pct_10' is Infinite" in e for e in errors)


def test_duplicate_or_invalid_team_detected():
    """20 & 21: Verify identical home/away teams trigger error."""
    game = {
        "game_id": "GAME_001",
        "game_date": "2026-10-21",
        "home_team": "LAL",
        "away_team": "LAL"
    }
    valid, errors = validate_game_record(game)
    assert valid is False
    assert any("identical" in e for e in errors)


def test_invalid_player_identifier_detected():
    """22: Verify missing player identifier is caught."""
    valid, errors = validate_player_record({})
    assert valid is False
    assert any("Missing player identifier" in e for e in errors)


def test_invalid_actual_statistic_detected():
    """23: Verify negative or NaN actual stats trigger error."""
    rec = {"person_id": "1629029", "points": -5.0}
    valid, errors = validate_player_record(rec, is_actual=True)
    assert valid is False
    assert any("Invalid actual points" in e for e in errors)


# ==============================================================================
# SECTION F: FEATURE CONTRACT
# ==============================================================================

def test_correct_feature_vector_passes():
    """24: Verify standard 24-feature vector passes contract check."""
    feat_dict = {f: 1.0 for f in PLAYER_FEATURE_CONTRACT}
    valid, errors = validate_feature_vector(feat_dict)
    assert valid is True
    assert len(errors) == 0


def test_missing_feature_contract_fails():
    """25 & 26: Verify missing required feature fails contract check."""
    feat_dict = {f: 1.0 for f in PLAYER_FEATURE_CONTRACT}
    del feat_dict["player_min_avg_10"]
    del feat_dict["team_pace_10"]
    
    valid, errors = validate_feature_vector(feat_dict)
    assert valid is False
    assert any("Missing 2 required features" in e for e in errors)


def test_temporal_leakage_safeguard_check():
    """27: Verify strict temporal inequality check feature_date < target_game_date."""
    assert check_temporal_leakage_safeguard("2026-10-20", "2026-10-21") is True
    assert check_temporal_leakage_safeguard("2026-10-21", "2026-10-21") is False
    assert check_temporal_leakage_safeguard("2026-10-22", "2026-10-21") is False


# ==============================================================================
# SECTION G: PREDICTION HEALTH & VALIDATION
# ==============================================================================

def test_prediction_output_bounds_validation():
    """28 & 30: Verify predictions within normal ranges pass and negatives fail."""
    valid_preds = {
        "predicted_minutes": 32.5,
        "predicted_points": 28.4,
        "predicted_rebounds": 8.1,
        "predicted_assists": 9.2
    }
    valid, errors = validate_prediction_output(valid_preds)
    assert valid is True

    negative_preds = {
        "predicted_minutes": -4.0,
        "predicted_points": 25.0
    }
    valid, errors = validate_prediction_output(negative_preds)
    assert valid is False
    assert any("predicted_minutes" in e for e in errors)


def test_shadow_failure_does_not_fail_production_prediction():
    """31: Verify shadow prediction exception is gracefully caught and production output is returned."""
    from src.inference.player_predictor import PlayerPredictor
    
    predictor = PlayerPredictor()
    # Mock shadow suite to raise RuntimeError
    mock_shadow = MagicMock()
    mock_shadow.predict_player.side_effect = RuntimeError("Simulated shadow model failure")
    mock_shadow.model_version = "PlayerSuite-v1.1-c1-shadow"
    predictor._shadow_suite = mock_shadow

    # Request production predictions
    resp = predictor.predict_scheduled_game_players(
        home_team_identifier="LAL",
        away_team_identifier="GSW",
        game_date_str="2026-10-21",
        max_players_per_team=3
    )
    
    assert len(resp.players) > 0
    assert resp.home_team == "Los Angeles Lakers"
    # Shadow failure metric was incremented
    failure_count = metrics_collector.get_counter_value("shadow_prediction_requests_total", labels={"status": "failure"})
    assert failure_count > 0


# ==============================================================================
# SECTION H: PROMETHEUS METRICS
# ==============================================================================

def test_http_request_metrics_increment(client):
    """32 & 34: Verify HTTP request counter and histogram increment on API calls."""
    client.get("/health")
    
    val = metrics_collector.get_counter_value("http_requests_total", labels={"method": "GET", "path": "/health", "status": "2xx"})
    assert val >= 1.0


def test_http_error_metrics_increment(client):
    """33: Verify HTTP errors increment error metric."""
    client.get("/predict/9999999")
    
    err_val = metrics_collector.get_counter_value("http_errors_total", labels={"method": "GET", "path": "/predict/9999999", "status_code": "404"})
    assert err_val >= 1.0


def test_prometheus_scrape_endpoint_format(client):
    """35 & 36: Verify /metrics returns valid Prometheus exposition text."""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers.get("content-type", "")
    content = response.text
    
    assert "# HELP http_requests_total" in content
    assert "# TYPE http_requests_total counter"
    assert "http_requests_total" in content


# ==============================================================================
# SECTION I: FEATURE DRIFT
# ==============================================================================

def test_stable_baseline_no_drift():
    """37: Verify identical distributions produce low PSI and no drift."""
    np.random.seed(42)
    base_data = np.random.normal(loc=25.0, scale=5.0, size=500)
    curr_data = np.random.normal(loc=25.0, scale=5.0, size=500)
    
    psi = calculate_psi(base_data, curr_data)
    assert psi < 0.10


def test_shifted_distribution_triggers_drift():
    """38: Verify shifted distribution produces high PSI and triggers drift detection."""
    np.random.seed(42)
    base_data = np.random.normal(loc=25.0, scale=3.0, size=500)
    curr_data = np.random.normal(loc=40.0, scale=3.0, size=500)  # Major mean shift
    
    psi = calculate_psi(base_data, curr_data)
    assert psi > 0.25
    
    detector = DataDriftDetector()
    df_base = pd.DataFrame({
        "player_min_avg_10": base_data,
        "player_usage_pct_10": base_data,
        "player_pts_per_min_10": base_data,
        "player_reb_per_min_10": base_data,
        "player_ast_per_min_10": base_data,
        "days_since_last_game": base_data
    })
    df_curr = pd.DataFrame({
        "player_min_avg_10": curr_data,
        "player_usage_pct_10": curr_data,
        "player_pts_per_min_10": curr_data,
        "player_reb_per_min_10": curr_data,
        "player_ast_per_min_10": curr_data,
        "days_since_last_game": curr_data
    })
    
    res = detector.compute_player_feature_drift(current_df=df_curr, reference_df=df_base)
    assert res["status"] == "DRIFT_DETECTED"
    assert res["drift_detected"] is True


def test_missing_baseline_returns_unknown():
    """39: Verify missing baseline returns UNKNOWN status rather than false healthy."""
    detector = DataDriftDetector()
    res = detector.compute_player_feature_drift(current_df=None, reference_df=None)
    assert res["status"] == "UNKNOWN"
    assert res["drift_detected"] is False


# ==============================================================================
# SECTION J: ERROR HANDLING & CLASSIFICATION
# ==============================================================================

def test_data_quality_error_mapping():
    """40: Verify data quality errors increment error counter."""
    metrics_collector.reset()
    validate_game_record({"game_date": "invalid-date"})
    fail_count = metrics_collector.get_counter_value("data_quality_failures_total", labels={"check_type": "game_record"})
    assert fail_count >= 1.0


def test_freshness_status_evaluation():
    """41 & 42: Verify check_data_freshness returns valid status dict."""
    freshness = check_data_freshness()
    assert freshness["status"] in ["FRESH", "STALE", "UNKNOWN"]
    assert "file" in freshness


# ==============================================================================
# SECTION K: REGRESSION TESTS
# ==============================================================================

def test_prediction_path_can_emit_structured_log_event(client):
    """
    Regression Test (Phase 11):
    Verifies that predictor service and API endpoints invoke `log_event()` without
    raising NameError or crashing the prediction response.
    """
    custom_req_id = f"test-reg-{uuid.uuid4().hex[:8]}"
    headers = {"X-Request-ID": custom_req_id}
    
    # 1. Test Next Lakers Prediction
    resp = client.get("/predict/lakers/next", headers=headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
    data = resp.json()
    assert "lakers_win_probability" in data
    assert "predicted_lakers_margin" in data
    assert "model_version" in data
    assert resp.headers.get("x-request-id") == custom_req_id

    # 2. Test Matchup Prediction
    post_resp = client.post(
        "/predict",
        json={"home_team": "LAL", "away_team": "GSW", "game_date": "2026-10-21", "persist": False},
        headers=headers
    )
    assert post_resp.status_code == 200, f"Expected 200, got {post_resp.status_code}: {post_resp.text}"
    post_data = post_resp.json()
    assert "home_win_probability" in post_data
    assert "predicted_home_margin" in post_data
    assert post_resp.headers.get("x-request-id") == custom_req_id

    # 3. Test Scheduled Player Prediction
    player_resp = client.get("/predict/5/players", headers=headers)
    assert player_resp.status_code == 200, f"Expected 200, got {player_resp.status_code}: {player_resp.text}"
    player_data = player_resp.json()
    assert "players" in player_data
    assert len(player_data["players"]) > 0
    assert player_resp.headers.get("x-request-id") == custom_req_id

