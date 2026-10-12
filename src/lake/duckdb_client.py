"""
DuckDB Analytical Client for Lakers in 5.
Provides vectorized SQL interface over historical Parquet datasets for feature engineering and ML training.
Includes robust standard-library SQLite in-memory fallback if DuckDB native extension is unavailable.
"""

import os
import sqlite3
from typing import Optional, Union, Dict, Any
try:
    import duckdb
except Exception:
    duckdb = None
import pandas as pd
from src.utils.logging import logger

class DuckDBClient:
    """
    High-performance analytical client wrapping DuckDB views over Parquet datasets,
    with zero-dependency SQLite in-memory fallback.
    """
    def __init__(self, parquet_dir: Optional[str] = None, database_file: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.parquet_dir = parquet_dir or os.path.join(base_dir, "data", "processed", "parquet")
        self.database_file = database_file
        
        self.conn = None
        self._sqlite_conn = None
        
        if duckdb is not None:
            try:
                self.conn = duckdb.connect(database=self.database_file or ":memory:")
                self.conn.execute("SET memory_limit = '128MB'")
                self.conn.execute("SET threads = 1")
                self._register_views()
            except Exception as e:
                logger.warning(f"DuckDB connection failed, initializing SQLite fallback: {e}")
                self.conn = None
                self._init_sqlite_fallback()
        else:
            self._init_sqlite_fallback()

    def _init_sqlite_fallback(self):
        """Initializes in-memory SQLite with DuckDB-compatible custom SQL scalar functions."""
        self._sqlite_conn = sqlite3.connect(":memory:", check_same_thread=False)
        
        def _sql_year(d):
            if not d: return None
            try: return int(str(d)[:4])
            except Exception: return None
            
        def _sql_month(d):
            if not d: return None
            try: return int(str(d)[5:7])
            except Exception: return None
            
        def _sql_try_cast(v, t=None):
            if v is None: return None
            s = str(v).strip()
            if not s: return None
            try: return float(s)
            except Exception: return None
            
        def _sql_substring(s, start, length):
            if s is None: return ""
            st = int(start) - 1
            ln = int(length)
            return str(s)[st:st+ln]
            
        self._sqlite_conn.create_function("YEAR", 1, _sql_year)
        self._sqlite_conn.create_function("MONTH", 1, _sql_month)
        self._sqlite_conn.create_function("TRY_CAST", 2, _sql_try_cast)
        self._sqlite_conn.create_function("TRY_CAST", 1, _sql_try_cast)
        self._sqlite_conn.create_function("SUBSTRING", 3, _sql_substring)
        self._sqlite_conn.create_function("DATE", 1, lambda d: str(d)[:10] if d else "")
        self._register_views()

    def _register_views(self):
        """
        Registers SQL views mapped to parquet lakehouse files when DuckDB is active.
        """
        if not os.path.exists(self.parquet_dir):
            return

        views = {
            "player_game_stats": "player_game_stats.parquet",
            "player_game_stats_extended": "player_game_stats_extended.parquet",
            "games": "games.parquet",
            "team_game_stats": "team_game_stats.parquet",
            "team_game_stats_extended": "team_game_stats_extended.parquet",
        }

        for view_name, file_name in views.items():
            file_path = os.path.join(self.parquet_dir, file_name)
            if os.path.exists(file_path):
                if self.conn is not None:
                    sql_path = file_path.replace(os.sep, "/")
                    self.conn.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{sql_path}')")
                logger.debug(f"Registered view: {view_name} -> {file_name}")

    def _ensure_sqlite_table(self, table_name: str):
        """Loads a parquet table into SQLite memory on-demand with optimal column projection."""
        if self._sqlite_conn is None:
            return
        cursor = self._sqlite_conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone() is None:
            file_path = os.path.join(self.parquet_dir, f"{table_name}.parquet")
            if os.path.exists(file_path):
                try:
                    col_map = {
                        "games": ["gameId", "gameDateTimeEst", "hometeamId", "awayteamId", "homeScore", "awayScore"],
                        "team_game_stats": ["teamId", "gameDateTimeEst", "gameId", "win", "teamScore", "opponentScore", "fieldGoalsAttempted", "freeThrowsAttempted", "turnovers"],
                        "team_game_stats_extended": ["teamId", "gameId", "offensiveRating", "defensiveRating", "estimatedOffensiveRating", "estimatedDefensiveRating", "effectiveFieldGoalPercentage", "trueShootingPercentage", "pace", "estimatedPace"],
                        "player_game_stats": ["personId", "playerteamId", "gameDateTimeEst", "gameId", "points", "numMinutes", "reboundsTotal", "assists", "fieldGoalsAttempted", "freeThrowsAttempted", "turnovers", "startingPosition"],
                        "player_game_stats_extended": ["personId", "gameId", "trueShootingPercentage", "usagePercentage"],
                    }
                    cols = col_map.get(table_name)
                    df = pd.read_parquet(file_path, columns=cols) if cols else pd.read_parquet(file_path)
                    df.to_sql(table_name, self._sqlite_conn, if_exists="replace", index=False)
                except Exception as e:
                    logger.warning(f"Failed to load {table_name} to SQLite fallback: {e}")

    def query_df(self, sql: str) -> pd.DataFrame:
        """Executes SQL query and returns pandas DataFrame."""
        if self.conn is not None:
            return self.conn.execute(sql).df()
        if self._sqlite_conn is not None:
            for tbl in ["player_game_stats_extended", "team_game_stats_extended", "player_game_stats", "team_game_stats", "games"]:
                if tbl in sql:
                    self._ensure_sqlite_table(tbl)
            clean_sql = self._clean_sql_for_sqlite(sql)
            return pd.read_sql_query(clean_sql, self._sqlite_conn)
        return pd.DataFrame()

    def _clean_sql_for_sqlite(self, sql: str) -> str:
        """Transforms DuckDB-specific syntax (e.g. TRY_CAST(... AS DOUBLE), DATE '...') for SQLite compatibility."""
        s = sql
        s = s.replace(" AS DOUBLE", ", 'DOUBLE'")
        s = s.replace(" AS DATE", ", 'DATE'")
        s = s.replace(" AS VARCHAR", ", 'VARCHAR'")
        s = s.replace("DATE '", "'")
        return s

    def close(self):
        if self.conn is not None:
            self.conn.close()
        if self._sqlite_conn is not None:
            self._sqlite_conn.close()
