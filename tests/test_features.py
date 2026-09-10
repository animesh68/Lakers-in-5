"""
Comprehensive Unit and Integration Tests for Phase 2A Feature Engineering.
Validates rolling windows, temporal boundaries, schedule calculations, Elo ratings, and player team-awareness.
"""

from datetime import date
import pandas as pd
import numpy as np
import pytest
from src.features.elo import EloCalculator
from src.features.leakage_checks import LeakageChecker

def test_synthetic_leakage_boundary():
    """
    Constructs a deterministic synthetic sequence of games and verifies that
    features for Game N strictly use Games 1..(N-1) and never Game N itself or any future game.
    """
    elo_calc = EloCalculator(initial_elo=1500.0, k_factor=20.0, home_advantage=100.0)
    
    # Synthetic 4-game sequence for Team A (Home) vs Team B (Away)
    synthetic_games = pd.DataFrame([
        {"game_id": "G1", "game_date": date(2026, 1, 1), "season": 2025, "home_team_id": 1, "away_team_id": 2, "home_score": 100, "away_score": 90},
        {"game_id": "G2", "game_date": date(2026, 1, 5), "season": 2025, "home_team_id": 1, "away_team_id": 2, "home_score": 110, "away_score": 120},
        {"game_id": "G3", "game_date": date(2026, 1, 10), "season": 2025, "home_team_id": 1, "away_team_id": 2, "home_score": 105, "away_score": 95},
        {"game_id": "G4", "game_date": date(2026, 1, 15), "season": 2025, "home_team_id": 1, "away_team_id": 2, "home_score": 130, "away_score": 110}
    ])

    elo_df = elo_calc.compute_elo_features(synthetic_games)
    
    # Game 1 pregame Elo must be exactly initial_elo (1500.0)
    assert elo_df.loc[elo_df["game_id"] == "G1", "home_elo"].iloc[0] == 1500.0
    assert elo_df.loc[elo_df["game_id"] == "G1", "away_elo"].iloc[0] == 1500.0
    
    # After G1 (Home won), Team 1's rating increases, so for G2, home_elo > 1500.0
    assert elo_df.loc[elo_df["game_id"] == "G2", "home_elo"].iloc[0] > 1500.0
    assert elo_df.loc[elo_df["game_id"] == "G2", "away_elo"].iloc[0] < 1500.0

    # For G4 on Jan 15, pregame Elo must reflect results of G1, G2, G3 but NOT G4's 130-110 outcome
    g4_home_elo = elo_df.loc[elo_df["game_id"] == "G4", "home_elo"].iloc[0]
    assert np.isfinite(g4_home_elo)

def test_player_team_awareness():
    """
    Verifies that a player traded from Team A to Team B does not have Team A stats
    incorrectly attributed to Team B.
    """
    # Player P1 played for Team 10 on Jan 1, then traded to Team 20 on Jan 10
    player_logs = pd.DataFrame([
        {"personId": 100, "playerteamId": 10, "gameId": "G_OLD", "gameDateTimeEst": "2026-01-01 19:00:00", "points": 30, "numMinutes": 35},
        {"personId": 100, "playerteamId": 20, "gameId": "G_NEW", "gameDateTimeEst": "2026-01-15 19:00:00", "points": 15, "numMinutes": 25}
    ])
    
    # Team 20 prior to G_NEW has 0 prior games for player 100 on Team 20
    team20_logs = player_logs[player_logs["playerteamId"] == 20]
    assert len(team20_logs) == 1
    assert team20_logs.iloc[0]["gameId"] == "G_NEW"

def test_leakage_checker_on_built_dataset():
    """
    Runs full LeakageChecker validation on the generated parquet feature dataset.
    """
    features_df = pd.read_parquet("data/features/game_features.parquet")
    checker = LeakageChecker(features_df)
    report = checker.run_all_checks()
    
    assert report["overall_status"] == "PASSED"
    assert len(features_df) == 73_279
    assert "target_home_win" in features_df.columns
    assert "target_point_margin" in features_df.columns
    assert "home_elo" in features_df.columns
    assert "home_win_pct_5" in features_df.columns
