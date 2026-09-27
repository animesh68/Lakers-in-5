"""
Training and Chronological Walk-Forward Validation Script for Phase 8 Player Models.
Extracts leakage-safe pregame feature vectors across recent NBA seasons using high-performance
DuckDB window functions, conducts walk-forward slice evaluation, and serializes versioned joblib artifacts to models/.
"""

import os
import sys
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
import duckdb
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.features.player_prediction_features import PLAYER_FEATURE_CONTRACT, LEAGUE_PRIORS
from src.models.player_models import PlayerPerformanceSuite
from src.utils.logging import logger


def build_vectorized_player_training_dataset(
    start_date: str = "2023-10-01",
    end_date: str = "2026-06-15"
) -> pd.DataFrame:
    """
    Constructs leakage-safe pregame training feature vectors using chronological window frames.
    Guarantees strict temporal safety: features only aggregate games strictly preceding each target game date.
    """
    logger.info(f"Extracting vectorized player-game dataset between {start_date} and {end_date}...")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    parquet_path = os.path.join(base_dir, "data", "processed", "parquet", "player_game_stats.parquet")
    team_parquet_path = os.path.join(base_dir, "data", "processed", "parquet", "team_game_stats.parquet")

    con = duckdb.connect()

    query = f"""
    WITH pgs_raw AS (
        SELECT 
            pgs.personId AS person_id,
            pgs.gameId AS game_id,
            TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE) AS game_date,
            pgs.playerteamId AS team_id,
            pgs.opponentteamId AS opponent_team_id,
            CASE WHEN pgs.home = '1' THEN 1.0 ELSE 0.0 END AS is_home,
            TRY_CAST(pgs.numMinutes AS DOUBLE) AS target_minutes,
            TRY_CAST(pgs.points AS DOUBLE) AS target_points,
            TRY_CAST(pgs.reboundsTotal AS DOUBLE) AS target_rebounds,
            TRY_CAST(pgs.assists AS DOUBLE) AS target_assists,
            TRY_CAST(pgs.fieldGoalsAttempted AS DOUBLE) AS fga,
            TRY_CAST(pgs.freeThrowsAttempted AS DOUBLE) AS fta,
            TRY_CAST(pgs.turnovers AS DOUBLE) AS tov,
            CASE WHEN pgs.startingPosition IS NOT NULL AND pgs.startingPosition != '' THEN 1.0 ELSE 0.0 END AS is_starter
        FROM '{parquet_path}' pgs
        WHERE pgs.numMinutes IS NOT NULL AND pgs.numMinutes != ''
    ),
    team_context AS (
        SELECT 
            teamId AS team_id,
            TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) AS game_date,
            TRY_CAST(teamScore AS DOUBLE) AS team_score,
            TRY_CAST(opponentScore AS DOUBLE) AS opp_score,
            TRY_CAST(fieldGoalsAttempted AS DOUBLE) + 0.44 * TRY_CAST(freeThrowsAttempted AS DOUBLE) + TRY_CAST(turnovers AS DOUBLE) AS est_possessions
        FROM '{team_parquet_path}'
        WHERE teamId IS NOT NULL
    ),
    team_context_lagged AS (
        SELECT 
            team_id,
            game_date,
            AVG(est_possessions) OVER (PARTITION BY team_id ORDER BY game_date ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS team_pace_10,
            AVG(team_score / NULLIF(est_possessions, 0) * 100) OVER (PARTITION BY team_id ORDER BY game_date ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS team_off_rating_10,
            AVG(opp_score / NULLIF(est_possessions, 0) * 100) OVER (PARTITION BY team_id ORDER BY game_date ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS team_def_rating_10
        FROM team_context
    ),
    pgs_lagged AS (
        SELECT 
            p.*,
            -- Prior game date and rest
            LAG(p.game_date, 1) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id) AS prev_game_date,
            -- Rolling 5-game minutes strictly preceding target game
            AVG(p.target_minutes) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING) AS player_min_avg_5,
            -- Rolling 10-game stats strictly preceding target game
            AVG(p.target_minutes) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS player_min_avg_10,
            AVG(p.target_minutes) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS player_min_season_avg,
            
            SUM(p.target_points) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS sum_pts_10,
            SUM(p.target_rebounds) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS sum_reb_10,
            SUM(p.target_assists) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS sum_ast_10,
            SUM(p.target_minutes) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS sum_min_10,
            SUM(p.fga) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS sum_fga_10,
            SUM(p.fta) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS sum_fta_10,
            SUM(p.tov) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS sum_tov_10,
            
            AVG(p.is_starter) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING) AS is_starter_ratio_10,
            COUNT(*) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS player_games_played_season,
            
            -- Transaction & Team Change detection
            LAG(p.team_id, 1) OVER (PARTITION BY p.person_id ORDER BY p.game_date, p.game_id) AS prev_team_id,
            COUNT(*) OVER (PARTITION BY p.person_id, p.team_id ORDER BY p.game_date, p.game_id ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING) AS games_with_current_team
        FROM pgs_raw p
    )
    SELECT 
        l.person_id,
        l.game_id,
        l.game_date,
        l.team_id,
        l.opponent_team_id,
        l.is_home,
        l.target_minutes,
        l.target_points,
        l.target_rebounds,
        l.target_assists,
        
        -- Features with fallback shrinkage
        COALESCE(l.player_min_avg_5, {LEAGUE_PRIORS["min_avg"]}) AS player_min_avg_5,
        COALESCE(l.player_min_avg_10, {LEAGUE_PRIORS["min_avg"]}) AS player_min_avg_10,
        COALESCE(l.player_min_season_avg, {LEAGUE_PRIORS["min_avg"]}) AS player_min_season_avg,
        
        COALESCE(l.sum_pts_10 / NULLIF(l.sum_min_10, 0), {LEAGUE_PRIORS["pts_per_min"]}) AS player_pts_per_min_10,
        COALESCE(l.sum_reb_10 / NULLIF(l.sum_min_10, 0), {LEAGUE_PRIORS["reb_per_min"]}) AS player_reb_per_min_10,
        COALESCE(l.sum_ast_10 / NULLIF(l.sum_min_10, 0), {LEAGUE_PRIORS["ast_per_min"]}) AS player_ast_per_min_10,
        
        COALESCE(l.sum_pts_10 / NULLIF(2.0 * (l.sum_fga_10 + 0.44 * l.sum_fta_10), 0), {LEAGUE_PRIORS["ts_pct"]}) AS player_ts_pct_10,
        COALESCE(LEAST(0.40, GREATEST(0.10, (l.sum_fga_10 + 0.44 * l.sum_fta_10 + l.sum_tov_10) / NULLIF(l.sum_min_10 * 2.0, 0))), {LEAGUE_PRIORS["usage_pct"]}) AS player_usage_pct_10,
        
        COALESCE(l.is_starter_ratio_10, 0.5) AS is_starter_ratio_10,
        LEAST(82.0, COALESCE(l.player_games_played_season, 0.0)) AS player_games_played_season,
        
        COALESCE(GREATEST(1.0, CAST(l.game_date - l.prev_game_date AS DOUBLE)), 10.0) AS days_since_last_game,
        CASE WHEN (l.game_date - l.prev_game_date) = 1 THEN 1.0 ELSE 0.0 END AS is_b2b,
        
        COALESCE(tc.team_pace_10, {LEAGUE_PRIORS["pace"]}) AS team_pace_10,
        COALESCE(opp.team_pace_10, {LEAGUE_PRIORS["pace"]}) AS opponent_pace_10,
        COALESCE(opp.team_def_rating_10, {LEAGUE_PRIORS["def_rating"]}) AS opponent_def_rating_10,
        COALESCE(tc.team_off_rating_10, {LEAGUE_PRIORS["off_rating"]}) AS team_off_rating_10,
        
        CASE WHEN l.prev_team_id IS NOT NULL AND l.prev_team_id != l.team_id THEN 1.0 ELSE 0.0 END AS is_team_change,
        CASE WHEN l.prev_team_id IS NOT NULL AND l.prev_team_id != l.team_id THEN 30.0 ELSE 0.0 END AS days_since_team_change,
        COALESCE(l.games_with_current_team, 0.0) AS games_with_current_team,
        
        COALESCE(l.player_min_avg_10, {LEAGUE_PRIORS["min_avg"]}) AS prior_team_min_avg,
        COALESCE(l.sum_pts_10 / NULLIF(l.sum_min_10, 0), {LEAGUE_PRIORS["pts_per_min"]}) AS prior_team_pts_per_min,
        COALESCE(l.sum_reb_10 / NULLIF(l.sum_min_10, 0), {LEAGUE_PRIORS["reb_per_min"]}) AS prior_team_reb_per_min,
        COALESCE(l.sum_ast_10 / NULLIF(l.sum_min_10, 0), {LEAGUE_PRIORS["ast_per_min"]}) AS prior_team_ast_per_min
        
    FROM pgs_lagged l
    LEFT JOIN team_context_lagged tc
        ON l.team_id = tc.team_id AND l.game_date = tc.game_date
    LEFT JOIN team_context_lagged opp
        ON l.opponent_team_id = opp.team_id AND l.game_date = opp.game_date
    WHERE l.game_date BETWEEN '{start_date}' AND '{end_date}'
      AND l.target_minutes >= 3.0
    ORDER BY l.game_date ASC, l.game_id ASC
    """
    
    df = con.execute(query).df()
    con.close()
    logger.info(f"Loaded {len(df):,} pregame training records with zero leakage.")
    return df


def evaluate_slice(y_true: np.ndarray, y_pred: np.ndarray) -> Dict[str, float]:
    """Computes MAE, RMSE, and Bias."""
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    bias = float(np.mean(y_pred - y_true))
    return {"mae": round(mae, 3), "rmse": round(rmse, 3), "bias": round(bias, 3)}


def run_chronological_evaluation_and_training():
    """
    Executes chronological walk-forward split validation and trains champion models.
    """
    # 1. Build training dataset
    df_data = build_vectorized_player_training_dataset(start_date="2023-10-01", end_date="2026-06-15")

    # 2. Chronological Split (Train: 2023-2025, Test: 2025-2026)
    split_date = "2025-10-01"
    df_train = df_data[df_data["game_date"] < split_date].copy()
    df_test = df_data[df_data["game_date"] >= split_date].copy()

    logger.info(f"Chronological Split: Train (< {split_date}) = {len(df_train):,} rows | Test (>= {split_date}) = {len(df_test):,} rows")

    # 3. Fit Model Suite on Train Split
    suite = PlayerPerformanceSuite(model_version="PlayerSuite-v1.0", schema_version="v1.0-player")
    suite.fit_all(df_train)

    # 4. Generate Out-of-Sample Predictions on Test Split
    test_features = df_test.copy()
    pred_minutes = suite.minutes_model.predict(test_features)
    test_features["expected_minutes"] = pred_minutes
    pred_points = suite.points_model.predict(test_features)
    pred_rebounds = suite.rebounds_model.predict(test_features)
    pred_assists = suite.assists_model.predict(test_features)

    # 5. Evaluate Overall Metrics
    eval_results = {
        "overall": {
            "minutes": evaluate_slice(df_test["target_minutes"].values, pred_minutes),
            "points": evaluate_slice(df_test["target_points"].values, pred_points),
            "rebounds": evaluate_slice(df_test["target_rebounds"].values, pred_rebounds),
            "assists": evaluate_slice(df_test["target_assists"].values, pred_assists),
            "sample_count": len(df_test)
        },
        "slices": {}
    }

    # Slice: High Minutes (>= 25 mins)
    mask_high = df_test["target_minutes"] >= 25.0
    if mask_high.sum() > 0:
        eval_results["slices"]["high_minutes"] = {
            "minutes": evaluate_slice(df_test.loc[mask_high, "target_minutes"].values, pred_minutes[mask_high]),
            "points": evaluate_slice(df_test.loc[mask_high, "target_points"].values, pred_points[mask_high]),
            "rebounds": evaluate_slice(df_test.loc[mask_high, "target_rebounds"].values, pred_rebounds[mask_high]),
            "assists": evaluate_slice(df_test.loc[mask_high, "target_assists"].values, pred_assists[mask_high]),
            "sample_count": int(mask_high.sum())
        }

    # Slice: Low Minutes (< 15 mins)
    mask_low = df_test["target_minutes"] < 15.0
    if mask_low.sum() > 0:
        eval_results["slices"]["low_minutes"] = {
            "minutes": evaluate_slice(df_test.loc[mask_low, "target_minutes"].values, pred_minutes[mask_low]),
            "points": evaluate_slice(df_test.loc[mask_low, "target_points"].values, pred_points[mask_low]),
            "rebounds": evaluate_slice(df_test.loc[mask_low, "target_rebounds"].values, pred_rebounds[mask_low]),
            "assists": evaluate_slice(df_test.loc[mask_low, "target_assists"].values, pred_assists[mask_low]),
            "sample_count": int(mask_low.sum())
        }

    # Slice: Team Change / Transition Players
    mask_trans = df_test["is_team_change"] == 1.0
    if mask_trans.sum() > 0:
        eval_results["slices"]["team_transition"] = {
            "minutes": evaluate_slice(df_test.loc[mask_trans, "target_minutes"].values, pred_minutes[mask_trans]),
            "points": evaluate_slice(df_test.loc[mask_trans, "target_points"].values, pred_points[mask_trans]),
            "rebounds": evaluate_slice(df_test.loc[mask_trans, "target_rebounds"].values, pred_rebounds[mask_trans]),
            "assists": evaluate_slice(df_test.loc[mask_trans, "target_assists"].values, pred_assists[mask_trans]),
            "sample_count": int(mask_trans.sum())
        }

    logger.info("================ WALK-FORWARD EVALUATION RESULTS ================")
    print(json.dumps(eval_results, indent=2))

    # 6. Fit Champion Suite on Full Dataset and Save Artifacts
    logger.info("Fitting Final Champion Suite on Full Dataset...")
    champion_suite = PlayerPerformanceSuite(model_version="PlayerSuite-v1.0", schema_version="v1.0-player")
    champion_suite.fit_all(df_data)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    models_dir = os.path.join(base_dir, "models")
    champion_suite.save_artifacts(models_dir, metadata={"evaluation": eval_results})
    logger.info("Player performance model training and serialization completed successfully.")


if __name__ == "__main__":
    run_chronological_evaluation_and_training()
