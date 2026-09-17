"""
FastAPI Serving Layer for Lakers in 5 Production Inference & Monitoring.
Exposes REST endpoints for game predictions, schedule lookup, model performance tracking,
drift detection, model health diagnostic, and retraining advisory decisions.
"""

import os
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.inference.schemas import (
    GamePredictionRequest,
    GamePredictionResponse,
    LakersGamePredictionResponse,
    ScheduledGame,
    HealthReportResponse,
    RetrainingDecisionResponse,
)
from src.inference.schedule_service import ScheduleService, normalize_team
from src.inference.predictor import GamePredictor
from src.monitoring.repository import PredictionRepository
from src.monitoring.metrics import MonitoringMetricsService
from src.monitoring.drift import DataDriftDetector
from src.monitoring.health import ModelHealthService, RetrainingDecisionEngine
from src.monitoring.store import PredictionRecord
from src.utils.logging import logger

app = FastAPI(
    title="Lakers in 5 — Production Inference & Monitoring API",
    description="Deterministic ML prediction, monitoring, and health API for upcoming NBA and Los Angeles Lakers games.",
    version="1.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service singletons
_predictor: Optional[GamePredictor] = None
_schedule_service: Optional[ScheduleService] = None
_repository: Optional[PredictionRepository] = None
_metrics_service: Optional[MonitoringMetricsService] = None
_drift_detector: Optional[DataDriftDetector] = None
_health_service: Optional[ModelHealthService] = None
_retrain_engine: Optional[RetrainingDecisionEngine] = None

def get_repository() -> PredictionRepository:
    global _repository
    if _repository is None:
        _repository = PredictionRepository()
    return _repository

def get_predictor() -> GamePredictor:
    global _predictor
    if _predictor is None:
        _predictor = GamePredictor(
            repository=get_repository(),
            schedule_service=get_schedule_service()
        )
    return _predictor

def get_schedule_service() -> ScheduleService:
    global _schedule_service
    if _schedule_service is None:
        _schedule_service = ScheduleService()
    return _schedule_service

def get_metrics_service() -> MonitoringMetricsService:
    global _metrics_service
    if _metrics_service is None:
        _metrics_service = MonitoringMetricsService(repository=get_repository())
    return _metrics_service

def get_drift_detector() -> DataDriftDetector:
    global _drift_detector
    if _drift_detector is None:
        _drift_detector = DataDriftDetector(repository=get_repository())
    return _drift_detector

def get_health_service() -> ModelHealthService:
    global _health_service
    if _health_service is None:
        _health_service = ModelHealthService(
            repository=get_repository(),
            metrics_service=get_metrics_service(),
            drift_detector=get_drift_detector()
        )
    return _health_service

def get_retrain_engine() -> RetrainingDecisionEngine:
    global _retrain_engine
    if _retrain_engine is None:
        _retrain_engine = RetrainingDecisionEngine(
            repository=get_repository(),
            health_service=get_health_service()
        )
    return _retrain_engine


@app.on_event("startup")
def startup_warmup():
    """Pre-warms champion models, DuckDB lakehouse, and schedule service on server boot."""
    try:
        logger.info("Pre-warming production inference predictor and schedule service...")
        get_predictor()
        get_schedule_service().load_schedule()
        logger.info("FastAPI service startup pre-warming completed successfully.")
    except Exception as e:
        logger.warning(f"Startup pre-warming encountered notice (non-fatal): {e}")


@app.get("/health", summary="Service Health Check")
def health_check():
    predictor = get_predictor()
    return {
        "status": "healthy",
        "service": "Lakers in 5 Production Inference Service",
        "model_version": predictor.model_version,
        "classifier": predictor.clf_label,
        "regressor": predictor.reg_label,
    }


@app.post("/predict", response_model=GamePredictionResponse, summary="Predict Game Outcome")
def predict_game_endpoint(request: GamePredictionRequest):
    """
    Generates pregame win probability and predicted point margin for an official 2026-27 NBA matchup.
    Validates team identifiers and ensures the matchup exists on the official schedule.
    """
    # 1. Team Canonicalization & Distinctness Validation
    try:
        home_info = normalize_team(request.home_team)
        away_info = normalize_team(request.away_team)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))

    if home_info["id"] == away_info["id"]:
        raise HTTPException(
            status_code=400,
            detail="Home team and away team must be distinct NBA teams."
        )

    # 2. Schedule-Backed Validation
    schedule_service = get_schedule_service()
    scheduled_game = schedule_service.find_game(request.home_team, request.away_team, str(request.game_date))
    if not scheduled_game:
        raise HTTPException(
            status_code=400,
            detail=f"No scheduled 2026-27 game exists for {home_info['code']} vs {away_info['code']} on {request.game_date}."
        )

    try:
        predictor = get_predictor()
        game_id_str = str(scheduled_game["game_num"]) if scheduled_game.get("game_num") is not None else None
        response = predictor.predict_game(
            home_team=home_info["name"],
            away_team=away_info["name"],
            game_date=str(request.game_date),
            game_id=game_id_str,
            include_features=False,
            persist=request.persist
        )
        return response
    except ValueError as ve:
        logger.warning(f"Validation error for matchup prediction: {ve}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Prediction failed for {request.away_team} at {request.home_team}: {e}")
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/predict/lakers/next", response_model=LakersGamePredictionResponse, summary="Predict Next Lakers Game")
def predict_lakers_next_endpoint(
    as_of_date: Optional[str] = Query(None, description="Reference ISO date (YYYY-MM-DD)"),
    persist: bool = Query(False, description="Persist prediction record")
):
    """
    Finds the next upcoming Lakers game on the schedule and returns predictions
    framed from the Lakers' perspective (home or away).
    """
    try:
        predictor = get_predictor()
        return predictor.predict_lakers_next(as_of_date=as_of_date, persist=persist)
    except Exception as e:
        logger.error(f"Lakers next prediction failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/predict/{game_id}", response_model=GamePredictionResponse, summary="Predict Scheduled Game by Number")
def predict_game_by_id_endpoint(
    game_id: int,
    persist: bool = Query(False, description="Persist prediction record")
):
    """
    Looks up a scheduled game by its official schedule game number and returns predictions.
    """
    try:
        predictor = get_predictor()
        return predictor.predict_by_game_num(game_num=game_id, persist=persist)
    except Exception as e:
        logger.error(f"Prediction by game_id {game_id} failed: {e}")
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/schedule/matchup", response_model=List[ScheduledGame], summary="Query Scheduled Games for Matchup")
def get_matchup_schedule_endpoint(
    home_team: str = Query(..., description="Home team identifier (e.g. LAL, Lakers)"),
    away_team: str = Query(..., description="Away team identifier (e.g. GSW, Warriors)")
):
    """
    Queries all official 2026-27 scheduled games between the specified home and away teams.
    """
    try:
        schedule = get_schedule_service()
        games = schedule.get_matchup_games(home_team_str=home_team, away_team_str=away_team)
        return games
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/schedule/2026-27", response_model=List[ScheduledGame], summary="Query 2026-27 Schedule")
def get_schedule_endpoint(
    team: Optional[str] = Query(None, description="Optional team filter (e.g. LAL, Warriors)"),
    as_of_date: Optional[str] = Query(None, description="Filter games on or after this ISO date"),
    limit: int = Query(20, ge=1, le=100, description="Max games to return")
):
    """
    Queries scheduled games for the 2026-27 NBA regular season.
    """
    try:
        schedule = get_schedule_service()
        if team:
            games = schedule.get_games_for_team(team_str=team, as_of_date=as_of_date)
        else:
            df = schedule.load_schedule()
            if as_of_date:
                df = df[df["game_date"] >= as_of_date]
            games = df.to_dict(orient="records")
            
        return games[:limit]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# MONITORING ENDPOINTS
# ==============================================================================

@app.get("/monitoring/health", response_model=HealthReportResponse, summary="Get Model Health Diagnostic")
def get_model_health_endpoint(window: str = Query("30d", pattern="^(7d|30d|season|all_time)$")):
    """
    Returns multi-dimensional production model health across performance, calibration, and drift.
    """
    try:
        health_svc = get_health_service()
        return health_svc.evaluate_health(window=window)
    except Exception as e:
        logger.error(f"Health check endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/performance", summary="Get Rolling Performance Metrics")
def get_performance_endpoint(
    window: str = Query("30d", pattern="^(7d|30d|season|all_time)$"),
    team: Optional[str] = Query(None, description="Optional team filter (e.g. Los Angeles Lakers)")
):
    """
    Calculates rolling classification (Log Loss, Brier, Accuracy, ROC-AUC, ECE) and regression (MAE, RMSE, Bias) metrics.
    """
    try:
        metrics_svc = get_metrics_service()
        return metrics_svc.compute_performance_metrics(window=window, team=team)
    except Exception as e:
        logger.error(f"Performance endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/calibration", summary="Get Decile Probability Calibration")
def get_calibration_endpoint(
    window: str = Query("season", pattern="^(7d|30d|season|all_time)$"),
    n_bins: int = Query(10, ge=5, le=20)
):
    """
    Generates decile calibration curve data for completed predictions.
    """
    try:
        metrics_svc = get_metrics_service()
        cal_df = metrics_svc.compute_calibration_table(window=window, n_bins=n_bins)
        return cal_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Calibration endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/drift", summary="Get Feature & Output Drift Metrics")
def get_drift_endpoint(window: str = Query("30d", pattern="^(7d|30d|season|all_time)$")):
    """
    Computes feature PSI, mean/std shift, missing rate shift, and output distribution metrics.
    """
    try:
        drift_detector = get_drift_detector()
        feature_drift = drift_detector.compute_feature_drift(window=window)
        pred_drift = drift_detector.compute_prediction_drift(window=window)
        return {
            "window": window,
            "feature_drift": feature_drift,
            "prediction_drift": pred_drift
        }
    except Exception as e:
        logger.error(f"Drift endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/predictions", summary="Query Persisted Predictions")
def get_predictions_endpoint(
    status: Optional[str] = Query(None, description="Filter status: pending | completed | cancelled"),
    team: Optional[str] = Query(None, description="Filter by team name"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    Queries prediction records from the persistent prediction store.
    """
    try:
        repo = get_repository()
        records = repo.get_predictions(status=status, team=team, limit=limit, offset=offset)
        return [r.model_dump() for r in records]
    except Exception as e:
        logger.error(f"Predictions query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/monitoring/retraining-decision", response_model=RetrainingDecisionResponse, summary="Get Retraining Recommendation")
def get_retraining_decision_endpoint(window: str = Query("season", pattern="^(7d|30d|season|all_time)$")):
    """
    Evaluates whether retraining should be recommended based on sample size, performance degradation, and drift.
    """
    try:
        engine = get_retrain_engine()
        return engine.evaluate_retraining_decision(window=window)
    except Exception as e:
        logger.error(f"Retraining decision endpoint failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==============================================================================
# FRONTEND STATIC ASSETS MOUNT
# ==============================================================================
frontend_dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")
if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")

