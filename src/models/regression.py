"""
Regression Models and Pipeline Definitions for Lakers in 5.
Predicts target_point_margin (homeScore - awayScore).
Includes: Ridge/Linear Regression (Pipeline), LightGBM Regressor, and XGBoost Regressor.
"""

from typing import Dict, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LinearRegression
from lightgbm import LGBMRegressor
from xgboost import XGBRegressor

from src.models.preprocessing import DifferentialFeatureTransformer
from src.utils.logging import logger

def get_regressor(
    model_name: str,
    random_state: int = 42,
    use_differentials: bool = False,
    diff_mode: str = "concat",
    **kwargs
) -> Any:
    """
    Factory to construct regression pipelines and estimators for margin prediction.
    
    Supported model names:
    - 'linear_regression' / 'ridge': Imputer + Scaler + Ridge Regression Pipeline
    - 'lightgbm_regressor': LightGBM Regressor
    - 'xgboost_regressor': XGBoost Regressor
    """
    name = model_name.lower().strip()
    
    if name in ("linear_regression", "ridge"):
        steps = []
        if use_differentials:
            steps.append(("diff", DifferentialFeatureTransformer(mode=diff_mode)))
        steps.append(("imputer", SimpleImputer(strategy="median")))
        steps.append(("scaler", StandardScaler()))
        
        alpha = kwargs.get("alpha", 10.0)
        steps.append(("model", Ridge(alpha=alpha, random_state=random_state)))
        return Pipeline(steps)
        
    elif name in ("lightgbm", "lightgbm_regressor"):
        lgb_params = {
            "n_estimators": kwargs.get("n_estimators", 150),
            "learning_rate": kwargs.get("learning_rate", 0.05),
            "num_leaves": kwargs.get("num_leaves", 31),
            "min_child_samples": kwargs.get("min_child_samples", 20),
            "subsample": kwargs.get("subsample", 0.8),
            "colsample_bytree": kwargs.get("colsample_bytree", 0.8),
            "random_state": random_state,
            "verbose": -1,
            "n_jobs": kwargs.get("n_jobs", -1),
        }
        if use_differentials:
            return Pipeline([
                ("diff", DifferentialFeatureTransformer(mode=diff_mode)),
                ("model", LGBMRegressor(**lgb_params))
            ])
        return LGBMRegressor(**lgb_params)
        
    elif name in ("xgboost", "xgboost_regressor"):
        xgb_params = {
            "n_estimators": kwargs.get("n_estimators", 150),
            "learning_rate": kwargs.get("learning_rate", 0.05),
            "max_depth": kwargs.get("max_depth", 5),
            "subsample": kwargs.get("subsample", 0.8),
            "colsample_bytree": kwargs.get("colsample_bytree", 0.8),
            "random_state": random_state,
            "n_jobs": kwargs.get("n_jobs", -1),
        }
        if use_differentials:
            return Pipeline([
                ("diff", DifferentialFeatureTransformer(mode=diff_mode)),
                ("model", XGBRegressor(**xgb_params))
            ])
        return XGBRegressor(**xgb_params)
        
    else:
        raise ValueError(f"Unknown regressor model_name: {model_name}")


def train_evaluate_regressor_fold(
    model: Any,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray
) -> Tuple[np.ndarray, Any]:
    """
    Fits margin regressor strictly on X_train, y_train and generates margin predictions on X_val.
    Returns (pred_margins, fitted_model).
    """
    model.fit(X_train, y_train)
    pred_margins = model.predict(X_val)
    return pred_margins, model
