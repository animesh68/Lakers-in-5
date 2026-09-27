"""
Production Player Performance Prediction Service for Phase 8.
Predicts individual expected minutes, points, rebounds, and assists for eligible rotation players
in official scheduled 2026-27 NBA games with zero temporal leakage.
"""

import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
import pandas as pd
import duckdb

from src.inference.schemas import PlayerPredictionRequest, PlayerPredictionResponse, PlayerProjectionItem
from src.inference.schedule_service import ScheduleService, normalize_team
from src.inference.roster_service import RosterService
from src.features.player_prediction_features import PlayerFeatureEngine
from src.models.player_models import PlayerPerformanceSuite
from src.lake.duckdb_client import DuckDBClient
from src.utils.logging import logger


class PlayerPredictor:
    """
    Inference service for player-level box score predictions.
    Coordinates schedule verification, roster universe resolution, pregame feature extraction,
    and model inference across the 4 dedicated target models.
    """
    def __init__(
        self,
        models_dir: Optional[str] = None,
        schedule_service: Optional[ScheduleService] = None,
        roster_service: Optional[RosterService] = None,
        feature_engine: Optional[PlayerFeatureEngine] = None,
        duckdb_client: Optional[DuckDBClient] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = models_dir or os.path.join(base_dir, "models")
        self.schedule_service = schedule_service or ScheduleService()
        self.roster_service = roster_service or RosterService()
        self.duckdb_client = duckdb_client or DuckDBClient()
        self.feature_engine = feature_engine or PlayerFeatureEngine(duckdb_conn=self.duckdb_client.conn, roster_service=self.roster_service)
        
        self._model_suite: Optional[PlayerPerformanceSuite] = None

    def _get_model_suite(self) -> PlayerPerformanceSuite:
        """Loads and caches the player model suite."""
        if self._model_suite is not None:
            return self._model_suite
        logger.info(f"Loading player performance champion models from {self.models_dir}...")
        self._model_suite = PlayerPerformanceSuite.load_artifacts(self.models_dir)
        return self._model_suite

    def predict_scheduled_game_players(
        self,
        home_team_identifier: str,
        away_team_identifier: str,
        game_date_str: str,
        max_players_per_team: int = 10
    ) -> PlayerPredictionResponse:
        """
        Executes player performance prediction for an official scheduled 2026-27 game.
        """
        # 1. Normalize Team Identifiers
        home_info = normalize_team(home_team_identifier)
        away_info = normalize_team(away_team_identifier)

        if home_info["id"] == away_info["id"]:
            raise ValueError(f"Home team and Away team must be distinct: got '{home_team_identifier}' vs '{away_team_identifier}'")

        # 2. Strict Schedule-Backed Verification
        scheduled_game = self.schedule_service.find_game(home_info["code"], away_info["code"], str(game_date_str))
        if not scheduled_game:
            # Check reverse home/away
            reverse_game = self.schedule_service.find_game(away_info["code"], home_info["code"], str(game_date_str))
            if reverse_game:
                raise ValueError(
                    f"Matchup inversion: {away_info['name']} hosts {home_info['name']} on {game_date_str}, "
                    f"not {home_info['name']} hosting {away_info['name']}."
                )
            raise ValueError(
                f"No official 2026-27 regular season game scheduled between {home_info['name']} "
                f"and {away_info['name']} on {game_date_str}."
            )

        game_id = f"{scheduled_game.get('game_num', 'GAME')}_{home_info['code']}_{away_info['code']}_{game_date_str}"

        # 3. Resolve Pregame Active Rotation Universes
        home_roster = self.roster_service.get_active_roster_universe(home_info["code"], str(game_date_str), max_players=max_players_per_team)
        away_roster = self.roster_service.get_active_roster_universe(away_info["code"], str(game_date_str), max_players=max_players_per_team)

        suite = self._get_model_suite()
        all_projections: List[PlayerProjectionItem] = []

        # 4. Generate Predictions for Home Team Players
        for p_meta in home_roster:
            p_id = p_meta["person_id"]
            p_name = p_meta["player_name"]
            
            feat_dict = self.feature_engine.extract_pregame_player_features(
                person_id=p_id,
                team_id=home_info["id"],
                opponent_team_id=away_info["id"],
                target_game_date=str(game_date_str),
                is_home=True,
                player_meta=p_meta
            )
            preds = suite.predict_player(feat_dict)
            
            all_projections.append(PlayerProjectionItem(
                player_id=p_id,
                player_name=p_name,
                team=home_info["name"],
                team_code=home_info["code"],
                expected_minutes=preds["expected_minutes"],
                predicted_points=preds["predicted_points"],
                predicted_rebounds=preds["predicted_rebounds"],
                predicted_assists=preds["predicted_assists"],
                is_transition_player=bool(p_meta.get("is_transition_player", False))
            ))

        # 5. Generate Predictions for Away Team Players
        for p_meta in away_roster:
            p_id = p_meta["person_id"]
            p_name = p_meta["player_name"]
            
            feat_dict = self.feature_engine.extract_pregame_player_features(
                person_id=p_id,
                team_id=away_info["id"],
                opponent_team_id=home_info["id"],
                target_game_date=str(game_date_str),
                is_home=False,
                player_meta=p_meta
            )
            preds = suite.predict_player(feat_dict)
            
            all_projections.append(PlayerProjectionItem(
                player_id=p_id,
                player_name=p_name,
                team=away_info["name"],
                team_code=away_info["code"],
                expected_minutes=preds["expected_minutes"],
                predicted_points=preds["predicted_points"],
                predicted_rebounds=preds["predicted_rebounds"],
                predicted_assists=preds["predicted_assists"],
                is_transition_player=bool(p_meta.get("is_transition_player", False))
            ))

        # Sort projections by expected minutes descending
        all_projections.sort(key=lambda x: x.expected_minutes, reverse=True)

        return PlayerPredictionResponse(
            game_id=game_id,
            game_date=str(game_date_str),
            home_team=home_info["name"],
            away_team=away_info["name"],
            players=all_projections,
            model_versions={
                "minutes": "PlayerMinutes-Ridge-v1",
                "points": "PlayerPoints-Ridge-v1",
                "rebounds": "PlayerRebounds-Ridge-v1",
                "assists": "PlayerAssists-Ridge-v1"
            },
            feature_schema_version="v1.0-player",
            prediction_timestamp=datetime.utcnow().isoformat()
        )
