"""
Team Feature Generator for Lakers in 5.
Calculates leakage-safe recent form and advanced efficiency metrics using DuckDB window aggregations.
"""

from typing import Optional
import duckdb
import pandas as pd
from src.utils.logging import logger

class TeamFeatureGenerator:
    """
    Computes rolling team-level statistics over preceding same-season games.
    Strictly uses ROWS BETWEEN N PRECEDING AND 1 PRECEDING (excluding the current game).
    """
    def __init__(self, duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None):
        self.conn = duckdb_conn

    def generate_team_rolling_features(self) -> pd.DataFrame:
        """
        Extracts team game logs, computes 5-game and 10-game rolling windows partitioned by (team_id, season),
        and returns a DataFrame keyed by (game_id, team_id).
        """
        logger.info("Computing team rolling form and advanced efficiency features...")
        
        # SQL query using DuckDB's vectorized analytical engine
        # We join team_game_stats with team_game_stats_extended and games to extract accurate season mapping and date
        query = """
        WITH team_game_base AS (
            SELECT 
                tgs.gameId AS game_id,
                tgs.teamId AS team_id,
                TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                -- Season computation: NBA seasons start in October/November (month >= 9 -> year, else year - 1)
                CASE 
                    WHEN MONTH(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                    THEN YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE))
                    ELSE YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) - 1
                END AS season,
                TRY_CAST(tgs.win AS DOUBLE) AS is_win,
                TRY_CAST(tgs.teamScore AS DOUBLE) AS points,
                TRY_CAST(tgs.opponentScore AS DOUBLE) AS points_allowed,
                TRY_CAST(tgs.teamScore AS DOUBLE) - TRY_CAST(tgs.opponentScore AS DOUBLE) AS point_margin,
                -- Advanced metrics from team_game_stats_extended (tracking era 1996+)
                COALESCE(TRY_CAST(ext.offensiveRating AS DOUBLE), TRY_CAST(ext.estimatedOffensiveRating AS DOUBLE)) AS off_rating,
                COALESCE(TRY_CAST(ext.defensiveRating AS DOUBLE), TRY_CAST(ext.estimatedDefensiveRating AS DOUBLE)) AS def_rating,
                TRY_CAST(ext.effectiveFieldGoalPercentage AS DOUBLE) AS efg,
                TRY_CAST(ext.trueShootingPercentage AS DOUBLE) AS ts,
                COALESCE(TRY_CAST(ext.pace AS DOUBLE), TRY_CAST(ext.estimatedPace AS DOUBLE)) AS pace,
                TRY_CAST(ext.teamTurnoverPercentage AS DOUBLE) AS tov_pct,
                TRY_CAST(ext.offensiveReboundPercentage AS DOUBLE) AS oreb_pct,
                TRY_CAST(ext.defensiveReboundPercentage AS DOUBLE) AS dreb_pct
            FROM team_game_stats tgs
            LEFT JOIN team_game_stats_extended ext 
                ON tgs.gameId = ext.gameId AND tgs.teamId = ext.teamId
            WHERE tgs.teamId IS NOT NULL
        ),
        team_rolling AS (
            SELECT 
                game_id,
                team_id,
                game_date,
                season,
                -- 5-game rolling windows (strictly preceding games: 5 preceding to 1 preceding)
                AVG(is_win) OVER w5 AS win_pct_5,
                AVG(points) OVER w5 AS avg_points_5,
                AVG(points_allowed) OVER w5 AS avg_points_allowed_5,
                AVG(point_margin) OVER w5 AS point_diff_5,
                AVG(off_rating) OVER w5 AS off_rating_5,
                AVG(def_rating) OVER w5 AS def_rating_5,
                AVG(efg) OVER w5 AS efg_5,
                AVG(ts) OVER w5 AS ts_5,
                AVG(pace) OVER w5 AS pace_5,
                AVG(tov_pct) OVER w5 AS tov_pct_5,
                AVG(oreb_pct) OVER w5 AS oreb_pct_5,
                AVG(dreb_pct) OVER w5 AS dreb_pct_5,

                -- 10-game rolling windows (strictly preceding games: 10 preceding to 1 preceding)
                AVG(is_win) OVER w10 AS win_pct_10,
                AVG(points) OVER w10 AS avg_points_10,
                AVG(points_allowed) OVER w10 AS avg_points_allowed_10,
                AVG(point_margin) OVER w10 AS point_diff_10,
                AVG(off_rating) OVER w10 AS off_rating_10,
                AVG(def_rating) OVER w10 AS def_rating_10,
                AVG(efg) OVER w10 AS efg_10,
                AVG(ts) OVER w10 AS ts_10,
                AVG(pace) OVER w10 AS pace_10,
                AVG(tov_pct) OVER w10 AS tov_pct_10,
                AVG(oreb_pct) OVER w10 AS oreb_pct_10,
                AVG(dreb_pct) OVER w10 AS dreb_pct_10,

                -- Count of preceding games in current season
                COUNT(points) OVER w5 AS count_prev_5,
                COUNT(points) OVER w10 AS count_prev_10
            FROM team_game_base
            WINDOW 
                w5 AS (
                    PARTITION BY team_id, season 
                    ORDER BY game_date, game_id 
                    ROWS BETWEEN 5 PRECEDING AND 1 PRECEDING
                ),
                w10 AS (
                    PARTITION BY team_id, season 
                    ORDER BY game_date, game_id 
                    ROWS BETWEEN 10 PRECEDING AND 1 PRECEDING
                )
        )
        SELECT 
            game_id,
            team_id,
            -- If team has 0 prior games in the current season, stats are NaN
            CASE WHEN count_prev_5 > 0 THEN win_pct_5 ELSE NULL END AS win_pct_5,
            CASE WHEN count_prev_5 > 0 THEN avg_points_5 ELSE NULL END AS avg_points_5,
            CASE WHEN count_prev_5 > 0 THEN avg_points_allowed_5 ELSE NULL END AS avg_points_allowed_5,
            CASE WHEN count_prev_5 > 0 THEN point_diff_5 ELSE NULL END AS point_diff_5,
            CASE WHEN count_prev_5 > 0 THEN off_rating_5 ELSE NULL END AS off_rating_5,
            CASE WHEN count_prev_5 > 0 THEN def_rating_5 ELSE NULL END AS def_rating_5,
            CASE WHEN count_prev_5 > 0 THEN efg_5 ELSE NULL END AS efg_5,
            CASE WHEN count_prev_5 > 0 THEN ts_5 ELSE NULL END AS ts_5,
            CASE WHEN count_prev_5 > 0 THEN pace_5 ELSE NULL END AS pace_5,
            CASE WHEN count_prev_5 > 0 THEN tov_pct_5 ELSE NULL END AS tov_pct_5,
            CASE WHEN count_prev_5 > 0 THEN oreb_pct_5 ELSE NULL END AS oreb_pct_5,
            CASE WHEN count_prev_5 > 0 THEN dreb_pct_5 ELSE NULL END AS dreb_pct_5,

            CASE WHEN count_prev_10 > 0 THEN win_pct_10 ELSE NULL END AS win_pct_10,
            CASE WHEN count_prev_10 > 0 THEN avg_points_10 ELSE NULL END AS avg_points_10,
            CASE WHEN count_prev_10 > 0 THEN avg_points_allowed_10 ELSE NULL END AS avg_points_allowed_10,
            CASE WHEN count_prev_10 > 0 THEN point_diff_10 ELSE NULL END AS point_diff_10,
            CASE WHEN count_prev_10 > 0 THEN off_rating_10 ELSE NULL END AS off_rating_10,
            CASE WHEN count_prev_10 > 0 THEN def_rating_10 ELSE NULL END AS def_rating_10,
            CASE WHEN count_prev_10 > 0 THEN efg_10 ELSE NULL END AS efg_10,
            CASE WHEN count_prev_10 > 0 THEN ts_10 ELSE NULL END AS ts_10,
            CASE WHEN count_prev_10 > 0 THEN pace_10 ELSE NULL END AS pace_10,
            CASE WHEN count_prev_10 > 0 THEN tov_pct_10 ELSE NULL END AS tov_pct_10,
            CASE WHEN count_prev_10 > 0 THEN oreb_pct_10 ELSE NULL END AS oreb_pct_10,
            CASE WHEN count_prev_10 > 0 THEN dreb_pct_10 ELSE NULL END AS dreb_pct_10
        FROM team_rolling
        """
        
        df = self.conn.execute(query).df()
        logger.info(f"Generated rolling features for {len(df):,} team-game records.")
        return df
