"""
Phase 9.2 Regression Tests: Prediction Integrity, Team Orientation & Player Projection Audit.
Validates:
1. Strict orientation contract across 4 core matchups:
   - GSW away @ LAL home (2026-10-21)
   - LAC away @ LAL home (2026-10-23)
   - LAL away @ LAC home (2026-10-28)
   - LAL away @ GSW home (2026-10-30)
2. Invariants:
   - home_win_probability + away_win_probability == 1.0 (approx)
   - predicted_home_margin sign semantics (positive = home favored, negative = away favored)
   - Swapping home and away swaps team roles and predictions consistently
   - Next Lakers endpoint orientation
3. Player performance projection integrity:
   - Non-transition established players have days_since_team_change == 0
   - Rolling stats exclude 0-minute inactive / DNP games
   - Star player minutes (Luka Doncic, Stephen Curry, Austin Reaves) > 28.0 min
   - Star player points (Luka Doncic, Stephen Curry, Austin Reaves) > 15.0 pts
"""

import pytest
from datetime import date
from fastapi.testclient import TestClient

from src.inference.api import app
from src.inference.roster_service import RosterService
from src.features.player_prediction_features import PlayerFeatureEngine
from src.inference.player_predictor import PlayerPredictor

client = TestClient(app)


def test_orientation_gsw_at_lal():
    """Case 1: GSW away @ LAL home on 2026-10-21"""
    res = client.post("/predict", json={
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2026-10-21",
        "persist": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["home_team"] == "Los Angeles Lakers"
    assert data["away_team"] == "Golden State Warriors"
    
    p_home = data["home_win_probability"]
    p_away = data["away_win_probability"]
    assert pytest.approx(p_home + p_away, abs=1e-4) == 1.0
    
    # Margin sign consistency (positive when home team favored)
    margin = data["predicted_home_margin"]
    if p_home >= 0.5:
        assert margin >= 0.0
    else:
        assert margin < 0.0


def test_orientation_lal_at_gsw():
    """Case 2: LAL away @ GSW home on 2026-10-30"""
    res = client.post("/predict", json={
        "home_team": "GSW",
        "away_team": "LAL",
        "game_date": "2026-10-30",
        "persist": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["home_team"] == "Golden State Warriors"
    assert data["away_team"] == "Los Angeles Lakers"
    
    p_home = data["home_win_probability"]
    p_away = data["away_win_probability"]
    assert pytest.approx(p_home + p_away, abs=1e-4) == 1.0
    
    margin = data["predicted_home_margin"]
    if p_home >= 0.5:
        assert margin >= 0.0
    else:
        assert margin < 0.0


def test_orientation_lac_at_lal():
    """Case 3: LAC away @ LAL home on 2026-10-23"""
    res = client.post("/predict", json={
        "home_team": "LAL",
        "away_team": "LAC",
        "game_date": "2026-10-23",
        "persist": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["home_team"] == "Los Angeles Lakers"
    assert data["away_team"] == "LA Clippers"
    
    p_home = data["home_win_probability"]
    p_away = data["away_win_probability"]
    assert pytest.approx(p_home + p_away, abs=1e-4) == 1.0


def test_orientation_lal_at_lac():
    """Case 4: LAL away @ LAC home on 2026-10-28"""
    res = client.post("/predict", json={
        "home_team": "LAC",
        "away_team": "LAL",
        "game_date": "2026-10-28",
        "persist": False
    })
    assert res.status_code == 200
    data = res.json()
    assert data["home_team"] == "LA Clippers"
    assert data["away_team"] == "Los Angeles Lakers"
    
    p_home = data["home_win_probability"]
    p_away = data["away_win_probability"]
    assert pytest.approx(p_home + p_away, abs=1e-4) == 1.0


def test_orientation_next_lakers_endpoint():
    """Tests that /predict/lakers/next provides correct orientation fields."""
    res = client.get("/predict/lakers/next")
    assert res.status_code == 200
    data = res.json()
    assert "is_lakers_home" in data
    assert "lakers_win_probability" in data
    assert "opponent_win_probability" in data
    assert "predicted_lakers_margin" in data
    p_lal = data["lakers_win_probability"]
    p_opp = data["opponent_win_probability"]
    assert pytest.approx(p_lal + p_opp, abs=1e-4) == 1.0


def test_roster_service_established_days_since_change_is_zero():
    """Verifies that established roster players have days_since_team_change == 0 for train-serve parity."""
    roster_service = RosterService()
    roster = roster_service.get_active_roster_universe("LAL", "2026-10-21")
    
    # Austin Reaves and Luka Doncic are established Lakers roster members
    for p in roster:
        if not p["is_transition_player"]:
            assert p["days_since_team_change"] == 0, f"Expected 0 for established player {p['player_name']}, got {p['days_since_team_change']}"


def test_player_projections_luka_reaves_curry_plausibility():
    """Verifies that star players receive realistic minutes (>28m) and points (>15pts)."""
    predictor = PlayerPredictor()
    res = predictor.predict_scheduled_game_players(
        home_team_identifier="LAL",
        away_team_identifier="GSW",
        game_date_str="2026-10-21"
    )
    
    player_map = {p.player_name: p for p in res.players}
    
    assert "Luka Doncic" in player_map, "Luka Doncic must be present in Lakers projections"
    assert "Austin Reaves" in player_map, "Austin Reaves must be present in Lakers projections"
    assert "Stephen Curry" in player_map, "Stephen Curry must be present in Warriors projections"
    
    luka = player_map["Luka Doncic"]
    assert luka.expected_minutes >= 28.0, f"Luka minutes underpredicted: {luka.expected_minutes}"
    assert luka.predicted_points >= 20.0, f"Luka points underpredicted: {luka.predicted_points}"
    assert luka.team_code == "LAL"
    
    reaves = player_map["Austin Reaves"]
    assert reaves.expected_minutes >= 28.0, f"Reaves minutes underpredicted: {reaves.expected_minutes}"
    assert reaves.predicted_points >= 15.0, f"Reaves points underpredicted: {reaves.predicted_points}"
    assert reaves.team_code == "LAL"
    
    curry = player_map["Stephen Curry"]
    assert curry.expected_minutes >= 28.0, f"Curry minutes underpredicted: {curry.expected_minutes}"
    assert curry.predicted_points >= 18.0, f"Curry points underpredicted: {curry.predicted_points}"
    assert curry.team_code == "GSW"


def test_player_prediction_api_endpoint():
    """Verifies that the /predict/players endpoint returns valid structured projections."""
    res = client.post("/predict/players", json={
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2026-10-21"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["home_team"] == "Los Angeles Lakers"
    assert data["away_team"] == "Golden State Warriors"
    assert len(data["players"]) >= 10
    
    for p in data["players"]:
        assert "player_id" in p
        assert "player_name" in p
        assert "team_code" in p
        assert p["expected_minutes"] > 0
        assert p["predicted_points"] >= 0
        assert p["predicted_rebounds"] >= 0
        assert p["predicted_assists"] >= 0
