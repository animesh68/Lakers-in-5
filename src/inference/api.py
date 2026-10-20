"""
FastAPI Serving Layer for Lakers in 5 Production Inference & Monitoring.
Exposes REST endpoints for game predictions, schedule lookup, model performance tracking,
drift detection, model health diagnostic, and retraining advisory decisions.
"""

import os
import uuid
import time
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from fastapi import FastAPI, HTTPException, Query, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, FileResponse, HTMLResponse
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.staticfiles import StaticFiles

from src.inference.schemas import (
    GamePredictionRequest,
    GamePredictionResponse,
    LakersGamePredictionResponse,
    ScheduledGame,
    HealthReportResponse,
    RetrainingDecisionResponse,
    PlayerPredictionRequest,
    PlayerPredictionResponse,
)
from src.inference.schedule_service import ScheduleService, normalize_team
from src.inference.predictor import GamePredictor
from src.inference.player_predictor import PlayerPredictor
from src.monitoring.repository import PredictionRepository
from src.monitoring.metrics import MonitoringMetricsService
from src.monitoring.drift import DataDriftDetector
from src.monitoring.health import ModelHealthService, RetrainingDecisionEngine
from src.monitoring.collector import metrics_collector
from src.monitoring.store import PredictionRecord
from src.utils.logging import logger, log_event, set_request_id, clear_request_id, get_request_id

app = FastAPI(
    title="Lakers in 5 — Production Inference & Monitoring API",
    description="Deterministic ML prediction, monitoring, and health API for upcoming NBA and Los Angeles Lakers games.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class RequestIDAndMetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware that attaches/propagates correlation IDs, records Prometheus HTTP metrics,
    and logs request lifecycle events.
    """
    async def dispatch(self, request: Request, call_next):
        # 1. Request Correlation ID
        req_id = request.headers.get("X-Request-ID") or request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        set_request_id(req_id)

        t0 = time.time()
        method = request.method
        path = request.url.path

        # Avoid logging metrics scrape or favicon at INFO to reduce container log spam
        is_diagnostic = path in ["/metrics", "/favicon.ico"]
        if not is_diagnostic:
            log_event(logger, "request_started", level=10, method=method, path=path, request_id=req_id)

        try:
            response = await call_next(request)
            duration_sec = time.time() - t0
            status_code = response.status_code

            # Inject header
            response.headers["X-Request-ID"] = req_id

            # Update Prometheus Metrics
            status_label = f"{status_code // 100}xx"
            metrics_collector.inc_counter("http_requests_total", labels={"method": method, "path": path, "status": status_label})
            metrics_collector.observe_histogram("http_request_duration_seconds", duration_sec, labels={"method": method, "path": path})

            if status_code >= 400:
                metrics_collector.inc_counter("http_errors_total", labels={"method": method, "path": path, "status_code": str(status_code)})

            if not is_diagnostic:
                level = 20 if status_code < 400 else (30 if status_code < 500 else 40)
                log_event(
                    logger,
                    "request_completed",
                    level=level,
                    method=method,
                    path=path,
                    status_code=status_code,
                    latency_ms=round(duration_sec * 1000, 2),
                    request_id=req_id
                )
            return response
        except Exception as e:
            duration_sec = time.time() - t0
            metrics_collector.inc_counter("http_requests_total", labels={"method": method, "path": path, "status": "5xx"})
            metrics_collector.inc_counter("http_errors_total", labels={"method": method, "path": path, "status_code": "500"})
            log_event(
                logger,
                "request_failed",
                level=40,
                method=method,
                path=path,
                error=str(e),
                latency_ms=round(duration_sec * 1000, 2),
                request_id=req_id
            )
            return JSONResponse(
                status_code=500,
                content={"error_type": "INTERNAL_ERROR", "detail": "An internal server error occurred.", "request_id": req_id},
                headers={"X-Request-ID": req_id}
            )
        finally:
            clear_request_id()


app.add_middleware(RequestIDAndMetricsMiddleware)


# Global service singletons
_predictor: Optional[GamePredictor] = None
_player_predictor: Optional[PlayerPredictor] = None
_schedule_service: Optional[ScheduleService] = None
_repository: Optional[PredictionRepository] = None
_metrics_service: Optional[MonitoringMetricsService] = None
_drift_detector: Optional[DataDriftDetector] = None
_health_service: Optional[ModelHealthService] = None
_retrain_engine: Optional[RetrainingDecisionEngine] = None

def get_player_predictor() -> PlayerPredictor:
    global _player_predictor
    if _player_predictor is None:
        _player_predictor = PlayerPredictor(schedule_service=get_schedule_service())
    return _player_predictor

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
        log_event(logger, "application_started", message="Pre-warming production inference predictor and schedule service...")
        get_predictor()
        get_schedule_service().load_schedule()
        log_event(logger, "application_ready", message="FastAPI service startup pre-warming completed successfully.")
    except Exception as e:
        logger.warning(f"Startup pre-warming encountered notice (non-fatal): {e}")


def get_git_commit() -> str:
    """Returns safe short commit hash from environment or git fallback."""
    commit = os.environ.get("RENDER_GIT_COMMIT") or os.environ.get("GIT_COMMIT")
    if commit:
        return commit[:8]
    try:
        import subprocess
        res = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=2
        )
        if res.returncode == 0:
            return res.stdout.strip()
    except Exception:
        pass
    return "unknown"


@app.get("/health", summary="Liveness Probe")
def health_check():
    """Lightweight liveness probe answering 'is the process alive?' with zero heavy I/O."""
    health_svc = get_health_service()
    data = health_svc.check_liveness()
    data["git_commit"] = get_git_commit()
    data["app_version"] = app.version
    return data


@app.get("/health/ready", summary="Readiness Probe")
def readiness_check():
    """
    Serving readiness probe. Verifies that critical production components and models are ready.
    Returns 200 if ready, 503 if unready (e.g. production model artifact missing).
    """
    health_svc = get_health_service()
    is_ready, report = health_svc.check_readiness()

    # Enrich with safe deployment diagnostics
    report["git_commit"] = get_git_commit()
    report["app_version"] = app.version
    report["season"] = "2026-27"
    try:
        player_pred = get_player_predictor()
        report["roster"] = player_pred.roster_service.get_roster_diagnostics()
    except Exception as e:
        report["roster"] = {"status": "unverified_fallback", "error": str(e)}

    if not is_ready:
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content=report)
    return report


@app.get("/health/models", summary="Model Diagnostics & Integrity")
def model_health_check():
    """
    Detailed model artifact integrity and version diagnostics for Production (v1.0) and Shadow (v1.1-c1).
    """
    health_svc = get_health_service()
    return health_svc.check_model_health()


@app.get("/health/version", summary="Safe Build & Roster Diagnostics")
def version_diagnostics_endpoint():
    """
    Exposes safe, non-sensitive deployment observability: build revision,
    model versions, schedule season, and roster source validation status.
    """
    try:
        player_pred = get_player_predictor()
        roster_diag = player_pred.roster_service.get_roster_diagnostics()
    except Exception as e:
        roster_diag = {"status": "error", "error": str(e)}

    return {
        "status": "healthy",
        "app_version": app.version,
        "git_commit": get_git_commit(),
        "season": "2026-27",
        "models": {
            "game_prediction": "v1.0",
            "player_performance": "PlayerSuite-v1.0",
            "shadow": "PlayerSuite-v1.1-c1-shadow"
        },
        "roster": roster_diag,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }



@app.get("/metrics", summary="Prometheus Metrics Scrape Endpoint")
def prometheus_metrics():
    """Exposes real-time application metrics in standard Prometheus exposition format."""
    text_content = metrics_collector.export_prometheus_text()
    return PlainTextResponse(content=text_content, media_type="text/plain; version=0.0.4; charset=utf-8")


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


@app.post("/predict/players", response_model=PlayerPredictionResponse, summary="Predict Individual Player Performance")
def predict_players_endpoint(request: PlayerPredictionRequest):
    """
    Predicts expected minutes, points, rebounds, and assists for active rotation players
    in an official scheduled 2026-27 NBA matchup.
    """
    try:
        player_predictor = get_player_predictor()
        return player_predictor.predict_scheduled_game_players(
            home_team_identifier=request.home_team,
            away_team_identifier=request.away_team,
            game_date_str=str(request.game_date)
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Player prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/predict/{game_id}/players", response_model=PlayerPredictionResponse, summary="Predict Players for Scheduled Game Number")
def predict_players_by_game_num_endpoint(game_id: int):
    """
    Looks up a scheduled 2026-27 game by official game number and predicts individual player performance.
    """
    schedule_service = get_schedule_service()
    game = schedule_service.get_game_by_num(game_id)
    if not game:
        raise HTTPException(status_code=404, detail=f"Scheduled game #{game_id} not found in official 2026-27 schedule.")
    
    try:
        player_predictor = get_player_predictor()
        return player_predictor.predict_scheduled_game_players(
            home_team_identifier=game.get("home_team_code") or game.get("home_team"),
            away_team_identifier=game.get("away_team_code") or game.get("away_team"),
            game_date_str=game["game_date"]
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        logger.error(f"Player prediction for game #{game_id} failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
# FRONTEND STATIC ASSETS & SPA ROUTE MOUNT
# ==============================================================================
frontend_dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist")

@app.get("/engine", include_in_schema=False)
@app.get("/engine/{full_path:path}", include_in_schema=False)
async def serve_engine_spa():
    index_file = os.path.join(frontend_dist_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return HTMLResponse("<!DOCTYPE html><html><body><h1>Lakers in 5 — Engine</h1><p>Frontend build in progress.</p></body></html>", status_code=200)

if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="frontend")


