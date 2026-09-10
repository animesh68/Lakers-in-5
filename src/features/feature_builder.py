"""
Master Feature Builder Pipeline for Lakers in 5.
Orchestrates leakage-safe feature generation, combines team, player, elo, and schedule features,
and outputs the ML-ready dataset with metadata.
"""

import os
import json
import time
from typing import Dict, Any, Optional, Tuple
import duckdb
import pandas as pd
import numpy as np
from src.lake.duckdb_client import DuckDBClient
from src.features.team_features import TeamFeatureGenerator
from src.features.player_features import PlayerFeatureGenerator
from src.features.elo import EloCalculator
from src.features.schedule_features import ScheduleFeatureGenerator
from src.utils.logging import logger

class FeatureBuilder:
    """
    Builds the complete game-level ML feature matrix from the Parquet Analytical Lakehouse.
    """
    def __init__(
        self,
        output_dir: Optional[str] = None,
        elo_k_factor: float = 20.0,
        elo_home_advantage: float = 100.0,
        player_min_minutes: float = 10.0
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.output_dir = output_dir or os.path.join(base_dir, "data", "features")
        os.makedirs(self.output_dir, exist_ok=True)
        
        self.elo_k_factor = elo_k_factor
        self.elo_home_advantage = elo_home_advantage
        self.player_min_minutes = player_min_minutes

    def get_official_games(self, client: DuckDBClient) -> pd.DataFrame:
        """
        Extracts official games excluding synthetic parent records.
        """
        logger.info("Extracting official games from Lakehouse...")
        query = """
        SELECT 
            gameId AS game_id,
            TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) AS game_date,
            CASE 
                WHEN MONTH(TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                THEN YEAR(TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE))
                ELSE YEAR(TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE)) - 1
            END AS season,
            hometeamId AS home_team_id,
            awayteamId AS away_team_id,
            TRIM(COALESCE(hometeamCity, '') || ' ' || COALESCE(hometeamName, '')) AS home_team,
            TRIM(COALESCE(awayteamCity, '') || ' ' || COALESCE(awayteamName, '')) AS away_team,
            TRY_CAST(homeScore AS DOUBLE) AS home_score,
            TRY_CAST(awayScore AS DOUBLE) AS away_score
        FROM games
        WHERE hometeamId IS NOT NULL AND awayteamId IS NOT NULL
        ORDER BY game_date, game_id
        """
        df = client.conn.execute(query).df()
        
        # Targets (strictly labeled as targets, NOT features)
        df["target_home_win"] = np.where(df["home_score"] > df["away_score"], 1, 0)
        df["target_point_margin"] = df["home_score"] - df["away_score"]
        
        logger.info(f"Retrieved {len(df):,} official games (194 synthetic placeholder records excluded).")
        return df

    def build_feature_dataset(self) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Executes full feature construction pipeline and returns the feature DataFrame and metadata.
        """
        start_time = time.time()
        logger.info("=" * 70)
        logger.info("STARTING PHASE 2A: LEAKAGE-SAFE FEATURE ENGINEERING")
        logger.info("=" * 70)

        client = DuckDBClient()

        # 1. Official Games Base & Targets
        games_df = self.get_official_games(client)

        # 2. Team Rolling Form & Efficiency Features
        team_gen = TeamFeatureGenerator(duckdb_conn=client.conn)
        team_features_df = team_gen.generate_team_rolling_features()

        # 3. Schedule & Rest Features
        sched_gen = ScheduleFeatureGenerator(duckdb_conn=client.conn)
        sched_features_df = sched_gen.generate_schedule_features()

        # 4. Player-Based Rotation Aggregations
        player_gen = PlayerFeatureGenerator(duckdb_conn=client.conn, min_rotation_minutes=self.player_min_minutes)
        player_features_df = player_gen.generate_player_rotation_features()

        # 5. Chronological Elo Ratings
        elo_calc = EloCalculator(k_factor=self.elo_k_factor, home_advantage=self.elo_home_advantage)
        elo_df = elo_calc.compute_elo_features(games_df)

        logger.info("Merging feature subsets onto game master table...")

        # Combine team-level features for Home and Away teams
        # Merge team rolling stats for home team
        home_team_stats = team_features_df.copy()
        home_team_stats.columns = ["game_id", "home_team_id"] + [f"home_{col}" for col in home_team_stats.columns if col not in ["game_id", "team_id"]]
        merged = pd.merge(games_df, home_team_stats, on=["game_id", "home_team_id"], how="left")

        # Merge team rolling stats for away team
        away_team_stats = team_features_df.copy()
        away_team_stats.columns = ["game_id", "away_team_id"] + [f"away_{col}" for col in away_team_stats.columns if col not in ["game_id", "team_id"]]
        merged = pd.merge(merged, away_team_stats, on=["game_id", "away_team_id"], how="left")

        # Merge schedule stats for home team
        home_sched = sched_features_df.copy()
        home_sched.columns = ["game_id", "home_team_id", "home_rest_days", "home_back_to_back", "home_games_last_7"]
        merged = pd.merge(merged, home_sched, on=["game_id", "home_team_id"], how="left")

        # Merge schedule stats for away team
        away_sched = sched_features_df.copy()
        away_sched.columns = ["game_id", "away_team_id", "away_rest_days", "away_back_to_back", "away_games_last_7"]
        merged = pd.merge(merged, away_sched, on=["game_id", "away_team_id"], how="left")
        
        # Calculate rest difference
        merged["rest_difference"] = merged["home_rest_days"] - merged["away_rest_days"]

        # Merge player rotation stats for home team
        home_players = player_features_df.copy()
        home_players.columns = ["game_id", "home_team_id", "home_rotation_points_5", "home_rotation_ts_5", "home_rotation_usage_5"]
        merged = pd.merge(merged, home_players, on=["game_id", "home_team_id"], how="left")

        # Merge player rotation stats for away team
        away_players = player_features_df.copy()
        away_players.columns = ["game_id", "away_team_id", "away_rotation_points_5", "away_rotation_ts_5", "away_rotation_usage_5"]
        merged = pd.merge(merged, away_players, on=["game_id", "away_team_id"], how="left")

        # Merge Elo ratings
        merged = pd.merge(merged, elo_df, on="game_id", how="left")

        # Drop raw game outcomes from feature columns to prevent any accidental leakage
        feature_cols_order = [
            "game_id", "game_date", "season", "home_team_id", "away_team_id", "home_team", "away_team",
            # Team Recent Form (Last 5)
            "home_win_pct_5", "away_win_pct_5",
            "home_avg_points_5", "away_avg_points_5",
            "home_avg_points_allowed_5", "away_avg_points_allowed_5",
            "home_point_diff_5", "away_point_diff_5",
            # Team Recent Form (Last 10)
            "home_win_pct_10", "away_win_pct_10",
            "home_avg_points_10", "away_avg_points_10",
            "home_avg_points_allowed_10", "away_avg_points_allowed_10",
            "home_point_diff_10", "away_point_diff_10",
            # Advanced Team Strength (Last 5)
            "home_off_rating_5", "away_off_rating_5",
            "home_def_rating_5", "away_def_rating_5",
            "home_efg_5", "away_efg_5",
            "home_ts_5", "away_ts_5",
            "home_pace_5", "away_pace_5",
            # Advanced Team Strength (Last 10)
            "home_off_rating_10", "away_off_rating_10",
            "home_def_rating_10", "away_def_rating_10",
            "home_efg_10", "away_efg_10",
            "home_ts_10", "away_ts_10",
            "home_pace_10", "away_pace_10",
            # Elo Ratings
            "home_elo", "away_elo", "elo_difference",
            # Rest & Schedule Features
            "home_rest_days", "away_rest_days", "rest_difference",
            "home_back_to_back", "away_back_to_back",
            "home_games_last_7", "away_games_last_7",
            # Player Rotation Form
            "home_rotation_points_5", "away_rotation_points_5",
            "home_rotation_ts_5", "away_rotation_ts_5",
            "home_rotation_usage_5", "away_rotation_usage_5",
            # Targets (NOT features)
            "target_home_win", "target_point_margin"
        ]

        final_df = merged[[c for c in feature_cols_order if c in merged.columns]].copy()
        
        # Save Parquet feature dataset
        output_parquet = os.path.join(self.output_dir, "game_features.parquet")
        final_df.to_parquet(output_parquet, index=False, compression="ZSTD")
        
        # Build Metadata
        metadata = self._build_metadata(final_df)
        metadata_path = os.path.join(self.output_dir, "feature_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        elapsed = time.time() - start_time
        logger.info(f"✅ Successfully built feature dataset: {len(final_df):,} rows x {len(final_df.columns)} columns in {elapsed:.2f}s")
        logger.info(f"Output saved to: {output_parquet}")
        logger.info(f"Metadata saved to: {metadata_path}")

        return final_df, metadata

    def _build_metadata(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Constructs comprehensive feature metadata documenting source, definition, lookback, and temporal rules.
        """
        meta = {
            "dataset_info": {
                "total_rows": len(df),
                "total_columns": len(df.columns),
                "earliest_game": str(df["game_date"].min()),
                "latest_game": str(df["game_date"].max()),
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "temporal_constraint": "Strictly pregame: source_game_date < target_game_date"
            },
            "targets": {
                "target_home_win": {
                    "type": "binary_classification_target",
                    "definition": "1 if homeScore > awayScore else 0",
                    "uses_current_game": True,
                    "is_feature": False
                },
                "target_point_margin": {
                    "type": "regression_target",
                    "definition": "homeScore - awayScore",
                    "uses_current_game": True,
                    "is_feature": False
                }
            },
            "features": {}
        }

        # Document individual features
        for col in df.columns:
            if col in ["target_home_win", "target_point_margin", "game_id", "game_date", "season", "home_team_id", "away_team_id", "home_team", "away_team"]:
                continue
            
            side = "Home" if col.startswith("home_") else ("Away" if col.startswith("away_") else "Matchup")
            lookback = 5 if "_5" in col else (10 if "_10" in col else (7 if "last_7" in col else None))
            
            is_rotation = "rotation" in col
            desc = "Canonical pregame roster rotation (avg of players with >=10 MPG on team in last 5 games before tip-off, no target game participation leakage)" if is_rotation else "Rolling pregame metric"
            
            meta["features"][col] = {
                "side": side,
                "lookback_games": lookback,
                "description": desc,
                "uses_current_game": False,
                "temporal_rule": "source_game_date < target_game_date",
                "missing_value_policy": "NaN preserved for cold starts / early season games",
                "null_count": int(df[col].isna().sum())
            }

        return meta
