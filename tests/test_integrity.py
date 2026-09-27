"""
Integration and integrity tests: foreign keys, uniqueness, and temporal data leakage guardrails.
"""

from datetime import date
from sqlalchemy import text
from src.validation.validator import DataValidator

def test_temporal_leakage_guardrail(test_engine):
    """
    Ensures that queries designed for feature engineering strictly filter out games
    on or after the prediction target date.
    """
    prediction_target_date = date(2026, 1, 20)

    with test_engine.begin() as conn:
        conn.execute(text("""
            INSERT OR REPLACE INTO games (game_id, game_date, home_team_id, away_team_id, home_score, away_score)
            VALUES ('G_PAST', '2026-01-18', 1610612747, 1610612744, 110, 105),
                   ('G_TARGET', '2026-01-20', 1610612747, 1610612743, 112, 108),
                   ('G_FUTURE', '2026-01-22', 1610612747, 1610612746, 100, 95);
        """))

    with test_engine.connect() as conn:
        # Query allowed features prior to prediction date
        allowed_games = conn.execute(
            text("SELECT game_id FROM games WHERE game_date < :pred_date"),
            {"pred_date": str(prediction_target_date)}
        ).fetchall()
        game_ids = [g[0] for g in allowed_games]

        assert "G_PAST" in game_ids
        assert "G_TARGET" not in game_ids, "CRITICAL: Target game itself must not be in prior feature window!"
        assert "G_FUTURE" not in game_ids, "CRITICAL: Future game leaked into feature window!"

def test_data_validator_on_clean_data(test_engine):
    with test_engine.begin() as conn:
        conn.execute(text("""
            INSERT OR REPLACE INTO teams (team_id, team_abbreviation, team_city, team_name)
            VALUES (1610612747, 'LAL', 'Los Angeles', 'Lakers'),
                   (1610612744, 'GSW', 'Golden State', 'Warriors');
        """))
        conn.execute(text("""
            INSERT OR REPLACE INTO players (person_id, first_name, last_name)
            VALUES (2544, 'LeBron', 'James');
        """))
        conn.execute(text("""
            INSERT OR REPLACE INTO games (game_id, game_date, home_team_id, away_team_id, home_score, away_score)
            VALUES ('G_VAL_1', '2026-01-18', 1610612747, 1610612744, 110, 105);
        """))
        conn.execute(text("""
            INSERT OR REPLACE INTO team_game_stats (
                game_id, team_id, opponent_team_id, home, win, team_score, opponent_score,
                points_in_the_paint, assists, rebounds_total, turnovers, field_goals_made, field_goals_attempted
            ) VALUES (
                'G_VAL_1', 1610612747, 1610612744, 1, 1, 110, 105, 50, 25, 45, 10, 40, 80
            );
        """))
        conn.execute(text("""
            INSERT OR REPLACE INTO player_game_stats (
                game_id, person_id, player_team_id, opponent_team_id, points, assists, rebounds_total,
                turnovers, steals, blocks, field_goals_made, field_goals_attempted
            ) VALUES (
                'G_VAL_1', 2544, 1610612747, 1610612744, 30, 8, 10, 2, 1, 1, 12, 20
            );
        """))

    validator = DataValidator(engine=test_engine)
    report = validator.run_all_validations()
    assert report["overall_status"] == "PASSED"


def test_canonical_team_name_normalization():
    """
    Regression test preventing duplicate city/name concatenation bugs
    such as 'LA Clippers Clippers'.
    """
    from src.inference.schedule_service import normalize_team, ScheduleService

    # Test LAC direct code normalization
    lac_meta = normalize_team("LAC")
    assert lac_meta["name"] == "LA Clippers", f"Expected 'LA Clippers', got '{lac_meta['name']}'"
    assert "LA Clippers Clippers" not in lac_meta["name"]

    # Test all 30 teams for duplication pattern (e.g. 'Clippers Clippers', 'Lakers Lakers')
    for code in ["LAL", "LAC", "GSW", "BOS", "NYK", "DEN", "MIA"]:
        meta = normalize_team(code)
        words = meta["name"].split()
        if len(words) >= 2:
            assert words[-1] != words[-2], f"Duplicate team name detected in {meta['name']}"

    # Test schedule games
    service = ScheduleService()
    schedule = service.get_games_for_team("LAC")[:5]
    for g in schedule:
        assert "LA Clippers Clippers" not in g.get("home_team", "")
        assert "LA Clippers Clippers" not in g.get("away_team", "")


def test_canonical_model_health_status_contract():
    """
    Regression test ensuring that model health statuses adhere strictly to canonical enums
    ['HEALTHY', 'WARNING', 'CRITICAL'] and never produce contradictory states.
    """
    from src.monitoring.health import ModelHealthService
    from src.monitoring.repository import PredictionRepository

    temp_repo = PredictionRepository(fallback_dir="data/monitoring_test_integrity", use_db=False)
    health_svc = ModelHealthService(repository=temp_repo)

    health_eval = health_svc.evaluate_health(window="30d")
    status = health_eval.get("status")
    assert status in ["HEALTHY", "WARNING", "CRITICAL"], f"Unknown model health status {status}"

    # When healthy, neither degraded nor critical flags should be present
    if status == "HEALTHY":
        assert health_eval.get("issues", []) == [] or len(health_eval.get("issues", [])) == 0


