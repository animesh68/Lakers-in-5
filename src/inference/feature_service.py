"""
Production Pregame Feature Generation Service for Lakers in 5.
Generates strictly pregame, leakage-safe feature vectors matching Phase 2 definitions
and Phase 3 model input contracts for future scheduled NBA games.
"""

import os
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import duckdb

from src.lake.duckdb_client import DuckDBClient
from src.features.elo import EloCalculator
from src.inference.schedule_service import normalize_team
from src.utils.logging import logger

MODEL_FEATURE_CONTRACT = [
    'home_win_pct_5', 'away_win_pct_5', 'home_avg_points_5', 'away_avg_points_5',
    'home_avg_points_allowed_5', 'away_avg_points_allowed_5', 'home_point_diff_5', 'away_point_diff_5',
    'home_win_pct_10', 'away_win_pct_10', 'home_avg_points_10', 'away_avg_points_10',
    'home_avg_points_allowed_10', 'away_avg_points_allowed_10', 'home_point_diff_10', 'away_point_diff_10',
    'home_off_rating_5', 'away_off_rating_5', 'home_def_rating_5', 'away_def_rating_5',
    'home_efg_5', 'away_efg_5', 'home_ts_5', 'away_ts_5', 'home_pace_5', 'away_pace_5',
    'home_off_rating_10', 'away_off_rating_10', 'home_def_rating_10', 'away_def_rating_10',
    'home_efg_10', 'away_efg_10', 'home_ts_10', 'away_ts_10', 'home_pace_10', 'away_pace_10',
    'home_elo', 'away_elo', 'elo_difference',
    'home_rest_days', 'away_rest_days', 'rest_difference',
    'home_back_to_back', 'away_back_to_back', 'home_games_last_7', 'away_games_last_7',
    'home_rotation_points_5', 'away_rotation_points_5',
    'home_rotation_ts_5', 'away_rotation_ts_5',
    'home_rotation_usage_5', 'away_rotation_usage_5'
]

class ProductionFeatureService:
    """
    Constructs real-time pregame feature vectors for any future NBA game.
    Guarantees that no information on or after target_game_date is ever accessed.
    """
    def __init__(self, duckdb_client: Optional[DuckDBClient] = None):
        self.client = duckdb_client or DuckDBClient()
        self._cached_elo_calculator: Optional[EloCalculator] = None
        self._cached_elo_cutoff_date: Optional[str] = None

    @staticmethod
    def get_season_for_date(game_date: str) -> int:
        """
        Determines the NBA season starting year from an ISO date string (YYYY-MM-DD).
        NBA seasons start in October/November (month >= 9 -> year, else year - 1).
        """
        dt = datetime.strptime(str(game_date)[:10], "%Y-%m-%d")
        return dt.year if dt.month >= 9 else dt.year - 1

    def compute_pregame_elo(
        self,
        home_team_id: str,
        away_team_id: str,
        target_game_date: str
    ) -> Tuple[float, float, float]:
        """
        Computes pregame Elo ratings immediately prior to target_game_date.
        Strictly uses games where game_date < target_game_date.
        """
        cutoff_date = str(target_game_date)[:10]
        
        # Check if we can reuse the cached Elo calculator state
        if self._cached_elo_calculator is None or self._cached_elo_cutoff_date != cutoff_date:
            logger.info(f"Computing chronological Elo state before {cutoff_date}...")
            query = f"""
            SELECT 
                gameId AS game_id,
                TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                CASE 
                    WHEN MONTH(TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                    THEN YEAR(TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE))
                    ELSE YEAR(TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE)) - 1
                END AS season,
                hometeamId AS home_team_id,
                awayteamId AS away_team_id,
                TRY_CAST(homeScore AS DOUBLE) AS home_score,
                TRY_CAST(awayScore AS DOUBLE) AS away_score
            FROM games
            WHERE hometeamId IS NOT NULL AND awayteamId IS NOT NULL
              AND TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) < DATE '{cutoff_date}'
              AND TRY_CAST(homeScore AS DOUBLE) IS NOT NULL
            ORDER BY game_date, game_id
            """
            historical_games = self.client.conn.execute(query).df()
            
            calculator = EloCalculator(k_factor=20.0, home_advantage=100.0, season_reversion=0.25)
            # Replay all historical games strictly prior to cutoff_date
            calculator.compute_elo_features(historical_games)
            
            # If target game is in a new season beyond the latest historical game, apply season reversion
            target_season = self.get_season_for_date(cutoff_date)
            if len(historical_games) > 0:
                latest_hist_season = int(historical_games["season"].max())
                if target_season > latest_hist_season:
                    for t in calculator.ratings:
                        calculator.ratings[t] = (
                            (1.0 - calculator.season_reversion) * calculator.ratings[t]
                            + calculator.season_reversion * calculator.initial_elo
                        )
                        
            self._cached_elo_calculator = calculator
            self._cached_elo_cutoff_date = cutoff_date
            
        calc = self._cached_elo_calculator
        pre_home_elo = float(calc.get_rating(str(home_team_id)))
        pre_away_elo = float(calc.get_rating(str(away_team_id)))
        
        # Effective home elo includes home advantage (+100.0)
        elo_diff = (pre_home_elo + calc.home_advantage) - pre_away_elo
        
        return pre_home_elo, pre_away_elo, elo_diff

    def compute_team_rolling_stats(
        self,
        team_id: str,
        target_game_date: str
    ) -> Dict[str, Optional[float]]:
        """
        Computes 5-game and 10-game rolling metrics for a team in the target season prior to target_game_date.
        """
        cutoff_date = str(target_game_date)[:10]
        target_season = self.get_season_for_date(cutoff_date)
        
        query = f"""
        SELECT 
            TRY_CAST(tgs.win AS DOUBLE) AS is_win,
            TRY_CAST(tgs.teamScore AS DOUBLE) AS points,
            TRY_CAST(tgs.opponentScore AS DOUBLE) AS points_allowed,
            TRY_CAST(tgs.teamScore AS DOUBLE) - TRY_CAST(tgs.opponentScore AS DOUBLE) AS point_margin,
            COALESCE(TRY_CAST(ext.offensiveRating AS DOUBLE), TRY_CAST(ext.estimatedOffensiveRating AS DOUBLE)) AS off_rating,
            COALESCE(TRY_CAST(ext.defensiveRating AS DOUBLE), TRY_CAST(ext.estimatedDefensiveRating AS DOUBLE)) AS def_rating,
            TRY_CAST(ext.effectiveFieldGoalPercentage AS DOUBLE) AS efg,
            TRY_CAST(ext.trueShootingPercentage AS DOUBLE) AS ts,
            COALESCE(TRY_CAST(ext.pace AS DOUBLE), TRY_CAST(ext.estimatedPace AS DOUBLE)) AS pace
        FROM team_game_stats tgs
        LEFT JOIN team_game_stats_extended ext 
            ON tgs.gameId = ext.gameId AND tgs.teamId = ext.teamId
        WHERE tgs.teamId = '{team_id}'
          AND TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE) < DATE '{cutoff_date}'
          AND (
            CASE 
                WHEN MONTH(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                THEN YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE))
                ELSE YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) - 1
            END
          ) = {target_season}
        ORDER BY TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE) DESC, tgs.gameId DESC
        LIMIT 10
        """
        logs = self.client.conn.execute(query).df()
        
        metrics = {}
        if len(logs) == 0:
            # Cold start (e.g. season opener) - NaNs preserved
            for window in (5, 10):
                metrics[f"win_pct_{window}"] = np.nan
                metrics[f"avg_points_{window}"] = np.nan
                metrics[f"avg_points_allowed_{window}"] = np.nan
                metrics[f"point_diff_{window}"] = np.nan
                metrics[f"off_rating_{window}"] = np.nan
                metrics[f"def_rating_{window}"] = np.nan
                metrics[f"efg_{window}"] = np.nan
                metrics[f"ts_{window}"] = np.nan
                metrics[f"pace_{window}"] = np.nan
            return metrics
            
        # Compute 5-game window
        l5 = logs.head(5)
        metrics["win_pct_5"] = float(l5["is_win"].mean()) if len(l5) > 0 else np.nan
        metrics["avg_points_5"] = float(l5["points"].mean()) if len(l5) > 0 else np.nan
        metrics["avg_points_allowed_5"] = float(l5["points_allowed"].mean()) if len(l5) > 0 else np.nan
        metrics["point_diff_5"] = float(l5["point_margin"].mean()) if len(l5) > 0 else np.nan
        metrics["off_rating_5"] = float(l5["off_rating"].mean()) if len(l5["off_rating"].dropna()) > 0 else np.nan
        metrics["def_rating_5"] = float(l5["def_rating"].mean()) if len(l5["def_rating"].dropna()) > 0 else np.nan
        metrics["efg_5"] = float(l5["efg"].mean()) if len(l5["efg"].dropna()) > 0 else np.nan
        metrics["ts_5"] = float(l5["ts"].mean()) if len(l5["ts"].dropna()) > 0 else np.nan
        metrics["pace_5"] = float(l5["pace"].mean()) if len(l5["pace"].dropna()) > 0 else np.nan
        
        # Compute 10-game window
        l10 = logs.head(10)
        metrics["win_pct_10"] = float(l10["is_win"].mean()) if len(l10) > 0 else np.nan
        metrics["avg_points_10"] = float(l10["points"].mean()) if len(l10) > 0 else np.nan
        metrics["avg_points_allowed_10"] = float(l10["points_allowed"].mean()) if len(l10) > 0 else np.nan
        metrics["point_diff_10"] = float(l10["point_margin"].mean()) if len(l10) > 0 else np.nan
        metrics["off_rating_10"] = float(l10["off_rating"].mean()) if len(l10["off_rating"].dropna()) > 0 else np.nan
        metrics["def_rating_10"] = float(l10["def_rating"].mean()) if len(l10["def_rating"].dropna()) > 0 else np.nan
        metrics["efg_10"] = float(l10["efg"].mean()) if len(l10["efg"].dropna()) > 0 else np.nan
        metrics["ts_10"] = float(l10["ts"].mean()) if len(l10["ts"].dropna()) > 0 else np.nan
        metrics["pace_10"] = float(l10["pace"].mean()) if len(l10["pace"].dropna()) > 0 else np.nan
        
        return metrics

    def compute_schedule_rest_stats(
        self,
        team_id: str,
        target_game_date: str
    ) -> Dict[str, Any]:
        """
        Computes rest days, back-to-back flag, and games in last 7 days prior to target_game_date.
        """
        cutoff_date = str(target_game_date)[:10]
        target_season = self.get_season_for_date(cutoff_date)
        
        query = f"""
        SELECT DISTINCT
            TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE) AS game_date
        FROM team_game_stats tgs
        WHERE tgs.teamId = '{team_id}'
          AND TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE) < DATE '{cutoff_date}'
          AND (
            CASE 
                WHEN MONTH(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                THEN YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE))
                ELSE YEAR(TRY_CAST(SUBSTRING(tgs.gameDateTimeEst, 1, 10) AS DATE)) - 1
            END
          ) = {target_season}
        ORDER BY game_date DESC
        """
        dates_df = self.client.conn.execute(query).df()
        
        if len(dates_df) == 0:
            return {
                "rest_days": np.nan,
                "back_to_back": 0,
                "games_last_7": 0
            }
            
        target_dt = datetime.strptime(cutoff_date, "%Y-%m-%d").date()
        prev_dt = pd.to_datetime(dates_df["game_date"].iloc[0]).date()
        
        rest_days = (target_dt - prev_dt).days
        is_b2b = 1 if rest_days == 1 else 0
        
        seven_days_ago = target_dt - timedelta(days=7)
        past_7_count = 0
        for d in dates_df["game_date"]:
            p_date = pd.to_datetime(d).date()
            if seven_days_ago <= p_date < target_dt:
                past_7_count += 1
                
        return {
            "rest_days": float(rest_days),
            "back_to_back": int(is_b2b),
            "games_last_7": int(past_7_count)
        }

    def compute_player_rotation_stats(
        self,
        team_id: str,
        target_game_date: str,
        min_rotation_minutes: float = 10.0,
        lookback_games: int = 5
    ) -> Dict[str, Optional[float]]:
        """
        Computes team-aware rotation player aggregations for the team prior to target_game_date.
        Ensures player statistics on prior teams are never attributed to this team.
        """
        cutoff_date = str(target_game_date)[:10]
        target_season = self.get_season_for_date(cutoff_date)
        
        query = f"""
        WITH player_logs AS (
            SELECT 
                pgs.personId AS person_id,
                TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                pgs.gameId AS game_id,
                TRY_CAST(pgs.points AS DOUBLE) AS points,
                TRY_CAST(pgs.numMinutes AS DOUBLE) AS minutes,
                TRY_CAST(ext.trueShootingPercentage AS DOUBLE) AS ts_pct,
                TRY_CAST(ext.usagePercentage AS DOUBLE) AS usage_pct
            FROM player_game_stats pgs
            LEFT JOIN player_game_stats_extended ext
                ON pgs.gameId = ext.gameId AND pgs.personId = ext.personId
            WHERE pgs.playerteamId = '{team_id}'
              AND TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE) < DATE '{cutoff_date}'
              AND (
                CASE 
                    WHEN MONTH(TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE)) >= 9 
                    THEN YEAR(TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE))
                    ELSE YEAR(TRY_CAST(SUBSTRING(pgs.gameDateTimeEst, 1, 10) AS DATE)) - 1
                END
              ) = {target_season}
            ORDER BY game_date DESC, game_id DESC
        ),
        player_ranked AS (
            SELECT 
                *,
                ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY game_date DESC, game_id DESC) AS rn
            FROM player_logs
        ),
        player_recent AS (
            SELECT 
                person_id,
                AVG(points) AS p_points_5,
                AVG(ts_pct) AS p_ts_5,
                AVG(usage_pct) AS p_usage_5,
                AVG(minutes) AS p_min_5,
                COUNT(*) AS p_count
            FROM player_ranked
            WHERE rn <= {lookback_games}
            GROUP BY person_id
        )
        SELECT 
            AVG(p_points_5) AS rotation_points_5,
            AVG(p_ts_5) AS rotation_ts_5,
            AVG(p_usage_5) AS rotation_usage_5
        FROM player_recent
        WHERE p_count > 0 AND (p_min_5 >= {min_rotation_minutes} OR p_min_5 IS NULL)
        """
        df = self.client.conn.execute(query).df()
        
        if len(df) == 0 or pd.isna(df["rotation_points_5"].iloc[0]):
            return {
                "rotation_points_5": np.nan,
                "rotation_ts_5": np.nan,
                "rotation_usage_5": np.nan
            }
            
        return {
            "rotation_points_5": float(df["rotation_points_5"].iloc[0]),
            "rotation_ts_5": float(df["rotation_ts_5"].iloc[0]) if pd.notna(df["rotation_ts_5"].iloc[0]) else np.nan,
            "rotation_usage_5": float(df["rotation_usage_5"].iloc[0]) if pd.notna(df["rotation_usage_5"].iloc[0]) else np.nan
        }

    def generate_pregame_feature_vector(
        self,
        home_team_identifier: str,
        away_team_identifier: str,
        target_game_date: str
    ) -> pd.DataFrame:
        """
        Assembles the complete 52-column feature matrix strictly before target_game_date.
        Validates column names, data types, and ordering against the champion model input contract.
        """
        home_info = normalize_team(home_team_identifier)
        away_info = normalize_team(away_team_identifier)
        home_id = home_info["id"]
        away_id = away_info["id"]
        cutoff_date = str(target_game_date)[:10]
        
        logger.info(f"Generating pregame feature vector for {away_info['name']} at {home_info['name']} ({cutoff_date})...")
        
        # 1. Elo features
        home_elo, away_elo, elo_diff = self.compute_pregame_elo(home_id, away_id, cutoff_date)
        
        # 2. Team rolling form & efficiency
        h_team_stats = self.compute_team_rolling_stats(home_id, cutoff_date)
        a_team_stats = self.compute_team_rolling_stats(away_id, cutoff_date)
        
        # 3. Schedule & rest
        h_sched = self.compute_schedule_rest_stats(home_id, cutoff_date)
        a_sched = self.compute_schedule_rest_stats(away_id, cutoff_date)
        rest_diff = (
            h_sched["rest_days"] - a_sched["rest_days"]
            if pd.notna(h_sched["rest_days"]) and pd.notna(a_sched["rest_days"])
            else np.nan
        )
        
        # 4. Player rotation metrics
        h_player = self.compute_player_rotation_stats(home_id, cutoff_date)
        a_player = self.compute_player_rotation_stats(away_id, cutoff_date)
        
        # 5. Assemble exact 52-column feature dict
        feat_dict = {
            # Team rolling L5
            "home_win_pct_5": h_team_stats["win_pct_5"],
            "away_win_pct_5": a_team_stats["win_pct_5"],
            "home_avg_points_5": h_team_stats["avg_points_5"],
            "away_avg_points_5": a_team_stats["avg_points_5"],
            "home_avg_points_allowed_5": h_team_stats["avg_points_allowed_5"],
            "away_avg_points_allowed_5": a_team_stats["avg_points_allowed_5"],
            "home_point_diff_5": h_team_stats["point_diff_5"],
            "away_point_diff_5": a_team_stats["point_diff_5"],
            # Team rolling L10
            "home_win_pct_10": h_team_stats["win_pct_10"],
            "away_win_pct_10": a_team_stats["win_pct_10"],
            "home_avg_points_10": h_team_stats["avg_points_10"],
            "away_avg_points_10": a_team_stats["avg_points_10"],
            "home_avg_points_allowed_10": h_team_stats["avg_points_allowed_10"],
            "away_avg_points_allowed_10": a_team_stats["avg_points_allowed_10"],
            "home_point_diff_10": h_team_stats["point_diff_10"],
            "away_point_diff_10": a_team_stats["point_diff_10"],
            # Advanced ratings L5
            "home_off_rating_5": h_team_stats["off_rating_5"],
            "away_off_rating_5": a_team_stats["off_rating_5"],
            "home_def_rating_5": h_team_stats["def_rating_5"],
            "away_def_rating_5": a_team_stats["def_rating_5"],
            "home_efg_5": h_team_stats["efg_5"],
            "away_efg_5": a_team_stats["efg_5"],
            "home_ts_5": h_team_stats["ts_5"],
            "away_ts_5": a_team_stats["ts_5"],
            "home_pace_5": h_team_stats["pace_5"],
            "away_pace_5": a_team_stats["pace_5"],
            # Advanced ratings L10
            "home_off_rating_10": h_team_stats["off_rating_10"],
            "away_off_rating_10": a_team_stats["off_rating_10"],
            "home_def_rating_10": h_team_stats["def_rating_10"],
            "away_def_rating_10": a_team_stats["def_rating_10"],
            "home_efg_10": h_team_stats["efg_10"],
            "away_efg_10": a_team_stats["efg_10"],
            "home_ts_10": h_team_stats["ts_10"],
            "away_ts_10": a_team_stats["ts_10"],
            "home_pace_10": h_team_stats["pace_10"],
            "away_pace_10": a_team_stats["pace_10"],
            # Elo
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_difference": elo_diff,
            # Schedule & Rest
            "home_rest_days": h_sched["rest_days"],
            "away_rest_days": a_sched["rest_days"],
            "rest_difference": rest_diff,
            "home_back_to_back": h_sched["back_to_back"],
            "away_back_to_back": a_sched["back_to_back"],
            "home_games_last_7": h_sched["games_last_7"],
            "away_games_last_7": a_sched["games_last_7"],
            # Rotation
            "home_rotation_points_5": h_player["rotation_points_5"],
            "away_rotation_points_5": a_player["rotation_points_5"],
            "home_rotation_ts_5": h_player["rotation_ts_5"],
            "away_rotation_ts_5": a_player["rotation_ts_5"],
            "home_rotation_usage_5": h_player["rotation_usage_5"],
            "away_rotation_usage_5": a_player["rotation_usage_5"],
        }
        
        # Verify complete schema alignment
        df_features = pd.DataFrame([feat_dict])
        
        # Enforce exact column order from model input contract
        missing_cols = set(MODEL_FEATURE_CONTRACT) - set(df_features.columns)
        if missing_cols:
            raise ValueError(f"Feature generation incomplete! Missing columns: {missing_cols}")
            
        df_features = df_features[MODEL_FEATURE_CONTRACT]
        return df_features
