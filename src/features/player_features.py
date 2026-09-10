"""
Player Feature Generator for Lakers in 5.
Calculates team-aware, strictly pregame-only aggregate rotation player performance metrics.
Guarantees zero post-game participation leakage: does NOT use target game box-scores or minutes.
"""

from typing import Optional
import duckdb
import pandas as pd
from src.utils.logging import logger

class PlayerFeatureGenerator:
    """
    Computes team-level rotation player aggregations over strictly preceding games with the same franchise.
    Ensures player statistics on prior teams are never attributed to their new team.
    Constructs pregame rotation state without conditioning on target game actual participants.
    """
    def __init__(
        self,
        duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None,
        min_rotation_minutes: float = 10.0,
        lookback_games: int = 5
    ):
        self.conn = duckdb_conn
        self.min_rotation_minutes = min_rotation_minutes
        self.lookback_games = lookback_games

    def generate_player_rotation_features(self) -> pd.DataFrame:
        """
        Calculates pregame rotation points, true shooting %, and usage % per team-game strictly prior to tip-off.
        """
        logger.info(f"Computing canonical pregame player rotation features (Lookback: {self.lookback_games} games, Min Min: {self.min_rotation_minutes})...")
        
        query = f"""
        WITH team_games AS (
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
        player_game_base AS (
            SELECT 
                pgs.personId AS person_id,
                pgs.playerteamId AS team_id,
                pgs.gameId AS game_id,
                TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                CASE 
                    WHEN MONTH(TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                    THEN YEAR(TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE))
                    ELSE YEAR(TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE)) - 1
                END AS season,
                TRY_CAST(pgs.points AS DOUBLE) AS points,
                TRY_CAST(pgs.numMinutes AS DOUBLE) AS minutes,
                TRY_CAST(ext.trueShootingPercentage AS DOUBLE) AS ts_pct,
                TRY_CAST(ext.usagePercentage AS DOUBLE) AS usage_pct
            FROM player_game_stats pgs
            LEFT JOIN player_game_stats_extended ext
                ON pgs.gameId = ext.gameId AND pgs.personId = ext.personId
            WHERE pgs.playerteamId IS NOT NULL AND pgs.personId IS NOT NULL
        ),
        player_rolling AS (
            SELECT 
                person_id,
                team_id,
                game_id,
                game_date,
                season,
                AVG(points) OVER w AS p_points_5,
                AVG(ts_pct) OVER w AS p_ts_5,
                AVG(usage_pct) OVER w AS p_usage_5,
                AVG(minutes) OVER w AS p_min_5,
                LEAD(game_date, 1) OVER (
                    PARTITION BY person_id, team_id, season 
                    ORDER BY game_date, game_id
                ) AS next_game_date
            FROM player_game_base
            WINDOW w AS (
                PARTITION BY person_id, team_id, season 
                ORDER BY game_date, game_id 
                ROWS BETWEEN {self.lookback_games - 1} PRECEDING AND CURRENT ROW
            )
        ),
        pregame_rotation_join AS (
            SELECT 
                tg.game_id,
                tg.team_id,
                pr.p_points_5,
                pr.p_ts_5,
                pr.p_usage_5
            FROM team_games tg
            JOIN player_rolling pr
                ON tg.team_id = pr.team_id 
               AND tg.season = pr.season
               AND tg.game_date > pr.game_date
               AND (pr.next_game_date IS NULL OR tg.game_date <= pr.next_game_date)
            WHERE (pr.p_min_5 >= {self.min_rotation_minutes} OR pr.p_min_5 IS NULL)
        )
        SELECT 
            game_id,
            team_id,
            AVG(p_points_5) AS rotation_points_5,
            AVG(p_ts_5) AS rotation_ts_5,
            AVG(p_usage_5) AS rotation_usage_5
        FROM pregame_rotation_join
        GROUP BY game_id, team_id
        """
        
        df = self.conn.execute(query).df()
        logger.info(f"Generated canonical pregame player rotation features for {len(df):,} team-game records.")
        return df
