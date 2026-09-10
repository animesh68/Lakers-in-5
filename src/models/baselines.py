"""
Baseline Models for Lakers in 5:
1. Naive Home Baseline (historical home-win rate from training fold)
2. Elo Probability Baseline (pregame Elo formula from Phase 2A)
"""

from typing import Optional, Union, Dict, Any
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, ClassifierMixin

class NaiveHomeBaseline(BaseEstimator, ClassifierMixin):
    """
    Naive baseline that always predicts the home team to win, with probability
    equal to the empirical home win rate computed strictly from the training fold.
    """
    def __init__(self):
        self.classes_ = np.array([0, 1])
        self.home_win_rate_: float = 0.5

    def fit(self, X: Any, y: Union[np.ndarray, pd.Series]) -> "NaiveHomeBaseline":
        y_arr = np.asarray(y)
        self.home_win_rate_ = float(np.mean(y_arr == 1))
        # Bound probability away from 0 and 1
        self.home_win_rate_ = np.clip(self.home_win_rate_, 0.01, 0.99)
        return self

    def predict_proba(self, X: Any) -> np.ndarray:
        n_samples = len(X)
        p_home = self.home_win_rate_
        p_away = 1.0 - p_home
        proba = np.column_stack([np.full(n_samples, p_away), np.full(n_samples, p_home)])
        return proba

    def predict(self, X: Any) -> np.ndarray:
        n_samples = len(X)
        pred = 1 if self.home_win_rate_ >= 0.5 else 0
        return np.full(n_samples, pred, dtype=int)


class EloBaseline(BaseEstimator, ClassifierMixin):
    """
    Baseline model that calculates pregame win probability directly from
    the Phase 2A Elo features using the standard logistic Elo formula.
    
    Formula:
        P(home win) = 1.0 / (1.0 + 10.0 ** (-elo_difference / 400.0))
        where elo_difference = (home_elo + home_advantage) - away_elo
    """
    def __init__(self, elo_diff_col: str = "elo_difference"):
        self.elo_diff_col = elo_diff_col
        self.classes_ = np.array([0, 1])

    def fit(self, X: Any, y: Optional[Any] = None) -> "EloBaseline":
        # Elo parameters are fixed from Phase 2A feature engineering
        return self

    def predict_proba(self, X: Union[pd.DataFrame, np.ndarray]) -> np.ndarray:
        if isinstance(X, pd.DataFrame):
            if self.elo_diff_col in X.columns:
                elo_diff = X[self.elo_diff_col].values
            elif "home_elo" in X.columns and "away_elo" in X.columns:
                # Standard home advantage (+100)
                elo_diff = (X["home_elo"].values + 100.0) - X["away_elo"].values
            else:
                raise KeyError(f"Neither {self.elo_diff_col} nor (home_elo, away_elo) found in X")
        else:
            # Assume 1D array of elo_diff
            elo_diff = np.asarray(X)
            if elo_diff.ndim > 1:
                elo_diff = elo_diff[:, 0]
                
        # Compute Elo probability
        p_home = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
        p_home = np.clip(p_home, 1e-6, 1.0 - 1e-6)
        p_away = 1.0 - p_home
        
        return np.column_stack([p_away, p_home])

    def predict(self, X: Any) -> np.ndarray:
        proba = self.predict_proba(X)
        return (proba[:, 1] >= 0.5).astype(int)
