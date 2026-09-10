"""
Pydantic Schemas and Data Contracts for Lakers in 5 Inference & Monitoring Service.
"""

from typing import Optional, Dict, Any, List
from datetime import date, datetime
from pydantic import BaseModel, Field

class PlayerAvailability(BaseModel):
    """
    Extensible schema for future injury and player availability context.
    Currently used as a structured contract for downstream news/availability layers.
    """
    player_id: str
    player_name: Optional[str] = None
    status: str = Field(description="Availability status e.g. ACTIVE, OUT, QUESTIONABLE, PROBABLE")
    minutes_restriction: Optional[float] = None
    source: str = "OFFICIAL_INJURY_REPORT"
    retrieved_at: Optional[datetime] = None

class GamePredictionRequest(BaseModel):
    """
    Request model for predicting an NBA game outcome.
    """
    home_team: str = Field(description="Home team name, code (e.g. LAL, GSW), or ID")
    away_team: str = Field(description="Away team name, code (e.g. LAL, GSW), or ID")
    game_date: date = Field(description="Target game date (YYYY-MM-DD)")
    game_id: Optional[str] = Field(None, description="Optional official game ID")
    persist: bool = Field(default=False, description="Whether to persist prediction record to the prediction store")
    player_availabilities: Optional[List[PlayerAvailability]] = Field(
        default=None, description="Optional player availability updates"
    )

class GamePredictionResponse(BaseModel):
    """
    Standard response model for team-agnostic game prediction.
    """
    prediction_id: Optional[str] = None
    game_id: Optional[str] = None
    game_date: str
    home_team: str
    away_team: str
    home_team_id: str
    away_team_id: str
    home_win_probability: float = Field(description="Calibrated probability of home team winning (0.0 to 1.0)")
    away_win_probability: float = Field(description="Calibrated probability of away team winning (0.0 to 1.0)")
    predicted_home_margin: float = Field(description="Predicted point margin from home team perspective (homeScore - awayScore)")
    model_version: str
    classifier_name: str
    regressor_name: str
    feature_schema_version: str = "v1"
    feature_snapshot_hash: str
    feature_timestamp: str
    features: Optional[Dict[str, Optional[float]]] = Field(
        default=None, description="Raw pregame feature vector used for prediction"
    )

class LakersGamePredictionResponse(BaseModel):
    """
    Lakers-specific response model interpreting probabilities and margin from the Lakers' perspective.
    """
    prediction_id: Optional[str] = None
    game_id: Optional[str] = None
    game_date: str
    matchup: str
    is_lakers_home: bool
    opponent_team: str
    lakers_win_probability: float
    opponent_win_probability: float
    predicted_lakers_margin: float = Field(
        description="Predicted margin from Lakers perspective (positive = Lakers win by X, negative = Lakers lose by X)"
    )
    home_team: str
    away_team: str
    model_version: str
    feature_schema_version: str = "v1"
    feature_snapshot_hash: str
    feature_timestamp: str

class ScheduledGame(BaseModel):
    """
    Represents an official scheduled game in the 2026-27 schedule.
    """
    game_num: int
    game_date: str
    home_team: str
    away_team: str
    home_team_id: str
    away_team_id: str
    game_time: Optional[str] = None
    is_lakers_game: bool = False

# Monitoring Endpoint Schemas

class HealthReportResponse(BaseModel):
    status: str
    window: str
    sample_count: int
    evaluated_at: str
    reasons: List[str]
    performance: Dict[str, Any]
    feature_drift: Dict[str, Any]
    prediction_distribution: Dict[str, Any]

class RetrainingDecisionResponse(BaseModel):
    decision: str
    sample_count: int
    min_sample_threshold: int
    reasons: List[str]
    metrics: Optional[Dict[str, Any]] = None
    evaluated_at: str
    is_automatic_retrain: bool = False
