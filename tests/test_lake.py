"""
Unit and integration tests for the Parquet + DuckDB Analytical Lake layer.
"""

import os
import pytest
from src.lake.duckdb_client import DuckDBClient
from src.lake.parquet_converter import ParquetConverter

def test_duckdb_client_queries():
    """
    Tests that DuckDBClient registers parquet views and executes queries.
    """
    client = DuckDBClient()
    row_counts = client.get_row_counts()
    
    assert "player_game_stats" in row_counts
    assert "games" in row_counts
    assert "team_game_stats" in row_counts
    
    assert row_counts["player_game_stats"] > 1_000_000, "Parquet must have all historical player stats"
    assert row_counts["games"] > 70_000, "Parquet must have all historical games"
    assert row_counts["team_game_stats"] > 140_000, "Parquet must have all team stats"

def test_duckdb_aggregations():
    """
    Tests analytical queries using DuckDB.
    """
    client = DuckDBClient()
    df = client.query_df("""
        SELECT COUNT(*) as game_count 
        FROM games
    """)
    assert df["game_count"].iloc[0] > 70_000

    # Query player stats
    player_df = client.query_df("""
        SELECT personId, COUNT(*) as games_played
        FROM player_game_stats
        GROUP BY personId
        ORDER BY games_played DESC
        LIMIT 5
    """)
    assert len(player_df) == 5
    assert player_df["games_played"].iloc[0] > 1000
