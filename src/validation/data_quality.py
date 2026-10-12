"""
Data Quality, Feature Validation, and Reliability Assurance Framework for Phase 11.
Provides reusable domain-aware validation rules for games, player records, feature vectors,
predictions, temporal consistency, and freshness.
"""

import os
import math
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime, date
import pandas as pd
import numpy as np

from src.features.player_prediction_features import PLAYER_FEATURE_CONTRACT
from src.monitoring.collector import metrics_collector
from src.utils.logging import logger, log_event


class DataQualityValidationError(ValueError):
    """Raised when data quality validation fails critically."""
    pass


class FeatureContractError(ValueError):
    """Raised when input feature vector violates the model contract."""
    pass


class PredictionValidationError(ValueError):
    """Raised when generated prediction fails output domain bounds."""
    pass


def validate_game_record(game: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates a schedule or completed game record.
    Ensures identifiers exist, teams are distinct, dates are valid, and scores are non-negative.
    """
    errors: List[str] = []

    # 1. Essential IDs and Dates
    if not game.get("game_id") and not game.get("game_num"):
        errors.append("Missing game_id / game_num identifier.")

    game_date = game.get("game_date")
    if not game_date:
        errors.append("Missing game_date.")
    else:
        try:
            str_date = str(game_date)[:10]
            datetime.strptime(str_date, "%Y-%m-%d")
        except ValueError:
            errors.append(f"Invalid game_date format: '{game_date}'. Expected YYYY-MM-DD.")

    # 2. Team Validation
    home_team = game.get("home_team") or game.get("home_team_code")
    away_team = game.get("away_team") or game.get("away_team_code")
    if not home_team:
        errors.append("Missing home_team identifier.")
    if not away_team:
        errors.append("Missing away_team identifier.")
    if home_team and away_team and str(home_team).strip().lower() == str(away_team).strip().lower():
        errors.append(f"Home team and away team cannot be identical: '{home_team}'.")

    # 3. Score validation if actuals are provided
    home_score = game.get("home_score")
    if home_score is not None:
        try:
            val = float(home_score)
            if math.isnan(val) or val < 0:
                errors.append(f"Invalid home_score: {home_score} (must be non-negative).")
        except (ValueError, TypeError):
            errors.append(f"Invalid numeric home_score: {home_score}.")

    away_score = game.get("away_score")
    if away_score is not None:
        try:
            val = float(away_score)
            if math.isnan(val) or val < 0:
                errors.append(f"Invalid away_score: {away_score} (must be non-negative).")
        except (ValueError, TypeError):
            errors.append(f"Invalid numeric away_score: {away_score}.")

    passed = len(errors) == 0
    if not passed:
        metrics_collector.inc_counter("data_quality_failures_total", labels={"check_type": "game_record"})
    return passed, errors


def validate_player_record(record: Dict[str, Any], is_actual: bool = False) -> Tuple[bool, List[str]]:
    """
    Validates an individual player box score or prediction input record.
    """
    errors: List[str] = []

    # Identifier
    player_id = record.get("person_id") or record.get("player_id")
    if not player_id:
        errors.append("Missing player identifier (person_id / player_id).")

    # If validating actual box score results
    if is_actual:
        for field in ["points", "rebounds", "assists", "minutes"]:
            val = record.get(field)
            if val is not None:
                try:
                    num = float(val)
                    if math.isnan(num) or math.isinf(num) or num < 0:
                        errors.append(f"Invalid actual {field}: {val} (must be finite non-negative number).")
                except (ValueError, TypeError):
                    errors.append(f"Non-numeric actual {field}: {val}.")

    passed = len(errors) == 0
    if not passed:
        metrics_collector.inc_counter("data_quality_failures_total", labels={"check_type": "player_record"})
    return passed, errors


def validate_feature_vector(
    features: Dict[str, Any],
    contract: Optional[List[str]] = None,
    allow_extra: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validates model feature input vector against the strict 24-feature contract.
    Ensures all contract features exist, are numeric, finite, and not NaN or Infinite.
    """
    expected_contract = contract or list(PLAYER_FEATURE_CONTRACT)
    errors: List[str] = []

    # 1. Missing Features
    missing_features = [f for f in expected_contract if f not in features]
    if missing_features:
        errors.append(f"Missing {len(missing_features)} required features: {missing_features[:5]}...")

    # 2. Value Validity (Type, NaN, Inf)
    for feat_name in expected_contract:
        if feat_name in features:
            val = features[feat_name]
            if val is None:
                errors.append(f"Feature '{feat_name}' is None.")
                continue
            try:
                num = float(val)
                if math.isnan(num):
                    errors.append(f"Feature '{feat_name}' is NaN.")
                elif math.isinf(num):
                    errors.append(f"Feature '{feat_name}' is Infinite.")
            except (ValueError, TypeError):
                errors.append(f"Feature '{feat_name}' is non-numeric: {type(val)} ({val}).")

    passed = len(errors) == 0
    if not passed:
        metrics_collector.inc_counter("data_quality_failures_total", labels={"check_type": "feature_contract"})
        log_event(logger, "feature_generation_failed", level=20, errors=errors)
    return passed, errors


def validate_prediction_output(predictions: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates model prediction output before serving to clients.
    Ensures expected target keys are present and within valid physical basketball domains.
    """
    errors: List[str] = []
    target_bounds = {
        "predicted_minutes": (0.0, 60.0),
        "predicted_points": (0.0, 100.0),
        "predicted_rebounds": (0.0, 50.0),
        "predicted_assists": (0.0, 40.0),
    }

    for target_key, (min_val, max_val) in target_bounds.items():
        if target_key in predictions:
            val = predictions[target_key]
            if val is None:
                errors.append(f"Target '{target_key}' is None.")
                continue
            try:
                num = float(val)
                if math.isnan(num) or math.isinf(num):
                    errors.append(f"Target '{target_key}' is NaN or Infinite: {val}.")
                elif num < min_val:
                    errors.append(f"Target '{target_key}' ({num:.2f}) is below minimum bound ({min_val}).")
                elif num > max_val:
                    errors.append(f"Target '{target_key}' ({num:.2f}) exceeds realistic basketball ceiling ({max_val}).")
            except (ValueError, TypeError):
                errors.append(f"Target '{target_key}' is non-numeric: {val}.")

    passed = len(errors) == 0
    if not passed:
        metrics_collector.inc_counter("data_quality_failures_total", labels={"check_type": "prediction_bounds"})
    return passed, errors


def check_temporal_leakage_safeguard(feature_date: Union[str, date, datetime], target_game_date: Union[str, date, datetime]) -> bool:
    """
    Asserts that feature observation date is strictly before target game date.
    """
    feat_d = str(feature_date)[:10]
    target_d = str(target_game_date)[:10]
    return feat_d < target_d


def check_data_freshness(
    parquet_path: Optional[str] = None,
    max_acceptable_age_days: int = 365
) -> Dict[str, Any]:
    """
    Evaluates dataset freshness against expected operational update cadence.
    Returns status: 'FRESH' | 'STALE' | 'UNKNOWN'
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    target_path = parquet_path or os.path.join(base_dir, "data", "processed", "parquet", "player_game_stats.parquet")

    if not os.path.exists(target_path):
        return {
            "status": "UNKNOWN",
            "file": os.path.basename(target_path),
            "reason": "File does not exist",
            "last_modified": None,
            "age_days": None
        }

    try:
        mtime = os.path.getmtime(target_path)
        last_dt = datetime.fromtimestamp(mtime)
        age_days = (datetime.now() - last_dt).days

        # Parquet historical lakehouse updated as needed for 2026-27 season
        status = "FRESH" if age_days <= max_acceptable_age_days else "STALE"
        return {
            "status": status,
            "file": os.path.basename(target_path),
            "last_modified": last_dt.isoformat(),
            "age_days": age_days,
            "max_acceptable_age_days": max_acceptable_age_days
        }
    except Exception as e:
        return {
            "status": "UNKNOWN",
            "file": os.path.basename(target_path),
            "reason": str(e),
            "last_modified": None,
            "age_days": None
        }
