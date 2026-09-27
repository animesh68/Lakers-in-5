"""
Player Performance Prediction Feature Engineering Pipeline for Phase 8.
Constructs strictly pregame, leakage-safe feature vectors for individual player predictions
(Minutes, Points, Rebounds, Assists) with principled cold-start fallback shrinkage and
full train/serve parity.
"""

import os
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
import duckdb

from src.inference.roster_service import RosterService, normalize_player_name
from src.inference.schedule_service import normalize_team
from src.utils.logging import logger

# Canonical 24-Feature Contract for Individual Player Performance Models
PLAYER_FEATURE_CONTRACT = [
    # Player Rolling Form & Volume
    "player_min_avg_5",
    "player_min_avg_10",
    "player_min_season_avg",
    "player_pts_per_min_10",
    "player_reb_per_min_10",
    "player_ast_per_min_10",
    "player_ts_pct_10",
    "player_usage_pct_10",
    "is_starter_ratio_10",
    "player_games_played_season",
    
    # Schedule, Rest & Venue
    "is_home",
    "days_since_last_game",
    "is_b2b",
    
    # Team & Opponent Context
    "team_pace_10",
    "opponent_pace_10",
    "opponent_def_rating_10",
    "team_off_rating_10",
    
    # Transaction & Roster Transition Awareness
    "is_team_change",
    "days_since_team_change",
    "games_with_current_team",
    "prior_team_min_avg",
    "prior_team_pts_per_min",
    "prior_team_reb_per_min",
    "prior_team_ast_per_min",
]

# Principled League Priors for Cold-Start / Rookie Fallback Shrinkage
LEAGUE_PRIORS = {
    "min_avg": 18.5,
    "pts_per_min": 0.46,
    "reb_per_min": 0.19,
    "ast_per_min": 0.10,
    "ts_pct": 0.54,
    "usage_pct": 0.18,
    "pace": 99.5,
    "off_rating": 112.0,
    "def_rating": 112.0,
}


class PlayerFeatureEngine:
    """
    Computes leakage-safe player feature vectors as-of any target game date.
    Maintains exact parity across batch historical model training and online serving.
    """
    def __init__(
        self,
        duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None,
        parquet_path: Optional[str] = None,
        roster_service: Optional[RosterService] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.parquet_path = parquet_path or os.path.join(
            base_dir, "data", "processed", "parquet", "player_game_stats.parquet"
        )
        self.team_parquet_path = os.path.join(
            base_dir, "data", "processed", "parquet", "team_game_stats.parquet"
        )
        self.conn = duckdb_conn
        self.roster_service = roster_service or RosterService()

    def extract_pregame_player_features(
        self,
        person_id: str,
        team_id: str,
        opponent_team_id: str,
        target_game_date: str,
        is_home: bool = True,
        player_meta: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Extracts the 24 canonical pregame features for an individual player strictly before target_game_date.
        Never observes target game statistics or future transactions.
        """
        cutoff_date = str(target_game_date)[:10]
        dt_target = datetime.strptime(cutoff_date, "%Y-%m-%d")
        con = self.conn or duckdb.connect()

        # 1. Query Player Rolling Statistics strictly before cutoff
        try:
            player_query = f"""
            WITH raw_player_games AS (
                SELECT 
                    personId AS person_id,
                    playerteamId AS team_id,
                    TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                    TRY_CAST(numMinutes AS DOUBLE) AS minutes,
                    TRY_CAST(points AS DOUBLE) AS points,
                    TRY_CAST(reboundsTotal AS DOUBLE) AS rebounds,
                    TRY_CAST(assists AS DOUBLE) AS assists,
                    TRY_CAST(fieldGoalsAttempted AS DOUBLE) AS fga,
                    TRY_CAST(freeThrowsAttempted AS DOUBLE) AS fta,
                    TRY_CAST(turnovers AS DOUBLE) AS tov,
                    CASE WHEN startingPosition IS NOT NULL AND startingPosition != '' THEN 1.0 ELSE 0.0 END AS is_starter
                FROM '{self.parquet_path}'
                WHERE personId = '{person_id}'
                  AND TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) < '{cutoff_date}'
                ORDER BY game_date DESC
            )
            SELECT * FROM raw_player_games LIMIT 25
            """
            p_games_df = con.execute(player_query).df()
        except Exception as e:
            logger.warning(f"Error querying player stats for {person_id}: {e}")
            p_games_df = pd.DataFrame()

        # 2. Query Team & Opponent Context
        try:
            team_query = f"""
            WITH team_games AS (
                SELECT 
                    teamId AS team_id,
                    TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                    TRY_CAST(teamScore AS DOUBLE) AS team_score,
                    TRY_CAST(opponentScore AS DOUBLE) AS opp_score,
                    TRY_CAST(fieldGoalsAttempted AS DOUBLE) + 0.44 * TRY_CAST(freeThrowsAttempted AS DOUBLE) + TRY_CAST(turnovers AS DOUBLE) AS est_possessions
                FROM '{self.team_parquet_path}'
                WHERE teamId IN ('{team_id}', '{opponent_team_id}')
                  AND TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) < '{cutoff_date}'
                ORDER BY game_date DESC
            )
            SELECT * FROM team_games
            """
            team_games_df = con.execute(team_query).df()
        except Exception as e:
            team_games_df = pd.DataFrame()
        finally:
            if self.conn is None:
                con.close()

        # Process Player Rolling Features with principled shrinkage
        n_games = len(p_games_df)
        
        # Determine current team games vs prior team
        if player_meta is None:
            # Deducing from history
            current_team_games = p_games_df[p_games_df["team_id"] == str(team_id)]
            is_team_change = len(p_games_df) > 0 and str(p_games_df.iloc[0]["team_id"]) != str(team_id)
            games_with_current_team = len(current_team_games)
            days_since_change = 0
            prior_team_games = p_games_df[p_games_df["team_id"] != str(team_id)]
        else:
            is_team_change = bool(player_meta.get("is_transition_player", False))
            games_with_current_team = int(player_meta.get("games_with_current_team", 0))
            days_since_change = int(player_meta.get("days_since_team_change", 0))
            prior_team_games = p_games_df

        # Rolling averages across last 5 and 10 games
        if n_games > 0:
            df5 = p_games_df.head(5)
            df10 = p_games_df.head(10)

            # Last game recency and b2b
            last_date_str = str(p_games_df.iloc[0]["game_date"])[:10]
            dt_last = datetime.strptime(last_date_str, "%Y-%m-%d")
            days_since_last_game = max(1, (dt_target - dt_last).days)
            is_b2b = 1.0 if days_since_last_game == 1 else 0.0

            # Minutes averages
            player_min_avg_5 = float(df5["minutes"].mean()) if len(df5) > 0 else LEAGUE_PRIORS["min_avg"]
            player_min_avg_10 = float(df10["minutes"].mean()) if len(df10) > 0 else LEAGUE_PRIORS["min_avg"]
            player_min_season_avg = float(p_games_df["minutes"].mean())

            # Per-minute production rates (prevent division by zero via smoothing)
            tot_min_10 = max(1.0, float(df10["minutes"].sum()))
            player_pts_per_min_10 = float(df10["points"].sum()) / tot_min_10
            player_reb_per_min_10 = float(df10["rebounds"].sum()) / tot_min_10
            player_ast_per_min_10 = float(df10["assists"].sum()) / tot_min_10

            # TS% estimation: PTS / (2 * (FGA + 0.44 * FTA))
            tot_pts_10 = float(df10["points"].sum())
            tot_fga_10 = float(df10["fga"].sum())
            tot_fta_10 = float(df10["fta"].sum())
            ts_denom = 2.0 * (tot_fga_10 + 0.44 * tot_fta_10)
            player_ts_pct_10 = (tot_pts_10 / ts_denom) if ts_denom > 0 else LEAGUE_PRIORS["ts_pct"]

            # Usage estimation: 100 * ((FGA + 0.44*FTA + TOV) * (TeamMin / 5)) / (PlayerMin * TeamPoss)
            # Simplified proxy: per-minute possession load
            player_usage_pct_10 = min(0.40, max(0.10, (tot_fga_10 + 0.44 * tot_fta_10 + float(df10["tov"].sum())) / max(1.0, tot_min_10 * 2.0)))

            is_starter_ratio_10 = float(df10["is_starter"].mean())
            player_games_played_season = float(min(82, n_games))
        else:
            # Complete Cold Start / Rookie Fallback
            days_since_last_game = 120.0
            is_b2b = 0.0
            player_min_avg_5 = LEAGUE_PRIORS["min_avg"]
            player_min_avg_10 = LEAGUE_PRIORS["min_avg"]
            player_min_season_avg = LEAGUE_PRIORS["min_avg"]
            player_pts_per_min_10 = LEAGUE_PRIORS["pts_per_min"]
            player_reb_per_min_10 = LEAGUE_PRIORS["reb_per_min"]
            player_ast_per_min_10 = LEAGUE_PRIORS["ast_per_min"]
            player_ts_pct_10 = LEAGUE_PRIORS["ts_pct"]
            player_usage_pct_10 = LEAGUE_PRIORS["usage_pct"]
            is_starter_ratio_10 = 0.5
            player_games_played_season = 0.0

        # Prior Team History Metrics
        if len(prior_team_games) > 0:
            df_prior = prior_team_games.head(15)
            tot_prior_min = max(1.0, float(df_prior["minutes"].sum()))
            prior_team_min_avg = float(df_prior["minutes"].mean())
            prior_team_pts_per_min = float(df_prior["points"].sum()) / tot_prior_min
            prior_team_reb_per_min = float(df_prior["rebounds"].sum()) / tot_prior_min
            prior_team_ast_per_min = float(df_prior["assists"].sum()) / tot_prior_min
        else:
            prior_team_min_avg = LEAGUE_PRIORS["min_avg"]
            prior_team_pts_per_min = LEAGUE_PRIORS["pts_per_min"]
            prior_team_reb_per_min = LEAGUE_PRIORS["reb_per_min"]
            prior_team_ast_per_min = LEAGUE_PRIORS["ast_per_min"]

        # Team & Opponent Rolling Pace and Ratings
        t_games = team_games_df[team_games_df["team_id"] == str(team_id)].head(10)
        opp_games = team_games_df[team_games_df["team_id"] == str(opponent_team_id)].head(10)

        team_pace_10 = float(t_games["est_possessions"].mean()) if len(t_games) > 0 else LEAGUE_PRIORS["pace"]
        team_off_rating_10 = float((t_games["team_score"] / t_games["est_possessions"] * 100).mean()) if len(t_games) > 0 else LEAGUE_PRIORS["off_rating"]

        opponent_pace_10 = float(opp_games["est_possessions"].mean()) if len(opp_games) > 0 else LEAGUE_PRIORS["pace"]
        opponent_def_rating_10 = float((opp_games["opp_score"] / opp_games["est_possessions"] * 100).mean()) if len(opp_games) > 0 else LEAGUE_PRIORS["def_rating"]

        feature_vector = {
            "player_min_avg_5": round(player_min_avg_5, 3),
            "player_min_avg_10": round(player_min_avg_10, 3),
            "player_min_season_avg": round(player_min_season_avg, 3),
            "player_pts_per_min_10": round(player_pts_per_min_10, 4),
            "player_reb_per_min_10": round(player_reb_per_min_10, 4),
            "player_ast_per_min_10": round(player_ast_per_min_10, 4),
            "player_ts_pct_10": round(player_ts_pct_10, 4),
            "player_usage_pct_10": round(player_usage_pct_10, 4),
            "is_starter_ratio_10": round(is_starter_ratio_10, 3),
            "player_games_played_season": round(player_games_played_season, 1),
            "is_home": 1.0 if is_home else 0.0,
            "days_since_last_game": round(float(days_since_last_game), 1),
            "is_b2b": float(is_b2b),
            "team_pace_10": round(team_pace_10, 2),
            "opponent_pace_10": round(opponent_pace_10, 2),
            "opponent_def_rating_10": round(opponent_def_rating_10, 2),
            "team_off_rating_10": round(team_off_rating_10, 2),
            "is_team_change": 1.0 if is_team_change else 0.0,
            "days_since_team_change": round(float(days_since_change), 1),
            "games_with_current_team": float(games_with_current_team),
            "prior_team_min_avg": round(prior_team_min_avg, 3),
            "prior_team_pts_per_min": round(prior_team_pts_per_min, 4),
            "prior_team_reb_per_min": round(prior_team_reb_per_min, 4),
            "prior_team_ast_per_min": round(prior_team_ast_per_min, 4),
        }

        return feature_vector
