"""
Classification Models and Pipeline Definitions for Lakers in 5.
Includes: Logistic Regression (Pipeline), LightGBM, and XGBoost.
"""

from typing import Dict, Any, Tuple, Optional, Union
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from lightgbm import LGBMClassifier
from xgboost import XGBClassifier

from src.models.preprocessing import DifferentialFeatureTransformer
from src.models.baselines import NaiveHomeBaseline, EloBaseline
from src.utils.logging import logger

def get_classifier(
    model_name: str,
    random_state: int = 42,
    use_differentials: bool = False,
    diff_mode: str = "concat",
    **kwargs
) -> Any:
    """
    Factory to construct classification pipelines and estimators.
    
    Supported model names:
    - 'naive_home': Naive home baseline
    - 'elo_baseline': Elo probability baseline
    - 'logistic_regression': Imputer + Scaler + LogisticRegression Pipeline
    - 'lightgbm': LightGBM Classifier
    - 'xgboost': XGBoost Classifier
    """
    name = model_name.lower().strip()
    
    if name == "naive_home":
        return NaiveHomeBaseline()
        
    elif name == "elo_baseline":
        return EloBaseline()
        
    elif name == "logistic_regression":
        steps = []
        if use_differentials:
            steps.append(("diff", DifferentialFeatureTransformer(mode=diff_mode)))
        steps.append(("imputer", SimpleImputer(strategy="median")))
        steps.append(("scaler", StandardScaler()))
        
        lr_kwargs = {
            "C": kwargs.get("C", 1.0),
            "max_iter": kwargs.get("max_iter", 1000),
            "random_state": random_state,
            "solver": kwargs.get("solver", "lbfgs")
        }
        steps.append(("model", LogisticRegression(**lr_kwargs)))
        return Pipeline(steps)
        
    elif name == "lightgbm":
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
                ("model", LGBMClassifier(**lgb_params))
            ])
        return LGBMClassifier(**lgb_params)
        
    elif name == "xgboost":
        xgb_params = {
            "n_estimators": kwargs.get("n_estimators", 150),
            "learning_rate": kwargs.get("learning_rate", 0.05),
            "max_depth": kwargs.get("max_depth", 5),
            "subsample": kwargs.get("subsample", 0.8),
            "colsample_bytree": kwargs.get("colsample_bytree", 0.8),
            "eval_metric": "logloss",
            "random_state": random_state,
            "n_jobs": kwargs.get("n_jobs", -1),
        }
        if use_differentials:
            return Pipeline([
                ("diff", DifferentialFeatureTransformer(mode=diff_mode)),
                ("model", XGBClassifier(**xgb_params))
            ])
        return XGBClassifier(**xgb_params)
        
    else:
        raise ValueError(f"Unknown classifier model_name: {model_name}")


def train_evaluate_classifier_fold(
    model: Any,
    X_train: pd.DataFrame,
    y_train: np.ndarray,
    X_val: pd.DataFrame,
    y_val: np.ndarray
) -> Tuple[np.ndarray, np.ndarray, Any]:
    """
    Fits model strictly on X_train, y_train and generates predictions on X_val.
    Returns (pred_probas, pred_labels, fitted_model).
    """
    model.fit(X_train, y_train)
    pred_probas = model.predict_proba(X_val)
    pred_labels = model.predict(X_val)
    return pred_probas, pred_labels, model
