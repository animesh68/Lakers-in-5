"""
Feature Preprocessing and Leakage Prevention Module for Lakers in 5.
"""

from typing import List, Tuple, Optional, Dict, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from src.utils.logging import logger

METADATA_COLUMNS = [
    "game_id",
    "game_date",
    "season",
    "home_team",
    "away_team",
    "home_team_id",
    "away_team_id",
]

TARGET_COLUMNS = [
    "target_home_win",
    "target_point_margin",
]

# Matched paired features for differential representation (home - away)
PAIRED_FEATURE_SUFFIXES = [
    "win_pct_5", "avg_points_5", "avg_points_allowed_5", "point_diff_5",
    "win_pct_10", "avg_points_10", "avg_points_allowed_10", "point_diff_10",
    "off_rating_5", "def_rating_5", "efg_5", "ts_5", "pace_5",
    "off_rating_10", "def_rating_10", "efg_10", "ts_10", "pace_10",
    "elo", "rest_days", "back_to_back", "games_last_7",
    "rotation_points_5", "rotation_ts_5", "rotation_usage_5"
]

def get_feature_columns(df: pd.DataFrame) -> List[str]:
    """
    Extracts all predictive feature column names from the dataset, strictly
    excluding metadata identifiers and target labels.
    """
    excluded = set(METADATA_COLUMNS + TARGET_COLUMNS)
    feature_cols = [col for col in df.columns if col not in excluded]
    return feature_cols

class DifferentialFeatureTransformer(BaseEstimator, TransformerMixin):
    """
    Dynamically computes differential features (home_metric - away_metric)
    inside a sklearn Pipeline without modifying the underlying raw dataset.
    
    Modes:
    - 'diff_only': Keeps only differential features and unpaired matchup features.
    - 'concat': Keeps original home/away features AND appends differential features.
    """
    def __init__(self, mode: str = "concat"):
        assert mode in ("concat", "diff_only"), f"Invalid mode: {mode}"
        self.mode = mode
        self.feature_names_out_: List[str] = []

    def fit(self, X: pd.DataFrame, y: Optional[Any] = None):
        # Infer column structure
        if isinstance(X, np.ndarray):
            # If passed as numpy array without column names, pass through
            return self
            
        feature_cols = list(X.columns)
        paired_diff_cols = []
        unpaired_cols = []
        
        home_cols = {col: col[5:] for col in feature_cols if col.startswith("home_")}
        away_cols = {col: col[5:] for col in feature_cols if col.startswith("away_")}
        
        common_suffixes = sorted(list(set(home_cols.values()).intersection(set(away_cols.values()))))
        
        for suffix in common_suffixes:
            paired_diff_cols.append(f"diff_{suffix}")
            
        unpaired_cols = [
            col for col in feature_cols
            if not (col.startswith("home_") and col[5:] in common_suffixes)
            and not (col.startswith("away_") and col[5:] in common_suffixes)
        ]
        
        if self.mode == "diff_only":
            self.feature_names_out_ = paired_diff_cols + unpaired_cols
        else:
            self.feature_names_out_ = feature_cols + paired_diff_cols
            
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        if isinstance(X, np.ndarray):
            return X
            
        df = X.copy()
        feature_cols = list(df.columns)
        
        home_cols = {col: col[5:] for col in feature_cols if col.startswith("home_")}
        away_cols = {col: col[5:] for col in feature_cols if col.startswith("away_")}
        common_suffixes = sorted(list(set(home_cols.values()).intersection(set(away_cols.values()))))
        
        diff_dict = {}
        for suffix in common_suffixes:
            h_col = f"home_{suffix}"
            a_col = f"away_{suffix}"
            if h_col in df.columns and a_col in df.columns:
                diff_dict[f"diff_{suffix}"] = df[h_col] - df[a_col]
            
        diff_df = pd.DataFrame(diff_dict, index=df.index)
        
        if self.mode == "diff_only":
            unpaired_cols = [
                col for col in feature_cols
                if not (col.startswith("home_") and col[5:] in common_suffixes)
                and not (col.startswith("away_") and col[5:] in common_suffixes)
            ]
            result_df = pd.concat([diff_df, df[unpaired_cols]], axis=1)
        else:
            result_df = pd.concat([df, diff_df], axis=1)
            
        if self.feature_names_out_ and all(c in result_df.columns for c in self.feature_names_out_):
            result_df = result_df[self.feature_names_out_]
            
        return result_df

    def get_feature_names_out(self, input_features=None) -> List[str]:
        return self.feature_names_out_


def build_preprocessor_pipeline(
    include_differentials: bool = False,
    diff_mode: str = "concat",
    impute_strategy: str = "median",
    scale_numeric: bool = True
) -> Pipeline:
    """
    Builds a leakage-safe preprocessing pipeline.
    All transformers will be fitted STRICTLY on X_train during cross-validation.
    """
    steps = []
    
    if include_differentials:
        steps.append(("diff", DifferentialFeatureTransformer(mode=diff_mode)))
        
    steps.append(("imputer", SimpleImputer(strategy=impute_strategy)))
    
    if scale_numeric:
        steps.append(("scaler", StandardScaler()))
        
    return Pipeline(steps=steps)
