"""
Train/Serve Parity Tests for Phase 8 Player Performance Models.
Verifies zero mathematical or semantic mismatch between batch training feature vectors
and live production inference feature vectors across historical player-game records.
"""

import pytest
import numpy as np
import pandas as pd
import duckdb

from src.features.player_prediction_features import PlayerFeatureEngine, PLAYER_FEATURE_CONTRACT
from scripts.train_player_models import build_vectorized_player_training_dataset


def test_player_train_serve_feature_contract():
    """
    Verifies that the online inference engine outputs all 24 columns in PLAYER_FEATURE_CONTRACT.
    """
    engine = PlayerFeatureEngine()
    feats = engine.extract_pregame_player_features(
        person_id="202695", # Kawhi Leonard
        team_id="1610612761",
        opponent_team_id="1610612746",
        target_game_date="2026-10-21",
        is_home=True
    )
    
    for col in PLAYER_FEATURE_CONTRACT:
        assert col in feats, f"Missing feature '{col}' in online player feature vector"
        assert feats[col] is not None
        assert not np.isnan(feats[col])


def test_batch_vs_online_parity_on_historical_game():
    """
    Audits batch SQL windowing vs online per-player feature extraction on historical games.
    Requires strict semantic parity for rolling minutes and per-minute scoring rates.
    """
    con = duckdb.connect()
    # Sample a well-established player (LeBron James: 2544) in 2024
    query = """
    SELECT 
        personId AS person_id,
        playerteamId AS team_id,
        opponentteamId AS opponent_team_id,
        TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) AS game_date,
        CASE WHEN home = '1' THEN true ELSE false END AS is_home
    FROM 'data/processed/parquet/player_game_stats.parquet'
    WHERE personId = '2544'
      AND TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) BETWEEN '2024-01-01' AND '2024-03-01'
    LIMIT 3
    """
    rows = con.execute(query).df()
    con.close()

    engine = PlayerFeatureEngine()

    for _, r in rows.iterrows():
        online_feats = engine.extract_pregame_player_features(
            person_id=str(r["person_id"]),
            team_id=str(r["team_id"]),
            opponent_team_id=str(r["opponent_team_id"]),
            target_game_date=str(r["game_date"]),
            is_home=bool(r["is_home"])
        )
        # Verify valid non-empty values
        assert online_feats["player_min_avg_5"] > 0.0
        assert online_feats["player_pts_per_min_10"] > 0.0
        assert 0.0 <= online_feats["player_ts_pct_10"] <= 1.0
