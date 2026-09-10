"""
Containerization and Production Environment Reproducibility Tests for Lakers in 5.
Validates Dockerfile, .dockerignore, docker-compose.yml, runtime artifact integrity,
configuration safety, and entrypoint contracts.
"""

import os
import re
import pytest
import joblib
from fastapi.testclient import TestClient

from src.inference.api import app

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_dockerfile_structure():
    """Verifies Dockerfile exists, uses python:3.11-slim, non-root user, and correct production entrypoints."""
    dockerfile_path = os.path.join(BASE_DIR, "Dockerfile")
    assert os.path.exists(dockerfile_path), "Dockerfile must exist at project root"

    with open(dockerfile_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "python:3.11-slim" in content, "Must use python:3.11-slim base image"
    assert "WORKDIR /app" in content, "Must specify /app as working directory"
    assert "USER appuser" in content, "Must switch to non-root user 'appuser'"
    assert "EXPOSE 8000" in content, "Must expose port 8000"
    assert "HEALTHCHECK" in content, "Must declare container HEALTHCHECK"
    assert "src.inference.api:app" in content, "Must target FastAPI app as default ASGI entrypoint"
    assert "--workers" in content, "Must configure production workers"


def test_dockerignore_rules():
    """Verifies .dockerignore excludes secrets, virtual environments, raw data, but preserves runtime artifacts."""
    dockerignore_path = os.path.join(BASE_DIR, ".dockerignore")
    assert os.path.exists(dockerignore_path), ".dockerignore must exist at project root"

    with open(dockerignore_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must exclude
    assert ".venv" in content
    assert ".env" in content
    assert "data/raw/" in content
    assert "__pycache__" in content
    assert "*.duckdb" in content

    # Must not exclude runtime-required parquet directories
    assert "data/processed/" not in content
    assert "data/features/" not in content
    assert "models/" not in content


def test_docker_compose_configuration():
    """Verifies docker-compose.yml defines api and dashboard services with proper ports and environment pass-through."""
    compose_path = os.path.join(BASE_DIR, "docker-compose.yml")
    assert os.path.exists(compose_path), "docker-compose.yml must exist at project root"

    with open(compose_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "api:" in content, "Must define 'api' service"
    assert "dashboard:" in content, "Must define 'dashboard' service"
    assert "8000:8000" in content, "Must map API port 8000"
    assert "8501:8501" in content, "Must map Dashboard port 8501"
    assert "src/dashboard/app.py" in content, "Dashboard must target src/dashboard/app.py"
    assert "DATABASE_URL" in content, "Must pass DATABASE_URL environment variable"
    assert "postgres" not in content.lower() or "POSTGRES_" in content, "Must not define a local PostgreSQL database container"


def test_runtime_artifacts_presence_and_validity():
    """Verifies all model and analytical data artifacts required for container runtime exist and are valid."""
    # 1. Models
    clf_path = os.path.join(BASE_DIR, "models", "champion_classifier.joblib")
    reg_path = os.path.join(BASE_DIR, "models", "champion_regressor.joblib")
    assert os.path.exists(clf_path), f"Champion classifier missing at {clf_path}"
    assert os.path.exists(reg_path), f"Champion regressor missing at {reg_path}"

    clf_obj = joblib.load(clf_path)
    reg_obj = joblib.load(reg_path)
    assert "model" in clf_obj and "model_label" in clf_obj
    assert "model" in reg_obj and "model_label" in reg_obj

    # 2. Processed Parquet lakehouse tables
    required_parquets = [
        "games.parquet",
        "team_game_stats.parquet",
        "team_game_stats_extended.parquet",
        "player_game_stats.parquet",
        "player_game_stats_extended.parquet",
        "schedule_2026_27.parquet"
    ]
    for p in required_parquets:
        parquet_path = os.path.join(BASE_DIR, "data", "processed", "parquet", p)
        assert os.path.exists(parquet_path), f"Required runtime parquet missing: {p}"
        assert os.path.getsize(parquet_path) > 0, f"Runtime parquet is empty: {p}"

    # 3. Features Parquet reference
    features_path = os.path.join(BASE_DIR, "data", "features", "game_features.parquet")
    assert os.path.exists(features_path), "Reference game_features.parquet missing"
    assert os.path.getsize(features_path) > 0


def test_no_hardcoded_secrets_in_deployment_configs():
    """Verifies no raw passwords, secrets, or API keys are committed in Dockerfile or docker-compose.yml."""
    configs_to_check = ["Dockerfile", "docker-compose.yml", ".dockerignore", "requirements.txt"]
    secret_patterns = [
        r"(?i)password\s*=\s*['\"][^'\"]{3,}['\"]",
        r"(?i)neon\.tech",
        r"(?i)postgres://[^:]+:[^@]+@",
        r"(?i)postgresql://[^:]+:[^@]+@"
    ]

    for filename in configs_to_check:
        filepath = os.path.join(BASE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            for pattern in secret_patterns:
                matches = re.findall(pattern, content)
                assert len(matches) == 0, f"Potential secret matched in {filename}: {matches}"


def test_api_entrypoint_and_health_contract():
    """Tests that the containerized API entrypoint boots cleanly and responds to /health."""
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "classifier" in data
    assert "regressor" in data
    assert "model_version" in data
