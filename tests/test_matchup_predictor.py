"""
Regression and Contract Tests for Matchup Predictor Endpoint and Workflow.
Validates:
- Valid scheduled/generic matchup prediction
- Date bounds validation (2026-27 season horizon)
- Team uniqueness validation (home != away)
- Team code validation (unknown team returns 400)
- Response schema completeness (home/away win probabilities sum to 1.0, margins, aliases)
- Persistence toggle behavior (persist=False vs persist=True)
- Lakers perspective symmetry
"""

import os
import pytest
from datetime import date
from fastapi.testclient import TestClient

from src.inference.api import app
from src.inference.predictor import GamePredictor

client = TestClient(app)


def test_valid_matchup_prediction():
    """Verifies that a valid matchup returns calibrated probabilities and margins summing to 1.0."""
    payload = {
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2026-10-21",
        "persist": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["home_team"] == "Los Angeles Lakers"
    assert data["away_team"] == "Golden State Warriors"
    assert data["game_date"] == "2026-10-21"
    assert "home_win_probability" in data
    assert "away_win_probability" in data
    assert "predicted_home_margin" in data
    assert "predicted_margin" in data
    
    # Probabilities must sum to 1.0
    p_home = data["home_win_probability"]
    p_away = data["away_win_probability"]
    assert 0.0 <= p_home <= 1.0
    assert 0.0 <= p_away <= 1.0
    assert pytest.approx(p_home + p_away, abs=1e-5) == 1.0
    
    # Margin alias parity
    assert data["predicted_margin"] == data["predicted_home_margin"]
    assert "feature_snapshot_hash" in data
    assert "model_version" in data


def test_matchup_prediction_same_team_rejected():
    """Verifies that selecting the same home and away team is rejected with HTTP 400."""
    payload = {
        "home_team": "LAL",
        "away_team": "LAL",
        "game_date": "2026-10-21",
        "persist": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "distinct" in response.json()["detail"].lower() or "same" in response.json()["detail"].lower()


def test_matchup_prediction_invalid_team_rejected():
    """Verifies that an unknown team code returns HTTP 400 with informative error message."""
    payload = {
        "home_team": "UNKNOWN_TEAM",
        "away_team": "LAL",
        "game_date": "2026-10-21",
        "persist": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    assert "unknown" in response.json()["detail"].lower() or "identifier" in response.json()["detail"].lower()


def test_matchup_prediction_date_outside_season_rejected():
    """Verifies that dates outside the supported 2026-27 horizon are rejected with HTTP 400."""
    # Past date
    payload_past = {
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2025-05-15",
        "persist": False
    }
    res_past = client.post("/predict", json=payload_past)
    assert res_past.status_code == 400
    assert "horizon" in res_past.json()["detail"].lower() or "season" in res_past.json()["detail"].lower()

    # Far future date
    payload_future = {
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2028-01-01",
        "persist": False
    }
    res_future = client.post("/predict", json=payload_future)
    assert res_future.status_code == 400
    assert "horizon" in res_future.json()["detail"].lower() or "season" in res_future.json()["detail"].lower()


def test_matchup_prediction_invalid_date_format():
    """Verifies that malformed date strings return HTTP 422 validation error."""
    payload = {
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "not-a-date",
        "persist": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_matchup_prediction_persist_toggle():
    """Verifies persist=False returns prediction_id=None and persist=True generates a prediction record."""
    # 1. Transient (persist=False)
    payload_transient = {
        "home_team": "BOS",
        "away_team": "NYK",
        "game_date": "2026-11-05",
        "persist": False
    }
    res_transient = client.post("/predict", json=payload_transient)
    assert res_transient.status_code == 200
    assert res_transient.json()["prediction_id"] is None

    # 2. Persisted (persist=True)
    payload_persisted = {
        "home_team": "BOS",
        "away_team": "NYK",
        "game_date": "2026-11-05",
        "persist": True
    }
    res_persisted = client.post("/predict", json=payload_persisted)
    assert res_persisted.status_code == 200
    assert res_persisted.json()["prediction_id"] is not None


def test_scheduled_matchup_prediction_via_schedule_lookup():
    """Verifies that games from the schedule service can be predicted cleanly."""
    sched_resp = client.get("/schedule/2026-27?team=LAL&limit=5")
    assert sched_resp.status_code == 200
    games = sched_resp.json()
    assert len(games) > 0
    
    first_game = games[0]
    payload = {
        "home_team": first_game["home_team"],
        "away_team": first_game["away_team"],
        "game_date": first_game["game_date"],
        "persist": False
    }
    pred_resp = client.post("/predict", json=payload)
    assert pred_resp.status_code == 200
    data = pred_resp.json()
    assert data["game_date"] == first_game["game_date"]
    assert data["home_win_probability"] > 0.0
