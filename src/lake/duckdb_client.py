"""
DuckDB Analytical Client for Lakers in 5.
Provides vectorized SQL interface over historical Parquet datasets for feature engineering and ML training.
"""

import os
from typing import Optional, Union, Dict, Any
import duckdb
import pandas as pd
import polars as pl
from src.utils.logging import logger

class DuckDBClient:
    """
    High-performance analytical client wrapping DuckDB views over Parquet datasets.
    """
    def __init__(self, parquet_dir: Optional[str] = None, database_file: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.parquet_dir = parquet_dir or os.path.join(base_dir, "data", "processed", "parquet")
        self.database_file = database_file # None for in-memory
        self.conn = duckdb.connect(database=self.database_file or ":memory:")
        self._register_views()

    def _register_views(self):
        """
        Registers SQL views mapped to parquet files.
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
                sql_path = file_path.replace(os.sep, "/")
                self.conn.execute(f"CREATE OR REPLACE VIEW {view_name} AS SELECT * FROM read_parquet('{sql_path}')")
                logger.debug(f"Registered DuckDB view: {view_name} -> {file_name}")

    def query(self, sql: str) -> duckdb.DuckDBPyRelation:
        """
        Executes arbitrary SQL query and returns DuckDB relation.
        """
        return self.conn.execute(sql)

    def query_df(self, sql: str) -> pd.DataFrame:
        """
        Executes SQL query and returns pandas DataFrame.
        """
        return self.conn.execute(sql).df()

    def query_arrow(self, sql: str):
        """
        Executes SQL query and returns PyArrow Table for zero-copy memory transfers.
        """
        return self.conn.execute(sql).arrow()

    def get_row_counts(self) -> Dict[str, int]:
        """
        Returns row counts for all registered analytical views.
        """
        counts = {}
        tables = self.conn.execute("SHOW TABLES").fetchall()
        for t in tables:
            tbl_name = t[0]
            cnt = self.conn.execute(f"SELECT COUNT(*) FROM {tbl_name}").fetchone()[0]
            counts[tbl_name] = cnt
        return counts

    def close(self):
        self.conn.close()

if __name__ == "__main__":
    client = DuckDBClient()
    print("Registered tables:", client.get_row_counts())
