"""
Schedule & Rest Feature Generator for Lakers in 5.
Calculates rest days, back-to-back flags, and game density (games in last 7 days) strictly before game date.
"""

from typing import Optional
import duckdb
import pandas as pd
from src.utils.logging import logger

class ScheduleFeatureGenerator:
    """
    Computes schedule rest, fatigue, and density metrics for each team prior to tip-off.
    """
    def __init__(self, duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None):
        self.conn = duckdb_conn

    def generate_schedule_features(self) -> pd.DataFrame:
        """
        Calculates rest days, back-to-back status, and games in last 7 days per team-game.
        """
        logger.info("Computing schedule rest and fatigue features...")
        
        query = """
        WITH team_game_dates AS (
            SELECT DISTINCT
                tgs.gameId AS game_id,
                tgs.teamId AS team_id,
                TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                CASE 
                    WHEN MONTH(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                    THEN YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE))
                    ELSE YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) - 1
                END AS season
            FROM team_game_stats tgs
            WHERE tgs.teamId IS NOT NULL
        ),
        lagged_dates AS (
            SELECT 
                game_id,
                team_id,
                game_date,
                season,
                LAG(game_date, 1) OVER (
                    PARTITION BY team_id, season 
                    ORDER BY game_date, game_id
                ) AS prev_game_date
            FROM team_game_dates
        ),
        rest_calc AS (
            SELECT 
                cur.game_id,
                cur.team_id,
                cur.game_date,
                -- Rest days since previous same-season game (capped at 10 to normalize long breaks / season openers)
                CASE 
                    WHEN cur.prev_game_date IS NULL THEN NULL 
                    ELSE DATEDIFF('day', cur.prev_game_date, cur.game_date)
                END AS raw_rest_days,
                -- Back-to-back: played yesterday (rest_days == 1)
                CASE 
                    WHEN cur.prev_game_date IS NOT NULL AND DATEDIFF('day', cur.prev_game_date, cur.game_date) = 1 THEN 1 
                    ELSE 0 
                END AS is_back_to_back,
                -- Count of games played by this team in the preceding 7 calendar days [game_date - 7 days, game_date - 1 day]
                (
                    SELECT COUNT(*)
                    FROM team_game_dates past
                    WHERE past.team_id = cur.team_id
                      AND past.game_date >= (cur.game_date - INTERVAL 7 DAY)
                      AND past.game_date < cur.game_date
                ) AS games_last_7
            FROM lagged_dates cur
        )
        SELECT 
            game_id,
            team_id,
            raw_rest_days AS rest_days,
            is_back_to_back AS back_to_back,
            games_last_7
        FROM rest_calc
        """
        
        df = self.conn.execute(query).df()
        logger.info(f"Generated schedule features for {len(df):,} team-game records.")
        return df
