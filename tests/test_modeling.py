"""
Unit and Leakage Tests for Lakers in 5 Modeling Framework (Phase 3).
"""

import os
import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

from src.models.preprocessing import (
    METADATA_COLUMNS,
    TARGET_COLUMNS,
    get_feature_columns,
    DifferentialFeatureTransformer,
    build_preprocessor_pipeline,
)
from src.models.validation import TimeSeriesWalkForwardCV, load_modeling_dataset
from src.models.baselines import NaiveHomeBaseline, EloBaseline
from src.models.classification import get_classifier
from src.models.regression import get_regressor
from src.models.evaluation import (
    evaluate_classification_predictions,
    evaluate_regression_predictions,
    compute_expected_calibration_error,
)

@pytest.fixture
def sample_feature_dataframe():
    """Generates a synthetic DataFrame mimicking game_features.parquet."""
    n_samples = 200
    np.random.seed(42)
    dates = pd.date_range("2010-01-01", periods=n_samples, freq="2D")
    
    # 4 seasons: 2010, 2011, 2012, 2013
    seasons = [2010 + i // 50 for i in range(n_samples)]
    
    df = pd.DataFrame({
        "game_id": [f"game_{i:04d}" for i in range(n_samples)],
        "game_date": dates,
        "season": seasons,
        "home_team_id": ["1610612747"] * n_samples,
        "away_team_id": ["1610612738"] * n_samples,
        "home_team": ["Los Angeles Lakers"] * n_samples,
        "away_team": ["Boston Celtics"] * n_samples,
        "home_win_pct_5": np.random.uniform(0.2, 0.8, n_samples),
        "away_win_pct_5": np.random.uniform(0.2, 0.8, n_samples),
        "home_point_diff_5": np.random.normal(2.0, 5.0, n_samples),
        "away_point_diff_5": np.random.normal(-1.0, 5.0, n_samples),
        "home_elo": np.random.normal(1550, 50, n_samples),
        "away_elo": np.random.normal(1500, 50, n_samples),
        "elo_difference": np.random.normal(100, 50, n_samples),
        "home_rest_days": np.random.choice([1.0, 2.0, 3.0, np.nan], n_samples),
        "away_rest_days": np.random.choice([1.0, 2.0, 3.0, np.nan], n_samples),
        "rest_difference": np.random.normal(0, 1.0, n_samples),
        "home_back_to_back": np.random.choice([0, 1], n_samples),
        "away_back_to_back": np.random.choice([0, 1], n_samples),
        "home_games_last_7": np.random.randint(1, 5, n_samples),
        "away_games_last_7": np.random.randint(1, 5, n_samples),
        "target_home_win": np.random.choice([0, 1], n_samples, p=[0.42, 0.58]),
        "target_point_margin": np.random.normal(3.5, 12.0, n_samples),
    })
    return df


def test_metadata_and_target_exclusion(sample_feature_dataframe):
    """Verifies that no metadata identifiers or targets are present in predictive features."""
    feature_cols = get_feature_columns(sample_feature_dataframe)
    
    for meta_col in METADATA_COLUMNS:
        assert meta_col not in feature_cols, f"Metadata column '{meta_col}' leaked into feature columns!"
        
    for target_col in TARGET_COLUMNS:
        assert target_col not in feature_cols, f"Target column '{target_col}' leaked into feature columns!"
        
    assert "home_win_pct_5" in feature_cols
    assert "elo_difference" in feature_cols


def test_temporal_walk_forward_splits(sample_feature_dataframe):
    """Verifies strict chronological walk-forward splitting without temporal leakage."""
    cv = TimeSeriesWalkForwardCV(
        start_season=2010,
        val_start_season=2012,
        val_end_season=2012,
        test_season=2013
    )
    folds = cv.split_development_folds(sample_feature_dataframe)
    assert len(folds) == 1
    
    fold = folds[0]
    train_meta = fold["train_metadata"]
    val_meta = fold["val_metadata"]
    
    # Assert training is strictly strictly before validation
    assert train_meta["season"].max() < fold["val_season"]
    assert train_meta["game_date"].max() < val_meta["game_date"].min()
    
    # Assert test season 2013 is completely isolated
    assert 2013 not in train_meta["season"].values
    assert 2013 not in val_meta["season"].values


def test_final_test_isolation(sample_feature_dataframe):
    """Verifies that the final test set is isolated from training and has no date overlap."""
    cv = TimeSeriesWalkForwardCV(
        start_season=2010,
        val_start_season=2011,
        val_end_season=2012,
        test_season=2013
    )
    split = cv.get_final_test_split(sample_feature_dataframe)
    
    assert split["test_season"] == 2013
    assert split["train_end_season"] == 2012
    assert split["train_metadata"]["season"].max() == 2012
    assert (split["test_metadata"]["season"] == 2013).all()
    assert split["train_metadata"]["game_date"].max() < split["test_metadata"]["game_date"].min()


def test_preprocessor_fitted_strictly_on_train():
    """Verifies that imputer and scaler statistics are derived solely from training fold."""
    X_train = pd.DataFrame({
        "feat_a": [10.0, 20.0, np.nan],  # train median = 15.0
        "feat_b": [1.0, 2.0, 3.0]
    })
    X_val = pd.DataFrame({
        "feat_a": [np.nan, 1000.0],       # val has an extreme value
        "feat_b": [10.0, 20.0]
    })
    
    pipeline = build_preprocessor_pipeline(impute_strategy="median", scale_numeric=False)
    pipeline.fit(X_train)
    
    # Transformed X_val should impute missing feat_a using X_train's median (15.0), NOT val
    X_val_trans = pipeline.transform(X_val)
    assert np.isclose(X_val_trans[0, 0], 15.0), f"Expected 15.0, got {X_val_trans[0, 0]}"


def test_differential_feature_transformer():
    """Verifies differential feature construction (home - away)."""
    df = pd.DataFrame({
        "home_win_pct_5": [0.8, 0.6],
        "away_win_pct_5": [0.4, 0.6],
        "home_elo": [1600.0, 1500.0],
        "away_elo": [1500.0, 1500.0],
        "elo_difference": [100.0, 0.0]
    })
    
    transformer = DifferentialFeatureTransformer(mode="concat")
    df_transformed = transformer.fit_transform(df)
    
    assert "diff_win_pct_5" in df_transformed.columns
    assert np.isclose(df_transformed["diff_win_pct_5"].iloc[0], 0.4)
    assert np.isclose(df_transformed["diff_win_pct_5"].iloc[1], 0.0)
    assert "diff_elo" in df_transformed.columns


def test_naive_home_baseline():
    """Verifies Naive Home Baseline predicts train home win rate bounded in [0, 1]."""
    y_train = np.array([1, 1, 1, 0, 1])  # 80% home wins
    X_train = pd.DataFrame({"dummy": [1, 2, 3, 4, 5]})
    X_val = pd.DataFrame({"dummy": [10, 20]})
    
    model = NaiveHomeBaseline()
    model.fit(X_train, y_train)
    
    probas = model.predict_proba(X_val)
    assert probas.shape == (2, 2)
    assert np.isclose(probas[0, 1], 0.8)
    assert np.isclose(probas[0, 0], 0.2)
    preds = model.predict(X_val)
    assert (preds == 1).all()


def test_elo_baseline():
    """Verifies Elo baseline matches exact logistic formula."""
    X_val = pd.DataFrame({
        "elo_difference": [0.0, 400.0, -400.0]
    })
    model = EloBaseline()
    probas = model.predict_proba(X_val)
    
    # 0 diff -> 50%
    assert np.isclose(probas[0, 1], 0.5)
    # +400 diff -> 1 / (1 + 10^-1) = 1 / 1.1 = 0.90909
    assert np.isclose(probas[1, 1], 1.0 / 1.1, atol=1e-3)
    # -400 diff -> 1 / (1 + 10^1) = 1 / 11 = 0.0909
    assert np.isclose(probas[2, 1], 1.0 / 11.0, atol=1e-3)


def test_classification_and_regression_factories(sample_feature_dataframe):
    """Verifies all classifier and regressor model factories instantiate and fit cleanly."""
    feature_cols = get_feature_columns(sample_feature_dataframe)
    X = sample_feature_dataframe[feature_cols]
    y_win = sample_feature_dataframe["target_home_win"].values
    y_margin = sample_feature_dataframe["target_point_margin"].values
    
    # Test Classifiers
    clf_names = ["logistic_regression", "lightgbm", "xgboost"]
    for name in clf_names:
        clf = get_classifier(name, random_state=42)
        clf.fit(X, y_win)
        probas = clf.predict_proba(X)
        assert probas.shape == (len(X), 2)
        assert (probas >= 0.0).all() and (probas <= 1.0).all()
        
    # Test Regressors
    reg_names = ["ridge", "lightgbm_regressor", "xgboost_regressor"]
    for name in reg_names:
        reg = get_regressor(name, random_state=42)
        reg.fit(X, y_margin)
        preds = reg.predict(X)
        assert len(preds) == len(X)
        assert np.isfinite(preds).all()


def test_synthetic_future_leakage_detection():
    """
    Synthetic Leakage Test:
    Verifies that if a future-derived feature is accidentally passed,
    the framework's metadata/target exclusion prevents leakage.
    """
    df_synthetic = pd.DataFrame({
        "game_id": ["g1", "g2"],
        "game_date": pd.to_datetime(["2020-01-01", "2020-01-03"]),
        "season": [2020, 2020],
        "home_team_id": ["1", "2"],
        "away_team_id": ["2", "1"],
        "home_team": ["Lakers", "Warriors"],
        "away_team": ["Warriors", "Lakers"],
        "home_win_pct_5": [0.6, 0.7],
        "away_win_pct_5": [0.5, 0.4],
        "target_home_win": [1, 0],
        "target_point_margin": [5.0, -8.0],
    })
    
    feature_cols = get_feature_columns(df_synthetic)
    assert "target_home_win" not in feature_cols
    assert "target_point_margin" not in feature_cols
    assert "game_id" not in feature_cols
