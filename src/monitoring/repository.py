"""
Prediction Repository Abstraction for Lakers in 5.
Provides persistent storage, querying, and updating of prediction records across
PostgreSQL / SQLAlchemy and DuckDB / Parquet storage backends.
"""

import os
import json
from datetime import datetime, date
from typing import Optional, List, Dict, Any
import pandas as pd
import duckdb
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.orm import Session

from src.monitoring.store import PredictionRecord, PredictionORM, Base
from src.utils.db import get_engine, get_db_session, test_connection
from src.utils.logging import logger

class PredictionRepository:
    """
    Unified repository interface for prediction records.
    Automatically initializes tables on startup and supports both relational DB and local analytical lakehouse fallback.
    """
    def __init__(
        self,
        db_url: Optional[str] = None,
        fallback_dir: Optional[str] = None,
        use_db: Optional[bool] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.fallback_dir = fallback_dir or os.path.join(base_dir, "data", "monitoring")
        os.makedirs(self.fallback_dir, exist_ok=True)
        self.fallback_parquet_path = os.path.join(self.fallback_dir, "predictions.parquet")
        
        self.use_db = False
        self.engine = None
        
        if use_db is False:
            self.use_db = False
        else:
            try:
                self.engine = get_engine(db_url)
                if test_connection(self.engine):
                    Base.metadata.create_all(self.engine)
                    self.use_db = True
                    logger.info("PredictionRepository initialized with active database engine.")
                else:
                    logger.info("Database connection unavailable; PredictionRepository using DuckDB/Parquet fallback.")
            except Exception as e:
                logger.warning(f"Failed to initialize database engine for PredictionRepository: {e}. Using DuckDB/Parquet fallback.")
                self.use_db = False

    def save_prediction(self, record: PredictionRecord) -> PredictionRecord:
        """
        Saves a prediction record. If a prediction with the same prediction_id already exists,
        updates it idempotently.
        """
        if self.use_db and self.engine:
            try:
                with get_db_session(self.engine) as session:
                    existing = session.execute(
                        select(PredictionORM).where(PredictionORM.prediction_id == record.prediction_id)
                    ).scalars().first()
                    
                    if existing:
                        for k, v in record.model_dump(exclude={"created_at"}).items():
                            if k == "game_date" and isinstance(v, str):
                                v = datetime.strptime(v, "%Y-%m-%d").date()
                            setattr(existing, k, v)
                        existing.updated_at = datetime.utcnow()
                    else:
                        data = record.model_dump()
                        if isinstance(data["game_date"], str):
                            data["game_date"] = datetime.strptime(data["game_date"], "%Y-%m-%d").date()
                        orm_obj = PredictionORM(**data)
                        session.add(orm_obj)
                return record
            except Exception as e:
                logger.error(f"Failed to save prediction to DB: {e}. Falling back to Parquet.")

        return self._save_to_parquet(record)

    def get_prediction_by_id(self, prediction_id: str) -> Optional[PredictionRecord]:
        """Fetches a single prediction by its unique ID."""
        if self.use_db and self.engine:
            try:
                with get_db_session(self.engine) as session:
                    orm_obj = session.execute(
                        select(PredictionORM).where(PredictionORM.prediction_id == prediction_id)
                    ).scalars().first()
                    if orm_obj:
                        return self._orm_to_record(orm_obj)
            except Exception as e:
                logger.error(f"Error querying prediction from DB: {e}")

        df = self._load_parquet()
        if not df.empty and "prediction_id" in df.columns:
            matches = df[df["prediction_id"] == prediction_id]
            if not matches.empty:
                return self._row_to_record(matches.iloc[0])
        return None

    def get_predictions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
        team: Optional[str] = None,
        model_version: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[PredictionRecord]:
        """
        Queries predictions matching given filters, ordered by prediction_created_at descending.
        """
        if self.use_db and self.engine:
            try:
                with get_db_session(self.engine) as session:
                    query = select(PredictionORM)
                    conditions = []
                    if start_date:
                        d_start = datetime.strptime(start_date[:10], "%Y-%m-%d").date()
                        conditions.append(PredictionORM.game_date >= d_start)
                    if end_date:
                        d_end = datetime.strptime(end_date[:10], "%Y-%m-%d").date()
                        conditions.append(PredictionORM.game_date <= d_end)
                    if status:
                        conditions.append(PredictionORM.status == status)
                    if team:
                        conditions.append(or_(
                            PredictionORM.home_team.ilike(f"%{team}%"),
                            PredictionORM.away_team.ilike(f"%{team}%")
                        ))
                    if model_version:
                        conditions.append(PredictionORM.model_version == model_version)

                    if conditions:
                        query = query.where(and_(*conditions))

                    query = query.order_by(desc(PredictionORM.prediction_created_at)).offset(offset).limit(limit)
                    results = session.execute(query).scalars().all()
                    return [self._orm_to_record(r) for r in results]
            except Exception as e:
                logger.error(f"DB query failed in get_predictions: {e}")

        df = self._load_parquet()
        if df.empty:
            return []

        con = duckdb.connect()
        try:
            con.register("preds", df)
            where_clauses = []
            params = []
            if start_date:
                where_clauses.append("CAST(game_date AS VARCHAR) >= ?")
                params.append(start_date[:10])
            if end_date:
                where_clauses.append("CAST(game_date AS VARCHAR) <= ?")
                params.append(end_date[:10])
            if status:
                where_clauses.append("status = ?")
                params.append(status)
            if team:
                where_clauses.append("(LOWER(home_team) LIKE ? OR LOWER(away_team) LIKE ?)")
                t_lower = f"%{team.lower()}%"
                params.extend([t_lower, t_lower])
            if model_version:
                where_clauses.append("model_version = ?")
                params.append(model_version)

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
            sql = f"SELECT * FROM preds {where_str} ORDER BY prediction_created_at DESC LIMIT {limit} OFFSET {offset}"
            filtered_df = con.execute(sql, params).df()
            return [self._row_to_record(row) for _, row in filtered_df.iterrows()]
        finally:
            con.close()

    def update_outcomes(self, updates: List[Dict[str, Any]]) -> int:
        """
        Updates actual game outcomes and sets status='completed'. Idempotent.
        """
        if not updates:
            return 0

        updated_count = 0
        if self.use_db and self.engine:
            try:
                with get_db_session(self.engine) as session:
                    for upd in updates:
                        pid = upd["prediction_id"]
                        existing = session.execute(
                            select(PredictionORM).where(PredictionORM.prediction_id == pid)
                        ).scalars().first()
                        if existing:
                            existing.actual_home_score = upd.get("actual_home_score")
                            existing.actual_away_score = upd.get("actual_away_score")
                            existing.actual_home_win = upd.get("actual_home_win")
                            existing.actual_home_margin = upd.get("actual_home_margin")
                            existing.status = "completed"
                            existing.outcome_recorded_at = datetime.utcnow()
                            existing.updated_at = datetime.utcnow()
                            updated_count += 1
                return updated_count
            except Exception as e:
                logger.error(f"DB outcome update failed: {e}")

        df = self._load_parquet()
        if not df.empty:
            for upd in updates:
                pid = upd["prediction_id"]
                mask = df["prediction_id"] == pid
                if mask.any():
                    df.loc[mask, "actual_home_score"] = upd.get("actual_home_score")
                    df.loc[mask, "actual_away_score"] = upd.get("actual_away_score")
                    df.loc[mask, "actual_home_win"] = upd.get("actual_home_win")
                    df.loc[mask, "actual_home_margin"] = upd.get("actual_home_margin")
                    df.loc[mask, "status"] = "completed"
                    df.loc[mask, "outcome_recorded_at"] = datetime.utcnow()
                    df.loc[mask, "updated_at"] = datetime.utcnow()
                    updated_count += 1
            df.to_parquet(self.fallback_parquet_path, index=False)
        return updated_count

    def _save_to_parquet(self, record: PredictionRecord) -> PredictionRecord:
        """Saves or updates a record in the local Parquet file."""
        df = self._load_parquet()
        rec_dict = record.model_dump()
        new_row = pd.DataFrame([rec_dict])

        if df.empty:
            df = new_row
        else:
            if "prediction_id" in df.columns and record.prediction_id in df["prediction_id"].values:
                df = df[df["prediction_id"] != record.prediction_id]
            df = pd.concat([df, new_row], ignore_index=True)

        df.to_parquet(self.fallback_parquet_path, index=False)
        return record

    def _load_parquet(self) -> pd.DataFrame:
        """Loads predictions from local Parquet."""
        if os.path.exists(self.fallback_parquet_path):
            try:
                return pd.read_parquet(self.fallback_parquet_path)
            except Exception as e:
                logger.warning(f"Error reading {self.fallback_parquet_path}: {e}")
        return pd.DataFrame()

    def _orm_to_record(self, orm: PredictionORM) -> PredictionRecord:
        """Converts an ORM object into a Pydantic record."""
        return PredictionRecord(
            prediction_id=orm.prediction_id,
            game_id=orm.game_id,
            game_date=str(orm.game_date),
            home_team=orm.home_team,
            away_team=orm.away_team,
            home_team_id=orm.home_team_id,
            away_team_id=orm.away_team_id,
            prediction_created_at=orm.prediction_created_at,
            model_version=orm.model_version,
            classifier_model_version=orm.classifier_model_version,
            regressor_model_version=orm.regressor_model_version,
            home_win_probability=orm.home_win_probability,
            away_win_probability=orm.away_win_probability,
            predicted_home_margin=orm.predicted_home_margin,
            feature_schema_version=orm.feature_schema_version,
            feature_snapshot_hash=orm.feature_snapshot_hash,
            features_json=orm.features_json,
            status=orm.status,
            actual_home_score=orm.actual_home_score,
            actual_away_score=orm.actual_away_score,
            actual_home_win=orm.actual_home_win,
            actual_home_margin=orm.actual_home_margin,
            outcome_recorded_at=orm.outcome_recorded_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )

    def _row_to_record(self, row: pd.Series) -> PredictionRecord:
        """Converts a pandas DataFrame row into a Pydantic record."""
        row_dict = row.to_dict()
        cleaned = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
        return PredictionRecord(**cleaned)
