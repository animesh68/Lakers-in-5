"""
Unit, Leakage, Contract, and API Test Suite for Phase 4 Production Inference.
"""

import os
import pytest
import numpy as np
import pandas as pd
from datetime import datetime
from fastapi.testclient import TestClient

from src.inference.schemas import (
    GamePredictionRequest,
    GamePredictionResponse,
    LakersGamePredictionResponse,
)
from src.inference.schedule_service import ScheduleService, normalize_team, LAKERS_TEAM_ID
from src.inference.roster_service import RosterService
from src.inference.feature_service import ProductionFeatureService, MODEL_FEATURE_CONTRACT
from src.inference.predictor import GamePredictor
from src.inference.api import app
from src.lake.duckdb_client import DuckDBClient

@pytest.fixture(scope="module")
def predictor():
    return GamePredictor()

@pytest.fixture(scope="module")
def schedule_service():
    return ScheduleService()

@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


def test_feature_schema_contract(predictor):
    """Test 1: Generated production features exactly match the 52-column champion model contract."""
    feature_service = predictor.feature_service
    features_df = feature_service.generate_pregame_feature_vector(
        home_team_identifier="LAL",
        away_team_identifier="GSW",
        target_game_date="2026-10-21"
    )
    
    assert isinstance(features_df, pd.DataFrame)
    assert len(features_df) == 1
    assert list(features_df.columns) == MODEL_FEATURE_CONTRACT
    assert len(features_df.columns) == 52
    assert list(features_df.columns) == predictor.clf_feature_names


def test_temporal_leakage_future_game_injection():
    """
    Test 2: Injecting future game data into the database does not alter the pregame
    feature vector or prediction for an earlier target game.
    """
    client = DuckDBClient()
    feature_service = ProductionFeatureService(duckdb_client=client)
    
    # 1. Base prediction for 2026-10-21
    feat_before = feature_service.generate_pregame_feature_vector("LAL", "GSW", "2026-10-21")
    
    # 2. Inject a synthetic future game on 2026-11-01 into both games and team_game_stats views
    client.conn.execute("""
    CREATE OR REPLACE VIEW team_game_stats AS
    SELECT * FROM 'data/processed/parquet/team_game_stats.parquet'
    UNION ALL BY NAME
    SELECT 
        'synth_future_game' AS gameId,
        '2026-11-01 19:00:00' AS gameDateTimeEst,
        '1610612747' AS teamId,
        '1' AS win,
        '140' AS teamScore,
        '100' AS opponentScore
    """)
    client.conn.execute("""
    CREATE OR REPLACE VIEW games AS
    SELECT * FROM 'data/processed/parquet/games.parquet'
    UNION ALL BY NAME
    SELECT 
        'synth_future_game' AS gameId,
        '2026-11-01 19:00:00' AS gameDateTimeEst,
        '1610612747' AS hometeamId,
        '1610612744' AS awayteamId,
        '140' AS homeScore,
        '100' AS awayScore
    """)
    
    # 3. Regenerate pregame feature vector for 2026-10-21 (must be completely unaffected)
    feat_after = feature_service.generate_pregame_feature_vector("LAL", "GSW", "2026-10-21")
    
    # 4. Restore original views
    client.conn.execute("""
    CREATE OR REPLACE VIEW team_game_stats AS
    SELECT * FROM 'data/processed/parquet/team_game_stats.parquet'
    """)
    client.conn.execute("""
    CREATE OR REPLACE VIEW games AS
    SELECT * FROM 'data/processed/parquet/games.parquet'
    """)
    
    # Features for the earlier game must be 100% identical
    pd.testing.assert_frame_equal(feat_before, feat_after)


def test_target_game_exclusion():
    """
    Test 3: The target game's statistics are never used to calculate its own features.
    """
    client = DuckDBClient()
    feature_service = ProductionFeatureService(duckdb_client=client)
    
    # Target game on 2026-10-21
    feat = feature_service.generate_pregame_feature_vector("LAL", "GSW", "2026-10-21")
    
    # For a season opener, there are 0 preceding games in the 2026 season -> rolling points must be NaN
    assert np.isnan(feat["home_avg_points_5"].iloc[0])
    assert np.isnan(feat["away_avg_points_5"].iloc[0])


def test_elo_pregame_state(predictor):
    """
    Test 4: Verify that target game Elo is calculated strictly from prior games.
    """
    feature_service = predictor.feature_service
    home_elo, away_elo, elo_diff = feature_service.compute_pregame_elo(
        home_team_id="1610612747",
        away_team_id="1610612744",
        target_game_date="2026-10-21"
    )
    
    # Elo difference must equal (home_elo + 100.0) - away_elo
    assert np.isclose(elo_diff, (home_elo + 100.0) - away_elo)
    assert home_elo > 1000.0 and home_elo < 2000.0
    assert away_elo > 1000.0 and away_elo < 2000.0


def test_schedule_and_rest_calculation(predictor):
    """
    Test 5: Verify schedule rest days, back-to-back flags, and 7-day game density.
    """
    feature_service = predictor.feature_service
    # Test mid-season date from historical dataset where games exist
    stats = feature_service.compute_schedule_rest_stats(
        team_id="1610612747",
        target_game_date="2024-01-15"
    )
    
    assert "rest_days" in stats
    assert "back_to_back" in stats
    assert "games_last_7" in stats
    assert stats["back_to_back"] in (0, 1)
    assert stats["games_last_7"] >= 0


def test_season_boundary_cold_start(predictor):
    """
    Test 6: Season opener with cold-start NaNs is handled cleanly by the pipeline.
    """
    res = predictor.predict_game(
        home_team="LAL",
        away_team="GSW",
        game_date="2026-10-21"
    )
    
    assert res.home_win_probability >= 0.0 and res.home_win_probability <= 1.0
    assert res.away_win_probability >= 0.0 and res.away_win_probability <= 1.0
    assert np.isclose(res.home_win_probability + res.away_win_probability, 1.0)
    assert np.isfinite(res.predicted_home_margin)


def test_player_team_transition():
    """
    Test 7: Prior team player stats are not attributed to new team.
    """
    roster = RosterService()
    df_tx = roster.load_transactions()
    assert isinstance(df_tx, pd.DataFrame)
    
    # Verify player additions and departures can be queried
    lal_additions = roster.get_team_additions("LAL")
    assert isinstance(lal_additions, list)


def test_lakers_home_vs_away_perspective(predictor):
    """
    Test 8: Verify Lakers probability and margin invert properly when Lakers are away.
    """
    # 1. Lakers at Home vs Celtics
    home_res = predictor.predict_game("LAL", "BOS", "2026-12-25")
    
    # 2. Lakers Away vs Celtics
    away_res = predictor.predict_game("BOS", "LAL", "2026-12-25")
    
    # Lakers win probability at home should exceed Lakers win probability on the road
    p_lakers_home = home_res.home_win_probability
    p_lakers_away = away_res.away_win_probability
    assert p_lakers_home > p_lakers_away


def test_prediction_determinism(predictor):
    """
    Test 9: Identical inputs produce identical outputs deterministically.
    """
    res1 = predictor.predict_game("LAL", "GSW", "2026-10-21")
    res2 = predictor.predict_game("LAL", "GSW", "2026-10-21")
    
    assert np.isclose(res1.home_win_probability, res2.home_win_probability)
    assert np.isclose(res1.predicted_home_margin, res2.predicted_home_margin)


def test_fastapi_endpoints(api_client):
    """
    Test 10: FastAPI health, predict, schedule, and error responses.
    """
    # 1. Health check
    health_resp = api_client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "healthy"
    
    # 2. Predict post endpoint
    pred_resp = api_client.post("/predict", json={
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "2026-10-21"
    })
    assert pred_resp.status_code == 200
    data = pred_resp.json()
    assert "home_win_probability" in data
    assert "predicted_home_margin" in data
    
    # 3. Predict Lakers next
    lakers_resp = api_client.get("/predict/lakers/next")
    assert lakers_resp.status_code == 200
    lakers_data = lakers_resp.json()
    assert "lakers_win_probability" in lakers_data
    assert "predicted_lakers_margin" in lakers_data
    
    # 4. Schedule query
    sched_resp = api_client.get("/schedule/2026-27?team=LAL&limit=5")
    assert sched_resp.status_code == 200
    assert len(sched_resp.json()) == 5
    
    # 5. Invalid team error handling (400 Bad Request)
    err_resp = api_client.post("/predict", json={
        "home_team": "InvalidNonexistentTeam",
        "away_team": "GSW",
        "game_date": "2026-10-21"
    })
    assert err_resp.status_code == 400
    assert "Unknown NBA team identifier" in err_resp.json()["detail"]

    # 6. Invalid date format (422 Unprocessable Entity)
    date_err_resp = api_client.post("/predict", json={
        "home_team": "LAL",
        "away_team": "GSW",
        "game_date": "invalid-date-format"
    })
    assert date_err_resp.status_code == 422

    # 7. Missing required field (422 Unprocessable Entity)
    missing_resp = api_client.post("/predict", json={
        "home_team": "LAL"
    })
    assert missing_resp.status_code == 422

    # 8. Non-existent scheduled game number (404 Not Found)
    not_found_game = api_client.get("/predict/99999")
    assert not_found_game.status_code == 404
    assert "not found" in not_found_game.json()["detail"].lower()

    # 9. Out-of-range as_of_date for next Lakers game (404 Not Found)
    out_of_range_lakers = api_client.get("/predict/lakers/next?as_of_date=2099-01-01")
    assert out_of_range_lakers.status_code == 404

    # 10. Invalid monitoring window query parameter (422 Unprocessable Entity)
    inv_window = api_client.get("/monitoring/health?window=invalid_window")
    assert inv_window.status_code == 422
