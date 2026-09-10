"""
Time-Series Walk-Forward Splitter and Validation Module for Lakers in 5.
Enforces strict chronological expanding window validation and isolates the 2025-26 test set.
"""

from typing import List, Dict, Any, Tuple, Optional
import os
import pandas as pd
import numpy as np
import duckdb
from src.models.preprocessing import get_feature_columns, METADATA_COLUMNS, TARGET_COLUMNS
from src.utils.logging import logger

def load_modeling_dataset(
    features_path: Optional[str] = None,
    games_path: Optional[str] = None,
    start_season: int = 2000,
    end_season: int = 2025,
    regular_season_only: bool = True
) -> pd.DataFrame:
    """
    Loads feature matrix, filters regular season games from start_season to end_season,
    and sorts strictly chronologically by (game_date, game_id).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    features_path = features_path or os.path.join(base_dir, "data", "features", "game_features.parquet")
    games_path = games_path or os.path.join(base_dir, "data", "processed", "parquet", "games.parquet")
    
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Feature dataset not found at {features_path}")
        
    con = duckdb.connect()
    if regular_season_only and os.path.exists(games_path):
        logger.info(f"Loading regular season games ({start_season}-{end_season}) with feature matrix...")
        query = f"""
        SELECT f.*
        FROM '{features_path}' f
        JOIN '{games_path}' g ON f.game_id = g.gameId
        WHERE f.season >= {start_season} AND f.season <= {end_season}
          AND g.gameType = 'Regular Season'
        ORDER BY f.game_date, f.game_id
        """
    else:
        logger.info(f"Loading games ({start_season}-{end_season}) with feature matrix...")
        query = f"""
        SELECT *
        FROM '{features_path}'
        WHERE season >= {start_season} AND season <= {end_season}
        ORDER BY game_date, game_id
        """
    df = con.execute(query).df()
    
    # Ensure proper datetime format
    df["game_date"] = pd.to_datetime(df["game_date"])
    df = df.sort_values(by=["game_date", "game_id"]).reset_index(drop=True)
    logger.info(f"Loaded {len(df):,} regular season games across seasons {df['season'].min()} to {df['season'].max()}.")
    return df


class TimeSeriesWalkForwardCV:
    """
    Expanding-window walk-forward cross-validation splitter.
    
    For a given validation season S:
      - Train set: all regular-season games with season in [start_season, S - 1]
      - Validation set: all regular-season games with season == S
      
    Guarantees:
      1. Train max(game_date) < Val min(game_date)
      2. No future sample leakage into training sets
      3. The final test season (e.g. 2025) is strictly isolated and never present in dev folds.
    """
    def __init__(
        self,
        start_season: int = 2000,
        val_start_season: int = 2015,
        val_end_season: int = 2024,
        test_season: int = 2025
    ):
        self.start_season = start_season
        self.val_start_season = val_start_season
        self.val_end_season = val_end_season
        self.test_season = test_season

    def split_development_folds(
        self,
        df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Generates expanding-window validation folds for model selection.
        """
        folds = []
        feature_cols = get_feature_columns(df)
        
        for fold_idx, val_season in enumerate(range(self.val_start_season, self.val_end_season + 1), start=1):
            train_mask = (df["season"] >= self.start_season) & (df["season"] < val_season)
            val_mask = (df["season"] == val_season)
            
            df_train = df[train_mask].copy()
            df_val = df[val_mask].copy()
            
            # Temporal integrity assertions
            assert len(df_train) > 0, f"Fold {fold_idx}: Train set is empty for val_season {val_season}"
            assert len(df_val) > 0, f"Fold {fold_idx}: Val set is empty for val_season {val_season}"
            assert df_train["season"].max() < val_season, f"Fold {fold_idx}: Training season leaked into validation season"
            assert df_train["game_date"].max() < df_val["game_date"].min(), f"Fold {fold_idx}: Date overlap between train and val"
            assert self.test_season not in df_train["season"].values, f"Fold {fold_idx}: Test season {self.test_season} found in training data!"
            assert self.test_season not in df_val["season"].values, f"Fold {fold_idx}: Test season {self.test_season} found in validation data!"

            fold_data = {
                "fold_idx": fold_idx,
                "train_start_season": int(df_train["season"].min()),
                "train_end_season": int(df_train["season"].max()),
                "val_season": int(val_season),
                "train_count": len(df_train),
                "val_count": len(df_val),
                "X_train": df_train[feature_cols].copy(),
                "y_train_win": df_train["target_home_win"].values.astype(int),
                "y_train_margin": df_train["target_point_margin"].values.astype(float),
                "X_val": df_val[feature_cols].copy(),
                "y_val_win": df_val["target_home_win"].values.astype(int),
                "y_val_margin": df_val["target_point_margin"].values.astype(float),
                "train_metadata": df_train[METADATA_COLUMNS].copy(),
                "val_metadata": df_val[METADATA_COLUMNS].copy(),
            }
            folds.append(fold_data)
            
        logger.info(f"Generated {len(folds)} walk-forward validation folds (Val seasons: {self.val_start_season} to {self.val_end_season}).")
        return folds

    def get_final_test_split(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Generates the final test evaluation split.
        Train on all development data (start_season through val_end_season).
        Evaluate once on test_season.
        """
        feature_cols = get_feature_columns(df)
        
        train_mask = (df["season"] >= self.start_season) & (df["season"] <= self.val_end_season)
        test_mask = (df["season"] == self.test_season)
        
        df_train = df[train_mask].copy()
        df_test = df[test_mask].copy()
        
        assert len(df_train) > 0, "Final test split: Train set is empty"
        assert len(df_test) > 0, f"Final test split: Test set for season {self.test_season} is empty"
        assert df_train["season"].max() < self.test_season, "Final test split: Training seasons overlap test season"
        assert df_train["game_date"].max() < df_test["game_date"].min(), "Final test split: Date overlap with test season"
        
        return {
            "train_start_season": int(df_train["season"].min()),
            "train_end_season": int(df_train["season"].max()),
            "test_season": int(self.test_season),
            "train_count": len(df_train),
            "test_count": len(df_test),
            "X_train": df_train[feature_cols].copy(),
            "y_train_win": df_train["target_home_win"].values.astype(int),
            "y_train_margin": df_train["target_point_margin"].values.astype(float),
            "X_test": df_test[feature_cols].copy(),
            "y_test_win": df_test["target_home_win"].values.astype(int),
            "y_test_margin": df_test["target_point_margin"].values.astype(float),
            "train_metadata": df_train[METADATA_COLUMNS].copy(),
            "test_metadata": df_test[METADATA_COLUMNS].copy(),
        }

    def get_production_dataset(
        self,
        df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        Returns full training matrix through test_season (e.g. 2000-2025)
        for training the final production artifact to be used for future (2026-27) inference.
        """
        feature_cols = get_feature_columns(df)
        mask = (df["season"] >= self.start_season) & (df["season"] <= self.test_season)
        df_prod = df[mask].copy()
        
        return {
            "start_season": int(df_prod["season"].min()),
            "end_season": int(df_prod["season"].max()),
            "count": len(df_prod),
            "X": df_prod[feature_cols].copy(),
            "y_win": df_prod["target_home_win"].values.astype(int),
            "y_margin": df_prod["target_point_margin"].values.astype(float),
            "metadata": df_prod[METADATA_COLUMNS].copy(),
            "feature_names": feature_cols,
        }
