"""
Elo Rating System for Lakers in 5.
Calculates chronological pregame Elo ratings with configurable K-factor, home advantage, and season mean reversion.
"""

from typing import Dict, Any, Tuple, Optional
import pandas as pd
import numpy as np
from src.utils.logging import logger

class EloCalculator:
    """
    Computes chronological, leakage-safe pregame Elo ratings for NBA franchises.
    """
    def __init__(
        self,
        initial_elo: float = 1500.0,
        k_factor: float = 20.0,
        home_advantage: float = 100.0,
        season_reversion: float = 0.25
    ):
        self.initial_elo = initial_elo
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.season_reversion = season_reversion
        self.ratings: Dict[str, float] = {}

    def get_rating(self, team_id: str) -> float:
        """Returns the current Elo rating for a team, initialized to initial_elo if not seen."""
        return self.ratings.get(str(team_id), self.initial_elo)

    def expected_win_prob(self, rating_a: float, rating_b: float) -> float:
        """Computes expected win probability for team A against team B."""
        return 1.0 / (1.0 + 10.0 ** ((rating_b - rating_a) / 400.0))

    def compute_elo_features(self, games_df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes a DataFrame of official games sorted chronologically by (game_date, game_id),
        computes strictly pregame Elo features, and updates team ratings sequentially.
        """
        logger.info("Computing chronological pregame Elo ratings...")
        
        # Ensure chronological ordering
        df = games_df.sort_values(by=["game_date", "game_id"]).copy()
        
        home_elos = []
        away_elos = []
        elo_diffs = []
        
        current_season = None
        self.ratings.clear()

        for idx, row in df.iterrows():
            season = row.get("season")
            home_team = str(row.get("home_team_id"))
            away_team = str(row.get("away_team_id"))
            
            # Apply season reversion when crossing into a new season
            if current_season is not None and season != current_season:
                for t in self.ratings:
                    self.ratings[t] = (1.0 - self.season_reversion) * self.ratings[t] + self.season_reversion * self.initial_elo
            current_season = season

            # 1. Capture STRICT PREGAME Elo ratings before the game takes place
            pre_home_elo = self.get_rating(home_team)
            pre_away_elo = self.get_rating(away_team)
            
            # Effective home Elo includes home court advantage
            effective_home_elo = pre_home_elo + self.home_advantage
            elo_diff = effective_home_elo - pre_away_elo
            
            home_elos.append(pre_home_elo)
            away_elos.append(pre_away_elo)
            elo_diffs.append(elo_diff)

            # 2. Update Elo ratings post-game based on actual result
            home_score = row.get("home_score")
            away_score = row.get("away_score")
            if pd.notna(home_score) and pd.notna(away_score):
                home_win = 1.0 if float(home_score) > float(away_score) else 0.0
                exp_home_win = self.expected_win_prob(effective_home_elo, pre_away_elo)
                
                # Standard Elo update
                delta = self.k_factor * (home_win - exp_home_win)
                self.ratings[home_team] = pre_home_elo + delta
                self.ratings[away_team] = pre_away_elo - delta

        df["home_elo"] = home_elos
        df["away_elo"] = away_elos
        df["elo_difference"] = elo_diffs
        
        logger.info(f"Computed Elo ratings for {len(df):,} games across NBA history.")
        return df[["game_id", "home_elo", "away_elo", "elo_difference"]]
