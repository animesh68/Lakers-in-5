"""
Unit tests for player box score and advanced player tracking statistics.
"""

import pytest
from sqlalchemy import text
from src.validation.schemas import PlayerStatValidationSchema

def test_player_stat_schema_valid():
    valid_data = {
        "game_id": "0022300001",
        "person_id": 2544,
        "player_team_id": 1610612747,
        "opponent_team_id": 1610612743,
        "points": 21,
        "assists": 5,
        "rebounds_total": 8,
        "steals": 1,
        "blocks": 0,
        "turnovers": 2,
        "field_goals_made": 10,
        "field_goals_attempted": 16,
        "three_pointers_made": 1,
        "three_pointers_attempted": 4,
        "free_throws_made": 0,
        "free_throws_attempted": 1
    }
    stat = PlayerStatValidationSchema(**valid_data)
    assert stat.points == 21
    assert stat.person_id == 2544

def test_player_stat_impossible_3p_shooting():
    invalid_data = {
        "game_id": "0022300001",
        "person_id": 2544,
        "player_team_id": 1610612747,
        "opponent_team_id": 1610612743,
        "three_pointers_made": 5,
        "three_pointers_attempted": 3  # Made > Attempted
    }
    with pytest.raises(ValueError, match="3Ps .* > attempted"):
        PlayerStatValidationSchema(**invalid_data)

def test_player_stat_negative_points():
    invalid_data = {
        "game_id": "0022300001",
        "person_id": 2544,
        "points": -3
    }
    with pytest.raises(ValueError):
        PlayerStatValidationSchema(**invalid_data)

def test_insert_player_stats(test_engine):
    with test_engine.begin() as conn:
        conn.execute(text("""
            INSERT OR REPLACE INTO players (person_id, first_name, last_name)
            VALUES (2544, 'LeBron', 'James');
        """))
        conn.execute(text("""
            INSERT OR REPLACE INTO player_game_stats (
                game_id, person_id, first_name, last_name, points, assists, rebounds_total
            ) VALUES (
                '0022300010', 2544, 'LeBron', 'James', 28, 11, 10
            );
        """))

    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT points, assists, rebounds_total FROM player_game_stats WHERE game_id = '0022300010' AND person_id = 2544")).fetchone()
        assert res is not None
        assert res[0] == 28
        assert res[1] == 11
        assert res[2] == 10
