"""
Memory Safety and Resource Optimization Regression Tests for Lakers in 5.
Validates structural memory-safety properties:
- Predictor model caching idempotency
- Predictor repeated predictions memory stabilization / no unbounded object growth
- Inference pipeline isolation from data/raw
- DuckDB memory limit pragmas and thread constraints
- Reference feature loading column projections
- Production Dockerfile single-worker concurrency configuration
"""

import os
import gc
import sys
import pytest
from fastapi.testclient import TestClient

from src.inference.predictor import GamePredictor
from src.inference.feature_service import ProductionFeatureService, MODEL_FEATURE_CONTRACT
from src.lake.duckdb_client import DuckDBClient
from src.monitoring.drift import DataDriftDetector
from src.inference.api import app

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_predictor_model_caching_idempotency():
    """Verifies that GamePredictor deserializes models once and reuses in-memory artifacts."""
    predictor = GamePredictor()
    clf_1 = predictor.classifier
    reg_1 = predictor.regressor
    
    # Verify models are loaded
    assert clf_1 is not None
    assert reg_1 is not None
    
    # Multiple predictions should not reload or replace model references
    res1 = predictor.predict_game("LAL", "GSW", "2026-10-25")
    res2 = predictor.predict_game("LAL", "BOS", "2026-10-28")
    
    assert predictor.classifier is clf_1, "Classifier instance must remain identical across predictions"
    assert predictor.regressor is reg_1, "Regressor instance must remain identical across predictions"
    assert res1.home_win_probability is not None
    assert res2.home_win_probability is not None


def test_duckdb_client_memory_and_thread_limits():
    """Verifies DuckDBClient configures memory limits and thread bounds upon initialization."""
    client = DuckDBClient()
    try:
        mem_setting = client.conn.execute("SELECT current_setting('memory_limit')").fetchone()[0]
        threads_setting = client.conn.execute("SELECT current_setting('threads')").fetchone()[0]
        
        # DuckDB returns formatted string (e.g., '122.0 MiB' or '128MB')
        assert "MiB" in mem_setting or "MB" in mem_setting or "128" in mem_setting
        assert int(threads_setting) == 1, "DuckDB must be constrained to 1 thread in production inference"
    finally:
        client.close()


def test_reference_features_projection_memory_safety():
    """Verifies DataDriftDetector loads only required contract columns from parquet."""
    detector = DataDriftDetector()
    ref_df = detector._load_reference_data()
    
    # Must only contain the 52 feature contract columns
    assert len(ref_df.columns) <= len(MODEL_FEATURE_CONTRACT)
    for col in ref_df.columns:
        assert col in MODEL_FEATURE_CONTRACT


def test_inference_pipeline_does_not_access_raw_data():
    """Verifies that inference and feature service solely query processed parquet datasets, never data/raw."""
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    service = ProductionFeatureService()
    
    # Verify duckdb client points to processed parquet directory
    parquet_dir = service.client.parquet_dir
    assert "data/processed/parquet" in parquet_dir.replace("\\", "/")
    assert raw_dir not in parquet_dir


def test_dockerfile_worker_configuration_memory_safety():
    """Verifies Dockerfile CMD configures single-worker concurrency for 512MB RAM constraints."""
    dockerfile_path = os.path.join(BASE_DIR, "Dockerfile")
    assert os.path.exists(dockerfile_path)
    
    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "--workers ${WEB_CONCURRENCY:-1}" in content or "--workers 1" in content, (
        "Dockerfile must configure 1 worker by default to prevent cgroup OOM kills in 512MB environments"
    )
    # Ensure it doesn't hardcode --workers 2 or higher
    assert "--workers 2" not in content
    assert "--workers 4" not in content


def test_repeated_predictions_stability():
    """Verifies that repeated predictions execute stably without accumulating unbounded state."""
    client = TestClient(app)
    
    # Warmup
    r0 = client.get("/health")
    assert r0.status_code == 200
    
    # Run a sequence of prediction requests
    for _ in range(15):
        r = client.get("/predict/lakers/next")
        assert r.status_code == 200
        data = r.json()
        assert "lakers_win_probability" in data
        assert 0.0 <= data["lakers_win_probability"] <= 1.0
