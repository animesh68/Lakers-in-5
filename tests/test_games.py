"""
Unit tests for games schema, validation, and domain constraints.
"""

import pytest
from sqlalchemy import text
from src.validation.schemas import GameValidationSchema

def test_game_validation_schema_valid():
    valid_data = {
        "game_id": "0022300001",
        "game_date": "2023-10-24",
        "home_team_id": 1610612743,
        "away_team_id": 1610612747,
        "home_score": 119,
        "away_score": 107,
        "winner": "Denver Nuggets"
    }
    game = GameValidationSchema(**valid_data)
    assert game.game_id == "0022300001"
    assert game.home_score == 119

def test_game_validation_schema_identical_teams():
    invalid_data = {
        "game_id": "0022300002",
        "home_team_id": 1610612747,
        "away_team_id": 1610612747,
        "home_score": 100,
        "away_score": 98
    }
    with pytest.raises(ValueError, match="cannot be identical"):
        GameValidationSchema(**invalid_data)

def test_game_validation_negative_score():
    invalid_data = {
        "game_id": "0022300003",
        "home_team_id": 1610612747,
        "away_team_id": 1610612744,
        "home_score": -5,
        "away_score": 100
    }
    with pytest.raises(ValueError):
        GameValidationSchema(**invalid_data)

def test_insert_and_query_games(test_engine):
    with test_engine.begin() as conn:
        conn.execute(text("""
            INSERT OR REPLACE INTO teams (team_id, team_abbreviation, team_city, team_name)
            VALUES (1610612747, 'LAL', 'Los Angeles', 'Lakers'),
                   (1610612744, 'GSW', 'Golden State', 'Warriors');
        """))
        conn.execute(text("""
            INSERT OR REPLACE INTO games (
                game_id, game_datetime_est, game_date,
                home_team_id, away_team_id, home_score, away_score, winner
            ) VALUES (
                '0022300010', '2023-10-25 22:00:00', '2023-10-25',
                1610612747, 1610612744, 115, 110, 'Lakers'
            );
        """))

    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT game_id, winner FROM games WHERE game_id = '0022300010'")).fetchone()
        assert res is not None
        assert res[0] == "0022300010"
        assert res[1] == "Lakers"
