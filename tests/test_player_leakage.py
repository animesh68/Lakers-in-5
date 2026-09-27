"""
Temporal Data Leakage & Trade Boundary Tests for Phase 8 Player Performance Models.
Guarantees that no target-game statistics, future games, or future trade states
ever contaminate pregame player feature vectors.
"""

from datetime import datetime, date
import duckdb
import pytest
import pandas as pd

from src.features.player_prediction_features import PlayerFeatureEngine
from src.inference.roster_service import RosterService


def test_target_game_stat_exclusion(tmp_path):
    """
    CRITICAL: Verifies that target game performance (minutes, points, rebounds, assists)
    is strictly excluded from pregame rolling features.
    """
    parquet_path = tmp_path / "mock_player_stats.parquet"
    team_parquet_path = tmp_path / "mock_team_stats.parquet"

    # Create mock history with a past game, target game, and future game for a player
    con = duckdb.connect()
    con.execute(f"""
        CREATE TABLE pgs AS
        SELECT 
            'P1' AS personId,
            'G_PAST' AS gameId,
            '2026-01-10 19:00:00' AS gameDateTimeEst,
            '1610612747' AS playerteamId,
            '1610612744' AS opponentteamId,
            '1' AS home,
            '30.0' AS numMinutes,
            '20.0' AS points,
            '5.0' AS reboundsTotal,
            '4.0' AS assists,
            '15.0' AS fieldGoalsAttempted,
            '4.0' AS freeThrowsAttempted,
            '2.0' AS turnovers,
            'F' AS startingPosition
        UNION ALL
        SELECT 
            'P1', 'G_TARGET', '2026-01-15 19:00:00', '1610612747', '1610612744', '1',
            '42.0', '50.0', '15.0', '10.0', '30.0', '10.0', '5.0', 'F'
        UNION ALL
        SELECT 
            'P1', 'G_FUTURE', '2026-01-20 19:00:00', '1610612747', '1610612744', '1',
            '35.0', '25.0', '8.0', '6.0', '18.0', '5.0', '3.0', 'F';
    """)
    con.execute(f"COPY pgs TO '{parquet_path.as_posix()}' (FORMAT PARQUET)")
    
    # Team stats
    con.execute(f"""
        CREATE TABLE tgs AS
        SELECT 
            '1610612747' AS teamId,
            '2026-01-10 19:00:00' AS gameDateTimeEst,
            110.0 AS teamScore,
            105.0 AS opponentScore,
            85.0 AS fieldGoalsAttempted,
            20.0 AS freeThrowsAttempted,
            12.0 AS turnovers;
    """)
    con.execute(f"COPY tgs TO '{team_parquet_path.as_posix()}' (FORMAT PARQUET)")
    con.close()

    engine = PlayerFeatureEngine(parquet_path=str(parquet_path))
    engine.team_parquet_path = str(team_parquet_path)

    # Extract pregame features as of target date 2026-01-15
    feats = engine.extract_pregame_player_features(
        person_id="P1",
        team_id="1610612747",
        opponent_team_id="1610612744",
        target_game_date="2026-01-15",
        is_home=True
    )

    # Verify that the 50-point target game is NOT reflected in the pregame feature vector!
    assert feats["player_min_avg_5"] == 30.0, f"Expected 30.0 from prior game, got {feats['player_min_avg_5']}"
    assert feats["player_pts_per_min_10"] == round(20.0 / 30.0, 4), "Target game points leaked into pregame feature!"


def test_trade_date_temporal_boundary():
    """
    Verifies that prior to offseason transition cutoff (2026-07-01), player remains on prior team
    without new team additions.
    """
    roster_svc = RosterService()
    
    # As of 2026-06-01 (pre-offseason), Kawhi is not in Raptors roster universe
    pre_roster = roster_svc.get_active_roster_universe("TOR", "2026-06-01")
    pre_names = [p["player_name"] for p in pre_roster]
    assert "Kawhi Leonard" not in pre_names

    # As of 2026-10-21 (post-offseason), Kawhi is in Raptors roster universe
    post_roster = roster_svc.get_active_roster_universe("TOR", "2026-10-21")
    post_names = [p["player_name"] for p in post_roster]
    assert "Kawhi Leonard" in post_names
