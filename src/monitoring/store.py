"""
Prediction Store Data Models and Database Schema for Lakers in 5.
Defines both Pydantic datacontracts and SQLAlchemy ORM models for prediction persistence.
"""

from datetime import datetime, date
from typing import Optional, Dict, Any
import uuid
import json

from pydantic import BaseModel, Field
from sqlalchemy import (
    Column,
    String,
    Float,
    Integer,
    Date,
    DateTime,
    Text,
    Index,
    MetaData,
    Table,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class PredictionRecord(BaseModel):
    """
    Pydantic schema representing a persistent prediction record.
    """
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: Optional[str] = None
    game_date: str  # YYYY-MM-DD
    home_team: str
    away_team: str
    home_team_id: str
    away_team_id: str
    
    prediction_created_at: datetime = Field(default_factory=datetime.utcnow)
    
    model_version: str
    classifier_model_version: str
    regressor_model_version: str
    
    home_win_probability: float
    away_win_probability: float
    predicted_home_margin: float
    
    feature_schema_version: str = "v1"
    feature_snapshot_hash: str
    features_json: Optional[str] = None  # Optional raw JSON string of input features
    
    status: str = "pending"  # pending | completed | cancelled
    
    actual_home_score: Optional[int] = None
    actual_away_score: Optional[int] = None
    actual_home_win: Optional[int] = None
    actual_home_margin: Optional[float] = None
    outcome_recorded_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)




class PredictionORM(Base):
    """
    SQLAlchemy ORM table definition for PostgreSQL / SQLite prediction store.
    """
    __tablename__ = "predictions"

    prediction_id = Column(String(64), primary_key=True, index=True)
    game_id = Column(String(64), index=True, nullable=True)
    game_date = Column(Date, index=True, nullable=False)
    home_team = Column(String(100), nullable=False)
    away_team = Column(String(100), nullable=False)
    home_team_id = Column(String(32), nullable=False)
    away_team_id = Column(String(32), nullable=False)

    prediction_created_at = Column(DateTime, index=True, nullable=False, default=datetime.utcnow)

    model_version = Column(String(128), index=True, nullable=False)
    classifier_model_version = Column(String(128), nullable=False)
    regressor_model_version = Column(String(128), nullable=False)

    home_win_probability = Column(Float, nullable=False)
    away_win_probability = Column(Float, nullable=False)
    predicted_home_margin = Column(Float, nullable=False)

    feature_schema_version = Column(String(32), nullable=False, default="v1")
    feature_snapshot_hash = Column(String(64), index=True, nullable=False)
    features_json = Column(Text, nullable=True)

    status = Column(String(32), index=True, nullable=False, default="pending")

    actual_home_score = Column(Integer, nullable=True)
    actual_away_score = Column(Integer, nullable=True)
    actual_home_win = Column(Integer, nullable=True)
    actual_home_margin = Column(Float, nullable=True)
    outcome_recorded_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_predictions_game_date_status", "game_date", "status"),
        Index("idx_predictions_created_model", "prediction_created_at", "model_version"),
    )


class PlayerShadowPredictionRecord(BaseModel):
    """
    Pydantic schema representing an immutable pregame paired player prediction record
    (Production Pooled vs C1 Role-Stratified Shadow).
    """
    prediction_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    game_id: str
    game_date: str  # YYYY-MM-DD
    player_id: str
    player_name: Optional[str] = "Unknown"
    team_id: Optional[str] = None
    team_code: Optional[str] = None
    opponent_team_id: Optional[str] = None
    opponent_team_code: Optional[str] = None
    
    production_model_version: str = "PlayerSuite-v1.0"
    shadow_model_version: str = "PlayerSuite-v1.1-c1-shadow"
    
    role: str = "bench"  # star | starter | bench
    
    predicted_minutes_production: Optional[float] = None
    predicted_minutes_shadow: Optional[float] = None
    
    predicted_points_production: Optional[float] = None
    predicted_points_shadow: Optional[float] = None
    
    predicted_rebounds_production: Optional[float] = None
    predicted_rebounds_shadow: Optional[float] = None
    
    predicted_assists_production: Optional[float] = None
    predicted_assists_shadow: Optional[float] = None
    
    feature_contract_version: str = "v1.1-player-role-stratified"
    prediction_timestamp: datetime = Field(default_factory=datetime.utcnow)
    prediction_status: str = "pending"  # pending | evaluated | cancelled
    
    # Actual postgame outcomes (populated during outcome settlement)
    actual_minutes: Optional[float] = None
    actual_points: Optional[float] = None
    actual_rebounds: Optional[float] = None
    actual_assists: Optional[float] = None
    outcome_recorded_at: Optional[datetime] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PlayerShadowPredictionORM(Base):
    """
    SQLAlchemy ORM table definition for persistent paired player predictions.
    """
    __tablename__ = "player_shadow_predictions"

    prediction_id = Column(String(64), primary_key=True, index=True)
    game_id = Column(String(64), index=True, nullable=False)
    game_date = Column(Date, index=True, nullable=False)
    player_id = Column(String(32), index=True, nullable=False)
    player_name = Column(String(100), nullable=False)
    team_id = Column(String(32), nullable=False)
    team_code = Column(String(10), nullable=False)
    opponent_team_id = Column(String(32), nullable=False)
    opponent_team_code = Column(String(10), nullable=True)

    production_model_version = Column(String(128), nullable=False, default="PlayerSuite-v1.0")
    shadow_model_version = Column(String(128), nullable=False, default="PlayerSuite-v1.1-c1-shadow")

    role = Column(String(32), index=True, nullable=False)

    predicted_minutes_production = Column(Float, nullable=False)
    predicted_minutes_shadow = Column(Float, nullable=False)

    predicted_points_production = Column(Float, nullable=False)
    predicted_points_shadow = Column(Float, nullable=False)

    predicted_rebounds_production = Column(Float, nullable=False)
    predicted_rebounds_shadow = Column(Float, nullable=False)

    predicted_assists_production = Column(Float, nullable=False)
    predicted_assists_shadow = Column(Float, nullable=False)

    feature_contract_version = Column(String(64), nullable=False, default="v1.1-player-role-stratified")
    prediction_timestamp = Column(DateTime, index=True, nullable=False, default=datetime.utcnow)
    prediction_status = Column(String(32), index=True, nullable=False, default="pending")

    actual_minutes = Column(Float, nullable=True)
    actual_points = Column(Float, nullable=True)
    actual_rebounds = Column(Float, nullable=True)
    actual_assists = Column(Float, nullable=True)
    outcome_recorded_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_player_shadow_game_player", "game_id", "player_id", unique=True),
        Index("idx_player_shadow_date_status", "game_date", "prediction_status"),
        Index("idx_player_shadow_role_status", "role", "prediction_status"),
    )

