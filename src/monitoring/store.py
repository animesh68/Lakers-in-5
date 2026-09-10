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
