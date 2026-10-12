"""
Production Player Performance Prediction Service for Phase 8.
Predicts individual expected minutes, points, rebounds, and assists for eligible rotation players
in official scheduled 2026-27 NBA games with zero temporal leakage.
"""

import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date
import pandas as pd
try:
    import duckdb
except Exception:
    duckdb = None

import time
from src.inference.schemas import PlayerPredictionRequest, PlayerPredictionResponse, PlayerProjectionItem
from src.inference.schedule_service import ScheduleService, normalize_team
from src.inference.roster_service import RosterService
from src.features.player_prediction_features import PlayerFeatureEngine
from src.models.player_models import PlayerPerformanceSuite, RoleStratifiedPointsModel
from src.monitoring.repository import PredictionRepository
from src.monitoring.store import PlayerShadowPredictionRecord
from src.monitoring.collector import metrics_collector
from src.validation.data_quality import validate_feature_vector, validate_prediction_output, FeatureContractError
from src.lake.duckdb_client import DuckDBClient
from src.utils.logging import logger, log_event


class PlayerPredictor:
    """
    Inference service for player-level box score predictions.
    Coordinates schedule verification, roster universe resolution, pregame feature extraction,
    model inference across dedicated target models, and persistent prospective shadow logging.
    """
    def __init__(
        self,
        models_dir: Optional[str] = None,
        schedule_service: Optional[ScheduleService] = None,
        roster_service: Optional[RosterService] = None,
        feature_engine: Optional[PlayerFeatureEngine] = None,
        duckdb_client: Optional[DuckDBClient] = None,
        repository: Optional[PredictionRepository] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.models_dir = models_dir or os.path.join(base_dir, "models")
        self.schedule_service = schedule_service or ScheduleService()
        self.roster_service = roster_service or RosterService()
        self.duckdb_client = duckdb_client or DuckDBClient()
        self.feature_engine = feature_engine or PlayerFeatureEngine(duckdb_conn=self.duckdb_client.conn, roster_service=self.roster_service)
        self.repository = repository or PredictionRepository()
        
        self._model_suite: Optional[PlayerPerformanceSuite] = None
        self._shadow_suite: Optional[PlayerPerformanceSuite] = None
        self.shadow_dir = os.path.join(self.models_dir, "experimental", "c1_role_stratified")

    def _get_model_suite(self, model_version: str = "prod") -> PlayerPerformanceSuite:
        """Loads and caches the player model suite (prod or c1_shadow)."""
        if model_version == "c1_shadow":
            if self._shadow_suite is not None:
                return self._shadow_suite
            if os.path.exists(self.shadow_dir):
                log_event(logger, "model_loaded", model_version="PlayerSuite-v1.1-c1-shadow", is_shadow=True)
                self._shadow_suite = PlayerPerformanceSuite.load_shadow_suite(self.shadow_dir)
                metrics_collector.inc_counter("model_load_events_total", labels={"model_name": "c1_shadow", "status": "success"})
                return self._shadow_suite
            logger.warning(f"Shadow model directory not found at {self.shadow_dir}, falling back to prod.")
            metrics_collector.inc_counter("model_load_events_total", labels={"model_name": "c1_shadow", "status": "fallback"})

        if self._model_suite is not None:
            return self._model_suite
        log_event(logger, "model_loaded", model_version="PlayerSuite-v1.0", is_shadow=False)
        self._model_suite = PlayerPerformanceSuite.load_artifacts(self.models_dir)
        metrics_collector.inc_counter("model_load_events_total", labels={"model_name": "player_suite_v1", "status": "success"})
        return self._model_suite

    def predict_scheduled_game_players(
        self,
        home_team_identifier: str,
        away_team_identifier: str,
        game_date_str: str,
        max_players_per_team: int = 15,
        model_version: str = "prod"
    ) -> PlayerPredictionResponse:
        """
        Executes player performance prediction for an official scheduled 2026-27 game.
        Defaults to production champion models. If shadow candidate is available, executes
        shadow evaluation and logs audit diffs without altering UI output.
        """
        t0 = time.time()
        log_event(
            logger,
            "prediction_started",
            home_team=home_team_identifier,
            away_team=away_team_identifier,
            game_date=game_date_str,
            model_type="player_performance"
        )

        # 1. Normalize Team Identifiers
        home_info = normalize_team(home_team_identifier)
        away_info = normalize_team(away_team_identifier)

        if home_info["id"] == away_info["id"]:
            metrics_collector.inc_counter("prediction_requests_total", labels={"model_type": "player", "status": "validation_error"})
            raise ValueError(f"Home team and Away team must be distinct: got '{home_team_identifier}' vs '{away_team_identifier}'")

        # 2. Strict Schedule-Backed Verification
        scheduled_game = self.schedule_service.find_game(home_info["code"], away_info["code"], str(game_date_str))
        if not scheduled_game:
            # Check reverse home/away
            reverse_game = self.schedule_service.find_game(away_info["code"], home_info["code"], str(game_date_str))
            if reverse_game:
                metrics_collector.inc_counter("prediction_requests_total", labels={"model_type": "player", "status": "schedule_error"})
                raise ValueError(
                    f"Matchup inversion: {away_info['name']} hosts {home_info['name']} on {game_date_str}, "
                    f"not {home_info['name']} hosting {away_info['name']}."
                )
            metrics_collector.inc_counter("prediction_requests_total", labels={"model_type": "player", "status": "schedule_error"})
            raise ValueError(
                f"No official 2026-27 regular season game scheduled between {home_info['name']} "
                f"and {away_info['name']} on {game_date_str}."
            )

        game_id = f"{scheduled_game.get('game_num', 'GAME')}_{home_info['code']}_{away_info['code']}_{game_date_str}"

        # 3. Resolve Pregame Active Rotation Universes
        home_roster = self.roster_service.get_active_roster_universe(home_info["code"], str(game_date_str), max_players=max_players_per_team)
        away_roster = self.roster_service.get_active_roster_universe(away_info["code"], str(game_date_str), max_players=max_players_per_team)

        prod_suite = self._get_model_suite(model_version="prod")
        
        # Check shadow suite availability for audit comparison
        shadow_suite = None
        if os.path.exists(self.shadow_dir):
            try:
                shadow_suite = self._get_model_suite(model_version="c1_shadow")
            except Exception as e:
                log_event(logger, "shadow_prediction_failed", level=30, error=f"Shadow suite load notice: {e}")
                metrics_collector.inc_counter("shadow_prediction_requests_total", labels={"status": "load_error"})

        active_suite = self._get_model_suite(model_version=model_version)
        all_projections: List[PlayerProjectionItem] = []
        shadow_records_to_log: List[PlayerShadowPredictionRecord] = []

        # Precompute team rolling contexts once for home and away teams
        home_team_ctx = self.feature_engine.get_team_rolling_context(home_info["id"], away_info["id"], str(game_date_str))
        away_team_ctx = self.feature_engine.get_team_rolling_context(away_info["id"], home_info["id"], str(game_date_str))

        # Build batch request specifications for all rotation players
        player_requests: List[Dict[str, Any]] = []
        for p_meta in home_roster:
            player_requests.append({
                "person_id": p_meta["person_id"],
                "team_id": home_info["id"],
                "opponent_team_id": away_info["id"],
                "team_dict": home_info,
                "opp_dict": away_info,
                "is_home": True,
                "player_meta": p_meta,
                "team_context": home_team_ctx
            })
        for p_meta in away_roster:
            player_requests.append({
                "person_id": p_meta["person_id"],
                "team_id": away_info["id"],
                "opponent_team_id": home_info["id"],
                "team_dict": away_info,
                "opp_dict": home_info,
                "is_home": False,
                "player_meta": p_meta,
                "team_context": away_team_ctx
            })

        # Batch-extract 24-feature contracts in a single vectorized DuckDB parquet query
        all_features = self.feature_engine.extract_pregame_batch_player_features(
            player_requests=player_requests,
            target_game_date=str(game_date_str)
        )

        for req, feat_dict in zip(player_requests, all_features):
            p_meta = req["player_meta"]
            p_id = p_meta["person_id"]
            p_name = p_meta["player_name"]
            team_dict = req["team_dict"]
            opp_dict = req["opp_dict"]

            # Pre-inference feature contract validation
            is_valid, feat_errs = validate_feature_vector(feat_dict)
            if not is_valid:
                log_event(logger, "feature_generation_failed", level=30, player_id=p_id, errors=feat_errs)

            # Production prediction
            prod_preds = prod_suite.predict_player(feat_dict)

            # Shadow prediction (wrapped in isolated try/except to protect production)
            shadow_preds = prod_preds
            if shadow_suite is not None:
                try:
                    shadow_preds = shadow_suite.predict_player(feat_dict)
                    metrics_collector.inc_counter("shadow_prediction_requests_total", labels={"status": "success"})
                except Exception as shadow_err:
                    log_event(logger, "shadow_prediction_failed", level=30, player_id=p_id, error=str(shadow_err))
                    metrics_collector.inc_counter("shadow_prediction_requests_total", labels={"status": "failure"})
                    shadow_preds = prod_preds

            # Determine pregame role directly without allocating DataFrame
            min_10 = feat_dict.get("player_min_avg_10", 0.0)
            usg_10 = feat_dict.get("player_usage_pct_10", 0.0)
            if min_10 >= 28.0 and usg_10 >= 0.24:
                role = "star"
            elif min_10 >= 24.0:
                role = "starter"
            else:
                role = "bench"

            diff = round(shadow_preds["predicted_points"] - prod_preds["predicted_points"], 1)
            logger.debug(f"[SHADOW AUDIT] {p_name} ({team_dict['code']}) | Role: {role} | Prod PTS: {prod_preds['predicted_points']} | Shadow PTS: {shadow_preds['predicted_points']} | Diff: {diff:+0.1f}")

            shadow_records_to_log.append(PlayerShadowPredictionRecord(
                game_id=game_id,
                game_date=str(game_date_str),
                player_id=p_id,
                player_name=p_name,
                team_id=team_dict["id"],
                team_code=team_dict["code"],
                opponent_team_id=opp_dict["id"],
                opponent_team_code=opp_dict["code"],
                production_model_version=prod_suite.model_version,
                shadow_model_version=shadow_suite.model_version if shadow_suite else "None",
                role=role,
                predicted_minutes_production=prod_preds["expected_minutes"],
                predicted_minutes_shadow=shadow_preds["expected_minutes"],
                predicted_points_production=prod_preds["predicted_points"],
                predicted_points_shadow=shadow_preds["predicted_points"],
                predicted_rebounds_production=prod_preds["predicted_rebounds"],
                predicted_rebounds_shadow=shadow_preds["predicted_rebounds"],
                predicted_assists_production=prod_preds["predicted_assists"],
                predicted_assists_shadow=shadow_preds["predicted_assists"],
                feature_contract_version="v1.1-player-role-stratified",
                prediction_status="pending"
            ))

            if active_suite is prod_suite:
                active_preds = prod_preds
            elif active_suite is shadow_suite:
                active_preds = shadow_preds
            else:
                active_preds = active_suite.predict_player(feat_dict)

            # Output domain validation
            is_out_valid, out_errs = validate_prediction_output(active_preds)
            if not is_out_valid:
                log_event(logger, "prediction_bounds_warning", level=30, player_id=p_id, warnings=out_errs)

            all_projections.append(PlayerProjectionItem(
                player_id=p_id,
                player_name=p_name,
                team=team_dict["name"],
                team_code=team_dict["code"],
                expected_minutes=active_preds["expected_minutes"],
                predicted_points=active_preds["predicted_points"],
                predicted_rebounds=active_preds["predicted_rebounds"],
                predicted_assists=active_preds["predicted_assists"],
                is_transition_player=bool(p_meta.get("is_transition_player", False))
            ))

        # Persist shadow prediction pairs idempotently
        if shadow_records_to_log:
            try:
                self.repository.save_player_shadow_predictions(shadow_records_to_log)
            except Exception as e:
                logger.warning(f"Failed to persist shadow prediction records: {e}")

        # Sort projections by expected minutes descending, then points descending, then name
        all_projections.sort(key=lambda x: (x.expected_minutes, x.predicted_points, x.player_name), reverse=True)

        latency_ms = (time.time() - t0) * 1000.0
        metrics_collector.inc_counter("prediction_requests_total", labels={"model_type": "player", "status": "success"})
        metrics_collector.observe_histogram("prediction_duration_seconds", latency_ms / 1000.0, labels={"model_type": "player"})

        log_event(
            logger,
            "prediction_completed",
            game_id=game_id,
            players_count=len(all_projections),
            latency_ms=round(latency_ms, 2),
            model_version=active_suite.model_version,
            status="success"
        )

        return PlayerPredictionResponse(
            game_id=game_id,
            game_date=str(game_date_str),
            home_team=home_info["name"],
            away_team=away_info["name"],
            players=all_projections,
            model_versions={
                "minutes": active_suite.model_version,
                "points": "PlayerPoints-RoleStratified-Ridge-v1.1" if active_suite.is_shadow else "PlayerPoints-Ridge-v1",
                "rebounds": active_suite.model_version,
                "assists": active_suite.model_version
            },
            feature_schema_version=active_suite.schema_version,
            prediction_timestamp=datetime.utcnow().isoformat()
        )
