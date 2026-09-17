"""
Regression and Contract Tests for Matchup Predictor Endpoint and Workflow.
Validates:
- Valid official scheduled matchup prediction (200 OK)
- Schedule-backed date enforcement: unscheduled team/date combinations return 400
- Valid teams with wrong date returns 400 with descriptive error
- Team uniqueness validation (home != away returns 400)
- Team code/alias validation (unknown team returns 400)
- Date format validation (malformed date returns 422)
- Query endpoint for matchup schedule (/schedule/matchup)
- Canonicalization parity across schedule and prediction
- Response schema completeness (home/away win probabilities sum to 1.0, margins, aliases)
- Persistence toggle behavior (persist=False vs persist=True)
"""

import os
import pytest
from datetime import date
from fastapi.testclient import TestClient

from src.inference.api import app
from src.inference.schedule_service import normalize_team

client = TestClient(app)


def test_valid_matchup_prediction_lal_gsw():
    """Verifies that a real scheduled matchup (LAL vs GSW on 2026-10-21) returns 200 and calibrated predictions."""
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
    
    # Margin alias parity for frontend consumption
    assert data["predicted_margin"] == data["predicted_home_margin"]
    assert "feature_snapshot_hash" in data
    assert "model_version" in data


def test_valid_matchup_prediction_bos_nyk():
    """Verifies that another real scheduled matchup (BOS vs NYK on 2026-10-23) returns 200."""
    payload = {
        "home_team": "BOS",
        "away_team": "NYK",
        "game_date": "2026-10-23",
        "persist": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["home_team"] == "Boston Celtics"
    assert data["away_team"] == "New York Knicks"
    assert data["game_date"] == "2026-10-23"
    assert pytest.approx(data["home_win_probability"] + data["away_win_probability"], abs=1e-5) == 1.0


def test_unscheduled_matchup_date_rejected():
    """Verifies that a valid team pair on an unscheduled date returns HTTP 400 with a clear error."""
    payload = {
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2026-12-31",
        "persist": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "No scheduled 2026-27 game exists for LAL vs GSW on 2026-12-31." in detail


def test_arbitrary_in_season_date_rejected_for_teams():
    """Verifies that BOS vs NYK on 2026-11-05 (an unscheduled date for this pair) returns HTTP 400."""
    payload = {
        "home_team": "BOS",
        "away_team": "NYK",
        "game_date": "2026-11-05",
        "persist": False
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "No scheduled 2026-27 game exists for BOS vs NYK on 2026-11-05." in detail


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
    """Verifies that dates outside the season return HTTP 400."""
    payload_past = {
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2025-05-15",
        "persist": False
    }
    res_past = client.post("/predict", json=payload_past)
    assert res_past.status_code == 400
    assert "no scheduled 2026-27 game exists" in res_past.json()["detail"].lower()


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
    # 1. Transient (persist=False) - using official scheduled BOS vs NYK on 2026-10-23
    payload_transient = {
        "home_team": "BOS",
        "away_team": "NYK",
        "game_date": "2026-10-23",
        "persist": False
    }
    res_transient = client.post("/predict", json=payload_transient)
    assert res_transient.status_code == 200
    assert res_transient.json()["prediction_id"] is None

    # 2. Persisted (persist=True)
    payload_persisted = {
        "home_team": "BOS",
        "away_team": "NYK",
        "game_date": "2026-10-23",
        "persist": True
    }
    res_persisted = client.post("/predict", json=payload_persisted)
    assert res_persisted.status_code == 200
    assert res_persisted.json()["prediction_id"] is not None


def test_get_matchup_schedule_endpoint():
    """Verifies that /schedule/matchup returns official scheduled games for any team pair."""
    response = client.get("/schedule/matchup?home_team=LAL&away_team=GSW")
    assert response.status_code == 200
    games = response.json()
    assert len(games) == 2  # 2 home games for LAL vs GSW
    dates = [g["game_date"] for g in games]
    assert "2026-10-21" in dates
    assert "2027-03-14" in dates
    for g in games:
        assert g["home_team_code"] == "LAL"
        assert g["away_team_code"] == "GSW"


def test_schedule_lookup_and_prediction_canonicalization_parity():
    """Verifies that team aliases (e.g. 'celtics', 'Warriors') resolve to identical canonical team records."""
    # Boston Celtics vs New York Knicks using aliases
    sched_resp = client.get("/schedule/matchup?home_team=celtics&away_team=knicks")
    assert sched_resp.status_code == 200
    games = sched_resp.json()
    assert len(games) >= 1
    
    first_game = games[0]
    pred_resp = client.post("/predict", json={
        "home_team": "celtics",
        "away_team": "knicks",
        "game_date": first_game["game_date"]
    })
    assert pred_resp.status_code == 200
    data = pred_resp.json()
    assert data["home_team"] == "Boston Celtics"
    assert data["away_team"] == "New York Knicks"
    assert data["game_id"] == str(first_game["game_num"])

