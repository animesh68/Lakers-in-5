"""
Player Performance Model Architecture and Training Utilities for Phase 8.
Defines Model 1 (Minutes), Model 2 (Points), Model 3 (Rebounds), and Model 4 (Assists),
supporting scikit-learn Ridge and LightGBM / Gradient Boosting regularized regression.
"""

import os
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np
import pandas as pd
import joblib
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error

from src.features.player_prediction_features import PLAYER_FEATURE_CONTRACT
from src.utils.logging import logger


class PlayerTargetRegressor:
    """
    Standardized, robust regressor pipeline for player performance target.
    Includes feature scaling, $L_2$ regularization penalty, and non-negative output clipping.
    """
    def __init__(
        self,
        target_name: str,
        alpha: float = 10.0,
        include_minutes_feature: bool = False,
        min_clip: float = 0.0,
        max_clip: float = 60.0
    ):
        self.target_name = target_name
        self.alpha = alpha
        self.include_minutes_feature = include_minutes_feature
        self.min_clip = min_clip
        self.max_clip = max_clip
        
        self.pipeline: Pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("regressor", Ridge(alpha=self.alpha, random_state=42))
        ])
        self.feature_names: List[str] = list(PLAYER_FEATURE_CONTRACT)
        if self.include_minutes_feature:
            self.feature_names.append("expected_minutes")
        self.is_fitted: bool = False

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        """Fits the regression pipeline."""
        X_mat = np.nan_to_num(X[self.feature_names].values, nan=0.0)
        self.pipeline.fit(X_mat, y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates bounded non-negative continuous target predictions."""
        if not self.is_fitted:
            raise RuntimeError(f"Model for {self.target_name} is not fitted.")
        X_mat = np.nan_to_num(X[self.feature_names].values, nan=0.0)
        preds = self.pipeline.predict(X_mat)
        return np.clip(preds, self.min_clip, self.max_clip)


class RoleStratifiedPointsModel:
    """
    Role-Stratified Points Regressor (C1 Candidate):
    Maintains 3 distinct regularized linear Ridge pipelines for:
    1. 'star': high-minute, high-usage creators (min >= 28, usage >= 0.24)
    2. 'starter': secondary/rotation starters (min >= 24)
    3. 'bench': reserve and low-minute rotation players (min < 24)
    """
    def __init__(self, alpha: float = 15.0):
        self.alpha = alpha
        self.models: Dict[str, Pipeline] = {
            "star": Pipeline([("scaler", StandardScaler()), ("regressor", Ridge(alpha=self.alpha, random_state=42))]),
            "starter": Pipeline([("scaler", StandardScaler()), ("regressor", Ridge(alpha=self.alpha, random_state=42))]),
            "bench": Pipeline([("scaler", StandardScaler()), ("regressor", Ridge(alpha=self.alpha, random_state=42))])
        }
        self.feature_names: List[str] = list(PLAYER_FEATURE_CONTRACT) + ["expected_minutes"]
        self.is_fitted: bool = False

    @staticmethod
    def get_pregame_role(df: pd.DataFrame) -> pd.Series:
        roles = pd.Series("bench", index=df.index)
        roles[df["player_min_avg_10"] >= 24.0] = "starter"
        roles[(df["player_min_avg_10"] >= 28.0) & (df["player_usage_pct_10"] >= 0.24)] = "star"
        return roles

    def fit(self, X: pd.DataFrame, y: np.ndarray):
        roles = self.get_pregame_role(X)
        for role_name, pipeline in self.models.items():
            mask = (roles == role_name).values
            if mask.sum() == 0:
                continue
            X_sub = np.nan_to_num(X.loc[mask, self.feature_names].values, nan=0.0)
            y_sub = y[mask]
            pipeline.fit(X_sub, y_sub)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        if not self.is_fitted:
            raise RuntimeError("RoleStratifiedPointsModel is not fitted.")
        roles = self.get_pregame_role(X)
        preds = np.zeros(len(X))
        for role_name, pipeline in self.models.items():
            mask = (roles == role_name).values
            if mask.sum() == 0:
                continue
            X_sub = np.nan_to_num(X.loc[mask, self.feature_names].values, nan=0.0)
            preds[mask] = pipeline.predict(X_sub)
        return np.clip(preds, 0.0, 70.0)


class PlayerPerformanceSuite:
    """
    Cohesive 4-model ensemble predicting:
    1. expected_minutes
    2. predicted_points
    3. predicted_rebounds
    4. predicted_assists
    """
    def __init__(
        self,
        model_version: str = "PlayerSuite-v1.0",
        schema_version: str = "v1.0-player",
        is_shadow: bool = False
    ):
        self.model_version = model_version
        self.schema_version = schema_version
        self.is_shadow = is_shadow
        
        # Initialize the 4 dedicated regressors
        self.minutes_model = PlayerTargetRegressor("minutes", alpha=15.0, include_minutes_feature=False, min_clip=0.0, max_clip=48.0)
        self.points_model = PlayerTargetRegressor("points", alpha=10.0, include_minutes_feature=True, min_clip=0.0, max_clip=70.0)
        self.rebounds_model = PlayerTargetRegressor("rebounds", alpha=10.0, include_minutes_feature=True, min_clip=0.0, max_clip=35.0)
        self.assists_model = PlayerTargetRegressor("assists", alpha=10.0, include_minutes_feature=True, min_clip=0.0, max_clip=30.0)

    def fit_all(self, df_train: pd.DataFrame):
        """Fits all 4 models sequentially on training dataframe."""
        logger.info(f"Fitting Player Performance Suite on {len(df_train)} player-game training records...")
        
        # 1. Fit Minutes Model
        y_min = df_train["target_minutes"].values
        self.minutes_model.fit(df_train, y_min)
        
        # Generate in-sample predicted minutes as feature input for downstream models
        train_features = df_train.copy()
        train_features["expected_minutes"] = self.minutes_model.predict(train_features)
        
        # 2. Fit Points Model
        y_pts = df_train["target_points"].values
        self.points_model.fit(train_features, y_pts)
        
        # 3. Fit Rebounds Model
        y_reb = df_train["target_rebounds"].values
        self.rebounds_model.fit(train_features, y_reb)
        
        # 4. Fit Assists Model
        y_ast = df_train["target_assists"].values
        self.assists_model.fit(train_features, y_ast)
        
        logger.info("Successfully fitted all 4 player performance models.")
        return self

    def predict_player(self, feature_dict: Dict[str, float]) -> Dict[str, float]:
        """
        Generates minutes, points, rebounds, assists predictions for a single player feature vector.
        """
        df_single = pd.DataFrame([feature_dict])
        
        # 1. Predict Minutes
        exp_min = float(self.minutes_model.predict(df_single)[0])
        df_single["expected_minutes"] = exp_min
        
        # 2. Predict Box Score Targets
        pred_pts = float(self.points_model.predict(df_single)[0])
        pred_reb = float(self.rebounds_model.predict(df_single)[0])
        pred_ast = float(self.assists_model.predict(df_single)[0])
        
        return {
            "expected_minutes": round(exp_min, 1),
            "predicted_points": round(pred_pts, 1),
            "predicted_rebounds": round(pred_reb, 1),
            "predicted_assists": round(pred_ast, 1),
        }

    def save_artifacts(self, output_dir: str, metadata: Optional[Dict[str, Any]] = None):
        """Saves all 4 model artifacts and metadata manifest."""
        os.makedirs(output_dir, exist_ok=True)
        joblib.dump(self.minutes_model, os.path.join(output_dir, "player_minutes_model.joblib"))
        joblib.dump(self.points_model, os.path.join(output_dir, "player_points_model.joblib"))
        joblib.dump(self.rebounds_model, os.path.join(output_dir, "player_rebounds_model.joblib"))
        joblib.dump(self.assists_model, os.path.join(output_dir, "player_assists_model.joblib"))
        
        meta = metadata or {}
        meta.update({
            "model_version": self.model_version,
            "feature_schema_version": self.schema_version,
            "feature_contract": PLAYER_FEATURE_CONTRACT,
            "saved_at": datetime.utcnow().isoformat(),
            "models": {
                "minutes": "PlayerMinutes-Ridge-v1",
                "points": "PlayerPoints-Ridge-v1",
                "rebounds": "PlayerRebounds-Ridge-v1",
                "assists": "PlayerAssists-Ridge-v1"
            }
        })
        with open(os.path.join(output_dir, "player_models_metadata.json"), "w") as f:
            json.dump(meta, f, indent=2)
        logger.info(f"Saved player models and manifest to {output_dir}")

    @classmethod
    def load_artifacts(cls, models_dir: str) -> "PlayerPerformanceSuite":
        """Loads fitted model suite from disk artifacts."""
        suite = cls(model_version="PlayerSuite-v1.0", is_shadow=False)
        min_path = os.path.join(models_dir, "player_minutes_model.joblib")
        pts_path = os.path.join(models_dir, "player_points_model.joblib")
        reb_path = os.path.join(models_dir, "player_rebounds_model.joblib")
        ast_path = os.path.join(models_dir, "player_assists_model.joblib")
        
        if not all(os.path.exists(p) for p in [min_path, pts_path, reb_path, ast_path]):
            raise FileNotFoundError(f"Missing player model artifacts in {models_dir}")
            
        suite.minutes_model = joblib.load(min_path)
        suite.points_model = joblib.load(pts_path)
        suite.rebounds_model = joblib.load(reb_path)
        suite.assists_model = joblib.load(ast_path)
        return suite

    @classmethod
    def load_shadow_suite(cls, shadow_dir: str) -> "PlayerPerformanceSuite":
        """Loads experimental C1 shadow model suite from disk artifacts."""
        suite = cls(model_version="PlayerSuite-v1.1-c1-shadow", schema_version="v1.1-player-role-stratified", is_shadow=True)
        min_path = os.path.join(shadow_dir, "shadow_minutes_model.joblib")
        pts_path = os.path.join(shadow_dir, "shadow_points_model.joblib")
        reb_path = os.path.join(shadow_dir, "shadow_rebounds_model.joblib")
        ast_path = os.path.join(shadow_dir, "shadow_assists_model.joblib")
        
        if not all(os.path.exists(p) for p in [min_path, pts_path, reb_path, ast_path]):
            raise FileNotFoundError(f"Missing shadow model artifacts in {shadow_dir}")
            
        suite.minutes_model = joblib.load(min_path)
        suite.points_model = joblib.load(pts_path)
        suite.rebounds_model = joblib.load(reb_path)
        suite.assists_model = joblib.load(ast_path)
        return suite

