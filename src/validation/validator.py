"""
Validation suite for Lakers in 5 data quality and integrity assurance.
Performs consistency checks across database tables and outputs structured reports.
"""

from typing import Dict, Any, List
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.utils.logging import logger

class DataValidator:
    def __init__(self, engine: Engine):
        self.engine = engine

    def validate_games(self) -> Dict[str, Any]:
        """
        Validates the games table.
        """
        logger.info("Validating games table...")
        with self.engine.connect() as conn:
            total_games = conn.execute(text("SELECT COUNT(*) FROM games")).scalar() or 0
            dup_games = conn.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT game_id, COUNT(*) FROM games GROUP BY game_id HAVING COUNT(*) > 1
                ) sub
            """)).scalar() or 0
            same_teams = conn.execute(text("""
                SELECT COUNT(*) FROM games 
                WHERE home_team_id IS NOT NULL AND away_team_id IS NOT NULL AND home_team_id = away_team_id
            """)).scalar() or 0
            neg_scores = conn.execute(text("""
                SELECT COUNT(*) FROM games 
                WHERE (home_score IS NOT NULL AND home_score < 0) OR (away_score IS NOT NULL AND away_score < 0)
            """)).scalar() or 0

        passed = (dup_games == 0) and (same_teams == 0) and (neg_scores == 0) and (total_games > 0)
        return {
            "table": "games",
            "total_rows": total_games,
            "duplicate_keys": dup_games,
            "identical_home_away_teams": same_teams,
            "negative_scores": neg_scores,
            "passed": passed
        }

    def validate_team_stats(self) -> Dict[str, Any]:
        """
        Validates the team_game_stats table.
        """
        logger.info("Validating team_game_stats table...")
        with self.engine.connect() as conn:
            total_rows = conn.execute(text("SELECT COUNT(*) FROM team_game_stats")).scalar() or 0
            dup_keys = conn.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT game_id, team_id, COUNT(*) FROM team_game_stats GROUP BY game_id, team_id HAVING COUNT(*) > 1
                ) sub
            """)).scalar() or 0
            neg_stats = conn.execute(text("""
                SELECT COUNT(*) FROM team_game_stats 
                WHERE (points_in_the_paint < 0) 
                   OR (assists < 0) 
                   OR (rebounds_total < 0) 
                   OR (turnovers < 0)
            """)).scalar() or 0
            # In NBA tracking history, complete shot attempts were standardized starting in the 1970s.
            # Modern era games (post-1970) must strictly have made <= attempted.
            invalid_shooting = conn.execute(text("""
                SELECT COUNT(*) FROM team_game_stats tgs
                JOIN games g ON tgs.game_id = g.game_id
                WHERE g.game_date >= '1970-01-01'
                  AND ((tgs.field_goals_made > tgs.field_goals_attempted AND tgs.field_goals_attempted > 0)
                    OR (tgs.three_pointers_made > tgs.three_pointers_attempted AND tgs.three_pointers_attempted > 0)
                    OR (tgs.free_throws_made > tgs.free_throws_attempted AND tgs.free_throws_attempted > 0))
            """)).scalar() or 0

        passed = (dup_keys == 0) and (neg_stats == 0) and (invalid_shooting == 0) and (total_rows > 0)
        return {
            "table": "team_game_stats",
            "total_rows": total_rows,
            "duplicate_keys": dup_keys,
            "negative_stats": neg_stats,
            "invalid_shooting_counts_modern_era": invalid_shooting,
            "passed": passed
        }

    def validate_player_stats(self) -> Dict[str, Any]:
        """
        Validates the player_game_stats table.
        """
        logger.info("Validating player_game_stats table...")
        with self.engine.connect() as conn:
            total_rows = conn.execute(text("SELECT COUNT(*) FROM player_game_stats")).scalar() or 0
            dup_keys = conn.execute(text("""
                SELECT COUNT(*) FROM (
                    SELECT game_id, person_id, COUNT(*) FROM player_game_stats GROUP BY game_id, person_id HAVING COUNT(*) > 1
                ) sub
            """)).scalar() or 0
            neg_stats = conn.execute(text("""
                SELECT COUNT(*) FROM player_game_stats 
                WHERE (points < 0) 
                   OR (assists < 0) 
                   OR (rebounds_total < 0) 
                   OR (turnovers < 0) 
                   OR (steals < 0) 
                   OR (blocks < 0)
            """)).scalar() or 0
            invalid_shooting = conn.execute(text("""
                SELECT COUNT(*) FROM player_game_stats 
                WHERE (field_goals_made > field_goals_attempted AND field_goals_attempted > 0)
                   OR (three_pointers_made > three_pointers_attempted AND three_pointers_attempted > 0)
                   OR (free_throws_made > free_throws_attempted AND free_throws_attempted > 0)
            """)).scalar() or 0
            same_team_opp = conn.execute(text("""
                SELECT COUNT(*) FROM player_game_stats 
                WHERE player_team_id IS NOT NULL AND opponent_team_id IS NOT NULL AND player_team_id = opponent_team_id
            """)).scalar() or 0

        passed = (dup_keys == 0) and (neg_stats == 0) and (invalid_shooting == 0) and (same_team_opp == 0)
        return {
            "table": "player_game_stats",
            "total_rows": total_rows,
            "duplicate_keys": dup_keys,
            "negative_stats": neg_stats,
            "invalid_shooting_counts": invalid_shooting,
            "identical_team_opponent": same_team_opp,
            "passed": passed
        }

    def validate_lakehouse(self) -> Dict[str, Any]:
        """
        Validates the Parquet / DuckDB analytical lakehouse datasets.
        """
        from src.lake.duckdb_client import DuckDBClient
        logger.info("Validating DuckDB / Parquet Analytical Lakehouse...")
        client = DuckDBClient()
        counts = client.get_row_counts()
        
        has_player_stats = counts.get("player_game_stats", 0) > 1_000_000
        has_player_ext = counts.get("player_game_stats_extended", 0) > 800_000
        has_games = counts.get("games", 0) > 70_000
        has_team_stats = counts.get("team_game_stats", 0) > 140_000

        passed = has_player_stats and has_player_ext and has_games and has_team_stats
        return {
            "table": "parquet_duckdb_lakehouse",
            "views": counts,
            "passed": passed
        }

    def run_all_validations(self) -> Dict[str, Any]:
        """
        Runs full validation suite across Neon PostgreSQL and DuckDB Lakehouse.
        """
        games_res = self.validate_games()
        team_res = self.validate_team_stats()
        player_res = self.validate_player_stats()
        lake_res = self.validate_lakehouse()

        all_passed = games_res["passed"] and team_res["passed"] and player_res["passed"] and lake_res["passed"]
        summary = {
            "overall_status": "PASSED" if all_passed else "FAILED",
            "checks": [games_res, team_res, player_res, lake_res]
        }

        logger.info("=" * 70)
        logger.info(f"DATA VALIDATION REPORT: {summary['overall_status']}")
        logger.info("=" * 70)
        for check in summary["checks"]:
            status_str = "[PASS]" if check["passed"] else "[FAIL]"
            tbl_name = check.get("table", "unknown")
            rows_str = f" (Rows: {check['total_rows']:,})" if "total_rows" in check else ""
            logger.info(f"{status_str} Target: {tbl_name}{rows_str}")
            for k, v in check.items():
                if k not in ["table", "passed", "total_rows"]:
                    logger.info(f"    - {k}: {v}")
        logger.info("=" * 70)
        return summary
