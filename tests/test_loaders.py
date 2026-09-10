"""
Integration tests for raw data loader functions.
Verifies loader parsing logic, chunking, and database population.
"""

from src.ingestion.load_teams import load_teams
from src.ingestion.load_players import load_players
from src.ingestion.load_team_histories import load_team_histories
from src.ingestion.load_transactions import load_transactions
from src.ingestion.load_games import load_games
from src.ingestion.load_team_stats import load_team_stats

def test_load_teams(test_engine, raw_data_dir):
    count = load_teams(test_engine, raw_data_dir)
    assert count > 0

def test_load_team_histories(test_engine, raw_data_dir):
    count = load_team_histories(test_engine, raw_data_dir)
    assert count == 140

def test_load_transactions(test_engine, raw_data_dir):
    count = load_transactions(test_engine, raw_data_dir)
    assert count == 259

def test_load_players_bio(test_engine, raw_data_dir):
    count = load_players(test_engine, raw_data_dir)
    assert count >= 6692
