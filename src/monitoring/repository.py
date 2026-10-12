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
try:
    import duckdb
except Exception:
    duckdb = None
from sqlalchemy import select, update, delete, and_, or_, desc
from sqlalchemy.orm import Session

from src.monitoring.store import (
    PredictionRecord,
    PredictionORM,
    PlayerShadowPredictionRecord,
    PlayerShadowPredictionORM,
    Base,
)
from src.utils.db import get_engine, get_db_session, test_connection
from src.utils.logging import logger

class PredictionRepository:
    """
    Unified repository interface for prediction records and player shadow prediction records.
    Automatically initializes tables on startup and supports both relational DB and local analytical lakehouse fallback.
    """
    def __init__(
        self,
        db_url: Optional[str] = None,
        fallback_dir: Optional[str] = None,
        use_db: Optional[bool] = None,
        parquet_player_shadow_path: Optional[str] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.fallback_dir = fallback_dir or os.path.join(base_dir, "data", "monitoring")
        os.makedirs(self.fallback_dir, exist_ok=True)
        self.fallback_parquet_path = os.path.join(self.fallback_dir, "predictions.parquet")
        self.player_shadow_parquet_path = parquet_player_shadow_path or os.path.join(self.fallback_dir, "player_shadow_predictions.parquet")
        
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
            for col in ["outcome_recorded_at", "updated_at", "status"]:
                if col in df.columns:
                    df[col] = df[col].astype("object")
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
            self._write_df_to_parquet(df, self.fallback_parquet_path)
        return updated_count

    def _write_df_to_parquet(self, df: pd.DataFrame, path: str):
        """Writes DataFrame to Parquet with DuckDB fallback when pyarrow DLL is unavailable."""
        try:
            df.to_parquet(path, index=False)
        except Exception:
            import duckdb
            con = duckdb.connect()
            con.register("df_to_save", df)
            p_sql = path.replace(os.sep, "/")
            con.execute(f"COPY df_to_save TO '{p_sql}' (FORMAT PARQUET)")
            con.close()

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

        self._write_df_to_parquet(df, self.fallback_parquet_path)
        return record

    def _write_df_to_parquet(self, df: pd.DataFrame, path: str):
        """Writes dataframe to parquet using Polars or Pandas."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            import polars as pl
            pl.from_pandas(df).write_parquet(path)
        except Exception:
            try:
                df.to_parquet(path, index=False)
            except Exception as e:
                logger.error(f"Failed to write parquet to {path}: {e}")

    def _load_parquet(self) -> pd.DataFrame:
        """Loads predictions from local Parquet."""
        if os.path.exists(self.fallback_parquet_path):
            try:
                import polars as pl
                return pl.read_parquet(self.fallback_parquet_path).to_pandas()
            except Exception:
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

    # -------------------------------------------------------------------------
    # Player Shadow Prediction Logging & Retrieval Methods
    # -------------------------------------------------------------------------

    def save_player_shadow_prediction(self, record: PlayerShadowPredictionRecord) -> PlayerShadowPredictionRecord:
        """
        Saves a single player shadow prediction record idempotently.
        """
        return self.save_player_shadow_predictions([record])[0]

    def save_player_shadow_predictions(self, records: List[PlayerShadowPredictionRecord]) -> List[PlayerShadowPredictionRecord]:
        """
        Batch saves player shadow prediction records idempotently.
        """
        if not records:
            return []

        if self.use_db and self.engine:
            try:
                with get_db_session(self.engine) as session:
                    for rec in records:
                        existing = session.execute(
                            select(PlayerShadowPredictionORM).where(
                                and_(
                                    PlayerShadowPredictionORM.game_id == rec.game_id,
                                    PlayerShadowPredictionORM.player_id == rec.player_id
                                )
                            )
                        ).scalars().first()

                        if existing:
                            for k, v in rec.model_dump(exclude={"created_at"}).items():
                                if k == "game_date" and isinstance(v, str):
                                    v = datetime.strptime(v, "%Y-%m-%d").date()
                                setattr(existing, k, v)
                            existing.updated_at = datetime.utcnow()
                        else:
                            data = rec.model_dump()
                            if isinstance(data["game_date"], str):
                                data["game_date"] = datetime.strptime(data["game_date"], "%Y-%m-%d").date()
                            orm_obj = PlayerShadowPredictionORM(**data)
                            session.add(orm_obj)
                return records
            except Exception as e:
                logger.error(f"Failed to save player shadow predictions to DB: {e}. Falling back to Parquet.")

        return self._save_player_shadow_to_parquet(records)

    def get_player_shadow_predictions(
        self,
        status: Optional[str] = None,
        game_id: Optional[str] = None,
        player_id: Optional[str] = None,
        limit: int = 10000
    ) -> List[PlayerShadowPredictionRecord]:
        """
        Retrieves player shadow predictions matching given criteria.
        """
        if self.use_db and self.engine:
            try:
                with get_db_session(self.engine) as session:
                    stmt = select(PlayerShadowPredictionORM)
                    conditions = []
                    if status:
                        conditions.append(PlayerShadowPredictionORM.prediction_status == status)
                    if game_id:
                        conditions.append(PlayerShadowPredictionORM.game_id == game_id)
                    if player_id:
                        conditions.append(PlayerShadowPredictionORM.player_id == player_id)
                    if conditions:
                        stmt = stmt.where(and_(*conditions))
                    stmt = stmt.order_by(desc(PlayerShadowPredictionORM.prediction_timestamp)).limit(limit)
                    results = session.execute(stmt).scalars().all()
                    return [self._orm_to_player_shadow_record(r) for r in results]
            except Exception as e:
                logger.error(f"Error querying player shadow predictions from DB: {e}")

        df = self._load_player_shadow_parquet()
        if df.empty:
            return []

        if status and "prediction_status" in df.columns:
            df = df[df["prediction_status"] == status]
        if game_id and "game_id" in df.columns:
            df = df[df["game_id"] == game_id]
        if player_id and "player_id" in df.columns:
            df = df[df["player_id"] == player_id]

        if df.empty:
            return []

        records = [self._row_to_player_shadow_record(row) for _, row in df.head(limit).iterrows()]
        return records

    def update_player_shadow_outcome(
        self,
        prediction_id: str,
        actual_minutes: float,
        actual_points: float,
        actual_rebounds: float,
        actual_assists: float
    ) -> bool:
        """
        Updates actual box score outcome for a player shadow prediction record.
        """
        now = datetime.utcnow()
        if self.use_db and self.engine:
            try:
                with get_db_session(self.engine) as session:
                    stmt = (
                        update(PlayerShadowPredictionORM)
                        .where(PlayerShadowPredictionORM.prediction_id == prediction_id)
                        .values(
                            actual_minutes=actual_minutes,
                            actual_points=actual_points,
                            actual_rebounds=actual_rebounds,
                            actual_assists=actual_assists,
                            prediction_status="evaluated",
                            outcome_recorded_at=now,
                            updated_at=now
                        )
                    )
                    res = session.execute(stmt)
                    return res.rowcount > 0
            except Exception as e:
                logger.error(f"Failed to update player shadow outcome in DB: {e}")

        df = self._load_player_shadow_parquet()
        if not df.empty and "prediction_id" in df.columns:
            mask = df["prediction_id"] == prediction_id
            if mask.sum() > 0:
                df.loc[mask, "actual_minutes"] = actual_minutes
                df.loc[mask, "actual_points"] = actual_points
                df.loc[mask, "actual_rebounds"] = actual_rebounds
                df.loc[mask, "actual_assists"] = actual_assists
                df.loc[mask, "prediction_status"] = "evaluated"
                df.loc[mask, "outcome_recorded_at"] = now
                df.loc[mask, "updated_at"] = now
                self._write_df_to_parquet(df, self.player_shadow_parquet_path)
                return True
        return False

    def _save_player_shadow_to_parquet(self, records: List[PlayerShadowPredictionRecord]) -> List[PlayerShadowPredictionRecord]:
        """Saves player shadow records to local fallback Parquet."""
        df = self._load_player_shadow_parquet()
        new_rows = pd.DataFrame([r.model_dump() for r in records])

        if df.empty:
            df = new_rows
        else:
            # Deduplicate by (game_id, player_id) or prediction_id
            keys = set(zip(new_rows["game_id"], new_rows["player_id"]))
            if "game_id" in df.columns and "player_id" in df.columns:
                existing_keys = list(zip(df["game_id"], df["player_id"]))
                mask = [k not in keys for k in existing_keys]
                df = df[mask]
            df = pd.concat([df, new_rows], ignore_index=True)

        self._write_df_to_parquet(df, self.player_shadow_parquet_path)
        return records

    def _load_player_shadow_parquet(self) -> pd.DataFrame:
        """Loads player shadow predictions from local Parquet."""
        if os.path.exists(self.player_shadow_parquet_path):
            try:
                import polars as pl
                return pl.read_parquet(self.player_shadow_parquet_path).to_pandas()
            except Exception:
                try:
                    return pd.read_parquet(self.player_shadow_parquet_path)
                except Exception as e:
                    logger.warning(f"Error reading {self.player_shadow_parquet_path}: {e}")
        return pd.DataFrame()

    def _orm_to_player_shadow_record(self, orm: PlayerShadowPredictionORM) -> PlayerShadowPredictionRecord:
        return PlayerShadowPredictionRecord(
            prediction_id=orm.prediction_id,
            game_id=orm.game_id,
            game_date=str(orm.game_date),
            player_id=orm.player_id,
            player_name=orm.player_name,
            team_id=orm.team_id,
            team_code=orm.team_code,
            opponent_team_id=orm.opponent_team_id,
            opponent_team_code=orm.opponent_team_code,
            production_model_version=orm.production_model_version,
            shadow_model_version=orm.shadow_model_version,
            role=orm.role,
            predicted_minutes_production=orm.predicted_minutes_production,
            predicted_minutes_shadow=orm.predicted_minutes_shadow,
            predicted_points_production=orm.predicted_points_production,
            predicted_points_shadow=orm.predicted_points_shadow,
            predicted_rebounds_production=orm.predicted_rebounds_production,
            predicted_rebounds_shadow=orm.predicted_rebounds_shadow,
            predicted_assists_production=orm.predicted_assists_production,
            predicted_assists_shadow=orm.predicted_assists_shadow,
            feature_contract_version=orm.feature_contract_version,
            prediction_timestamp=orm.prediction_timestamp,
            prediction_status=orm.prediction_status,
            actual_minutes=orm.actual_minutes,
            actual_points=orm.actual_points,
            actual_rebounds=orm.actual_rebounds,
            actual_assists=orm.actual_assists,
            outcome_recorded_at=orm.outcome_recorded_at,
            created_at=orm.created_at,
            updated_at=orm.updated_at
        )

    def _row_to_player_shadow_record(self, row: pd.Series) -> PlayerShadowPredictionRecord:
        row_dict = row.to_dict()
        cleaned = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}
        return PlayerShadowPredictionRecord(**cleaned)

