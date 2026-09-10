"""
Unit tests for team box score and advanced tracking statistics validation.
"""

import pytest
from sqlalchemy import text
from src.validation.schemas import TeamStatValidationSchema

def test_team_stat_schema_valid():
    valid_data = {
        "game_id": "0022300001",
        "team_id": 1610612747,
        "opponent_team_id": 1610612743,
        "home": 0,
        "win": 0,
        "team_score": 107,
        "opponent_score": 119,
        "field_goals_made": 40,
        "field_goals_attempted": 85,
        "assists": 25,
        "rebounds_total": 45,
        "turnovers": 12
    }
    stat = TeamStatValidationSchema(**valid_data)
    assert stat.team_score == 107
    assert stat.win == 0

def test_team_stat_schema_impossible_shooting():
    invalid_data = {
        "game_id": "0022300001",
        "team_id": 1610612747,
        "opponent_team_id": 1610612743,
        "home": 1,
        "win": 1,
        "field_goals_made": 50,
        "field_goals_attempted": 40  # Made > Attempted is impossible
    }
    with pytest.raises(ValueError, match="cannot exceed attempted"):
        TeamStatValidationSchema(**invalid_data)

def test_insert_team_stats(test_engine):
    with test_engine.begin() as conn:
        conn.execute(text("""
            INSERT OR REPLACE INTO team_game_stats (
                game_id, team_id, opponent_team_id, home, win, team_score, opponent_score, assists
            ) VALUES (
                '0022300010', 1610612747, 1610612744, 1, 1, 115, 110, 28
            );
        """))

    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT assists FROM team_game_stats WHERE game_id = '0022300010' AND team_id = 1610612747")).fetchone()
        assert res is not None
        assert res[0] == 28
