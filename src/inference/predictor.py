"""
Champion Model Predictor Service for Lakers in 5.
Loads production models, performs contract validation, computes deterministic feature hashes,
and delivers persistent team-agnostic and Lakers-specific outcome predictions.
"""

import os
import json
import hashlib
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, date
import joblib
import pandas as pd
import numpy as np

from src.inference.schemas import (
    GamePredictionResponse,
    LakersGamePredictionResponse,
    ScheduledGame,
    PlayerAvailability,
)
from src.inference.schedule_service import ScheduleService, normalize_team, LAKERS_TEAM_ID
from src.inference.feature_service import ProductionFeatureService, MODEL_FEATURE_CONTRACT
from src.monitoring.store import PredictionRecord
from src.monitoring.repository import PredictionRepository
from src.utils.logging import logger

def compute_feature_hash(features_dict: Dict[str, Any]) -> str:
    """
    Produces a deterministic SHA-256 hash of the canonical 52-column feature vector.
    Sorts keys and rounds floating point numbers to ensure exact reproducibility across machines.
    """
    canonical: Dict[str, Any] = {}
    for col in MODEL_FEATURE_CONTRACT:
        val = features_dict.get(col)
        if val is None or pd.isna(val):
            canonical[col] = None
        else:
            canonical[col] = round(float(val), 6)
            
    serialized = json.dumps(canonical, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class GamePredictor:
    """
    Production inference engine that combines the feature service with Phase 3 champion models
    and optional prediction logging.
    """
    def __init__(
        self,
        classifier_path: Optional[str] = None,
        regressor_path: Optional[str] = None,
        feature_service: Optional[ProductionFeatureService] = None,
        schedule_service: Optional[ScheduleService] = None,
        repository: Optional[PredictionRepository] = None,
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.clf_path = classifier_path or os.path.join(base_dir, "models", "champion_classifier.joblib")
        self.reg_path = regressor_path or os.path.join(base_dir, "models", "champion_regressor.joblib")
        
        self.feature_service = feature_service or ProductionFeatureService()
        self.schedule_service = schedule_service or ScheduleService()
        self.repository = repository or PredictionRepository()
        
        self._load_models()

    def _load_models(self):
        """Loads and validates champion model artifacts."""
        if not os.path.exists(self.clf_path):
            raise FileNotFoundError(f"Champion classifier artifact not found at {self.clf_path}")
        if not os.path.exists(self.reg_path):
            raise FileNotFoundError(f"Champion regressor artifact not found at {self.reg_path}")
            
        logger.info(f"Loading champion classifier from {self.clf_path}")
        clf_dict = joblib.load(self.clf_path)
        self.classifier = clf_dict["model"] if isinstance(clf_dict, dict) else clf_dict
        self.clf_label = clf_dict.get("model_label", "Champion Classifier") if isinstance(clf_dict, dict) else "Champion Classifier"
        self.clf_feature_names = clf_dict.get("feature_names", MODEL_FEATURE_CONTRACT) if isinstance(clf_dict, dict) else MODEL_FEATURE_CONTRACT
        
        logger.info(f"Loading champion regressor from {self.reg_path}")
        reg_dict = joblib.load(self.reg_path)
        self.regressor = reg_dict["model"] if isinstance(reg_dict, dict) else reg_dict
        self.reg_label = reg_dict.get("model_label", "Champion Regressor") if isinstance(reg_dict, dict) else "Champion Regressor"
        
        self.model_version = f"{self.clf_label} / {self.reg_label} (Phase 3 Production)"

    def predict_game(
        self,
        home_team: str,
        away_team: str,
        game_date: str,
        game_id: Optional[str] = None,
        include_features: bool = False,
        persist: bool = False
    ) -> GamePredictionResponse:
        """
        Predicts win probability and point margin for any arbitrary NBA matchup.
        If persist=True, saves prediction record to the PredictionRepository.
        """
        home_info = normalize_team(home_team)
        away_info = normalize_team(away_team)
        if home_info["id"] == away_info["id"]:
            raise ValueError("Home team and away team must be distinct NBA teams.")
            
        date_str = str(game_date)[:10]
        
        # 1. Generate strictly pregame feature vector
        features_df = self.feature_service.generate_pregame_feature_vector(
            home_team_identifier=home_info["id"],
            away_team_identifier=away_info["id"],
            target_game_date=date_str
        )
        
        # 2. Validate input schema contract
        if list(features_df.columns) != self.clf_feature_names:
            raise ValueError(
                f"Feature contract mismatch! Expected {len(self.clf_feature_names)} columns, "
                f"got {len(features_df.columns)}."
            )
            
        # 3. Model Inference
        probas = self.classifier.predict_proba(features_df)
        p_home_win = float(probas[0, 1])
        p_away_win = float(1.0 - p_home_win)
        
        pred_margin = float(self.regressor.predict(features_df)[0])
        
        feat_dict = features_df.iloc[0].to_dict()
        feature_hash = compute_feature_hash(feat_dict)
        feature_ts = datetime.utcnow().isoformat() + "Z"
        
        prediction_id = None
        if persist:
            record = PredictionRecord(
                game_id=game_id,
                game_date=date_str,
                home_team=home_info["name"],
                away_team=away_info["name"],
                home_team_id=home_info["id"],
                away_team_id=away_info["id"],
                model_version=self.model_version,
                classifier_model_version=self.clf_label,
                regressor_model_version=self.reg_label,
                home_win_probability=p_home_win,
                away_win_probability=p_away_win,
                predicted_home_margin=pred_margin,
                feature_schema_version="v1",
                feature_snapshot_hash=feature_hash,
                features_json=json.dumps(feat_dict),
                status="pending"
            )
            saved_record = self.repository.save_prediction(record)
            prediction_id = saved_record.prediction_id

        return GamePredictionResponse(
            prediction_id=prediction_id,
            game_id=game_id,
            game_date=date_str,
            home_team=home_info["name"],
            away_team=away_info["name"],
            home_team_id=home_info["id"],
            away_team_id=away_info["id"],
            home_win_probability=p_home_win,
            away_win_probability=p_away_win,
            predicted_home_margin=pred_margin,
            predicted_margin=pred_margin,
            model_version=self.model_version,
            classifier_name=self.clf_label,
            regressor_name=self.reg_label,
            feature_schema_version="v1",
            feature_snapshot_hash=feature_hash,
            feature_timestamp=feature_ts,
            features=feat_dict if include_features else None
        )

    def predict_by_game_num(
        self,
        game_num: int,
        include_features: bool = False,
        persist: bool = False
    ) -> GamePredictionResponse:
        """Looks up a game from the 2026-27 schedule by game number and generates its prediction."""
        game_info = self.schedule_service.get_game_by_num(game_num)
        if not game_info:
            raise ValueError(f"Game number {game_num} not found in the 2026-27 official schedule.")
            
        return self.predict_game(
            home_team=game_info["home_team_id"],
            away_team=game_info["away_team_id"],
            game_date=game_info["game_date"],
            game_id=str(game_info["game_num"]),
            include_features=include_features,
            persist=persist
        )

    def predict_lakers_next(
        self,
        as_of_date: Optional[str] = None,
        include_features: bool = False,
        persist: bool = False
    ) -> LakersGamePredictionResponse:
        """
        Finds the next unplayed Lakers game on the 2026-27 schedule and returns predictions
        explicitly framed from the Lakers' perspective (home or away).
        """
        next_game = self.schedule_service.get_next_lakers_game(as_of_date=as_of_date)
        if not next_game:
            raise ValueError(f"No upcoming Lakers games found on or after {as_of_date or '2026-10-20'}.")
            
        is_home = (next_game["home_team_id"] == LAKERS_TEAM_ID)
        opponent = next_game["away_team"] if is_home else next_game["home_team"]
        
        base_pred = self.predict_game(
            home_team=next_game["home_team_id"],
            away_team=next_game["away_team_id"],
            game_date=next_game["game_date"],
            game_id=str(next_game["game_num"]),
            include_features=include_features,
            persist=persist
        )
        
        if is_home:
            lakers_win_prob = base_pred.home_win_probability
            opponent_win_prob = base_pred.away_win_probability
            lakers_margin = base_pred.predicted_home_margin
            matchup_str = f"{opponent} at Los Angeles Lakers"
        else:
            lakers_win_prob = base_pred.away_win_probability
            opponent_win_prob = base_pred.home_win_probability
            lakers_margin = -base_pred.predicted_home_margin
            matchup_str = f"Los Angeles Lakers at {opponent}"
            
        return LakersGamePredictionResponse(
            prediction_id=base_pred.prediction_id,
            game_id=str(next_game["game_num"]),
            game_date=next_game["game_date"],
            matchup=matchup_str,
            is_lakers_home=is_home,
            opponent_team=opponent,
            lakers_win_probability=lakers_win_prob,
            opponent_win_probability=opponent_win_prob,
            predicted_lakers_margin=lakers_margin,
            home_team=next_game["home_team"],
            away_team=next_game["away_team"],
            model_version=self.model_version,
            feature_schema_version="v1",
            feature_snapshot_hash=base_pred.feature_snapshot_hash,
            feature_timestamp=base_pred.feature_timestamp
        )
