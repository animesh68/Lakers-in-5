"""
Comprehensive Functional & API Tests for Phase 8 Player Performance Prediction.
Tests endpoint contracts, scheduled-game validation, schema conformity, transition player handling,
and multi-player projection generation.
"""

import pytest
from fastapi.testclient import TestClient
from src.inference.api import app
from src.inference.player_predictor import PlayerPredictor
from src.inference.roster_service import RosterService


@pytest.fixture
def client():
    return TestClient(app)


def test_predict_players_endpoint_valid_scheduled_game(client):
    """
    Tests POST /predict/players on an official scheduled 2026-27 matchup (Lakers vs Warriors on 2026-10-21).
    """
    payload = {
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2026-10-21"
    }
    response = client.post("/predict/players", json=payload)
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "game_id" in data
    assert data["game_date"] == "2026-10-21"
    assert data["home_team"] == "Los Angeles Lakers"
    assert data["away_team"] == "Golden State Warriors"
    assert len(data["players"]) >= 10
    
    # Verify player structure
    for p in data["players"]:
        assert "player_id" in p
        assert "player_name" in p
        assert "team" in p
        assert "expected_minutes" in p
        assert "predicted_points" in p
        assert "predicted_rebounds" in p
        assert "predicted_assists" in p
        assert 0.0 <= p["expected_minutes"] <= 48.0
        assert 0.0 <= p["predicted_points"] <= 70.0
        assert 0.0 <= p["predicted_rebounds"] <= 35.0
        assert 0.0 <= p["predicted_assists"] <= 30.0
        assert isinstance(p["is_transition_player"], bool)

    # Verify model versions manifest
    assert "minutes" in data["model_versions"]
    assert "points" in data["model_versions"]
    assert "rebounds" in data["model_versions"]
    assert "assists" in data["model_versions"]
    assert data["feature_schema_version"] == "v1.0-player"


def test_predict_players_by_game_num_endpoint(client):
    """
    Tests GET /predict/{game_id}/players on official schedule game #5.
    """
    response = client.get("/predict/5/players")
    assert response.status_code == 200
    data = response.json()
    assert data["game_date"] == "2026-10-21"
    assert len(data["players"]) >= 10


def test_predict_players_unscheduled_matchup_rejected(client):
    """
    Ensures that predicting players for an arbitrary/unscheduled date is rejected with HTTP 400.
    """
    payload = {
        "home_team": "TOR",
        "away_team": "LAC",
        "game_date": "2026-10-21" # Not scheduled to play on this date
    }
    response = client.post("/predict/players", json=payload)
    assert response.status_code == 400
    assert "No official 2026-27 regular season game scheduled" in response.json()["detail"]


def test_predict_players_identical_teams_rejected(client):
    """
    Ensures that identical home and away teams are rejected with HTTP 400.
    """
    payload = {
        "home_team": "LAL",
        "away_team": "LAL",
        "game_date": "2026-10-21"
    }
    response = client.post("/predict/players", json=payload)
    assert response.status_code == 400
    assert "distinct" in response.json()["detail"].lower()


def test_transition_player_kawhi_leonard_on_raptors():
    """
    Validates roster awareness: Kawhi Leonard is assigned to Toronto Raptors for the 2026-27 season
    with is_transition_player=True and 0 games with current team prior to season opener.
    """
    roster_svc = RosterService()
    active_raptors = roster_svc.get_active_roster_universe("TOR", "2026-10-21")
    raptor_names = [p["player_name"] for p in active_raptors]
    
    assert "Kawhi Leonard" in raptor_names
    kawhi = next(p for p in active_raptors if p["player_name"] == "Kawhi Leonard")
    assert kawhi["is_transition_player"] is True
    assert kawhi["games_with_current_team"] == 0
    assert kawhi["team_code"] == "TOR"
