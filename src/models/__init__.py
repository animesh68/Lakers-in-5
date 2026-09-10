"""
Lakers in 5 - Model Experimentation, Validation, and Serving Package.
"""

from src.models.preprocessing import (
    METADATA_COLUMNS,
    TARGET_COLUMNS,
    get_feature_columns,
    DifferentialFeatureTransformer,
    build_preprocessor_pipeline,
)
from src.models.validation import TimeSeriesWalkForwardCV
from src.models.baselines import NaiveHomeBaseline, EloBaseline
from src.models.classification import (
    get_classifier,
    train_evaluate_classifier_fold,
)
from src.models.regression import (
    get_regressor,
    train_evaluate_regressor_fold,
)
from src.models.evaluation import (
    evaluate_classification_predictions,
    evaluate_regression_predictions,
    compute_calibration_curve,
    compute_expected_calibration_error,
)
from src.models.tracking import ExperimentTracker

__all__ = [
    "METADATA_COLUMNS",
    "TARGET_COLUMNS",
    "get_feature_columns",
    "DifferentialFeatureTransformer",
    "build_preprocessor_pipeline",
    "TimeSeriesWalkForwardCV",
    "NaiveHomeBaseline",
    "EloBaseline",
    "get_classifier",
    "train_evaluate_classifier_fold",
    "get_regressor",
    "train_evaluate_regressor_fold",
    "evaluate_classification_predictions",
    "evaluate_regression_predictions",
    "compute_calibration_curve",
    "compute_expected_calibration_error",
    "ExperimentTracker",
]
