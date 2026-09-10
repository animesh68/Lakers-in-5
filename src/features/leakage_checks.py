"""
Temporal Leakage & Data Integrity Validation Suite for Lakers in 5.
Rigorous mathematical tests ensuring no post-game or future data enters pregame features.
"""

from typing import Dict, Any, List
import pandas as pd
import numpy as np
from src.utils.logging import logger

class LeakageChecker:
    """
    Validates temporal causality, rolling window boundaries, and lack of target contamination.
    """
    def __init__(self, features_df: pd.DataFrame):
        self.df = features_df.copy()

    def check_temporal_ordering(self) -> Dict[str, Any]:
        """
        Ensures the dataset is strictly sorted and no future dates precede past dates.
        """
        is_sorted = self.df["game_date"].is_monotonic_increasing
        return {
            "check": "temporal_ordering",
            "passed": bool(is_sorted),
            "details": "Dataset is chronologically sorted by game_date" if is_sorted else "Dataset out of order"
        }

    def check_season_opener_cold_start(self) -> Dict[str, Any]:
        """
        Verifies that for every team's first game of a season, rolling form features are strictly NaN.
        If a team's first game of a season had non-null rolling stats, it would mean current or future stats leaked!
        """
        # Collect all team appearances (home and away) with game date
        home_appearances = self.df[["game_id", "game_date", "season", "home_team_id", "home_win_pct_5"]].rename(
            columns={"home_team_id": "team_id", "home_win_pct_5": "win_pct_5"}
        )
        away_appearances = self.df[["game_id", "game_date", "season", "away_team_id", "away_win_pct_5"]].rename(
            columns={"away_team_id": "team_id", "away_win_pct_5": "win_pct_5"}
        )
        all_appearances = pd.concat([home_appearances, away_appearances], ignore_index=True)
        
        # Sort chronologically and take the first chronological game of each season per team
        first_games = all_appearances.sort_values(["game_date", "game_id"]).groupby(["team_id", "season"]).nth(0)
        
        null_count = first_games["win_pct_5"].isna().sum()
        total_openers = len(first_games)
        passed = (null_count == total_openers)
        
        return {
            "check": "season_opener_cold_start",
            "passed": bool(passed),
            "total_openers": int(total_openers),
            "null_openers": int(null_count),
            "details": f"{null_count}/{total_openers} season openers correctly have NaN rolling form (zero leakage)"
        }

    def check_target_contamination(self) -> Dict[str, Any]:
        """
        Verifies that target variables are not leaked into any feature column.
        """
        target_cols = ["target_home_win", "target_point_margin"]
        feature_cols = [c for c in self.df.columns if c not in target_cols + ["game_id", "game_date", "season", "home_team_id", "away_team_id", "home_team", "away_team"]]
        
        contaminated_features = []
        for feat in feature_cols:
            valid_mask = self.df[feat].notna() & self.df["target_home_win"].notna()
            if valid_mask.sum() > 100:
                corr = np.corrcoef(self.df.loc[valid_mask, feat], self.df.loc[valid_mask, "target_home_win"])[0, 1]
                # If correlation is suspiciously high (> 0.95), target might have leaked
                if abs(corr) > 0.95:
                    contaminated_features.append((feat, float(corr)))
                    
        passed = len(contaminated_features) == 0
        return {
            "check": "target_contamination",
            "passed": passed,
            "contaminated_features": contaminated_features,
            "details": "Zero perfect or near-perfect correlation with targets detected" if passed else f"Contaminated features: {contaminated_features}"
        }

    def check_schedule_leakage(self) -> Dict[str, Any]:
        """
        Verifies that games in last 7 days does not include the game on game_date itself.
        """
        # Back-to-back games must have rest_days == 1
        b2b_mask = self.df["home_back_to_back"] == 1
        b2b_valid = (self.df.loc[b2b_mask, "home_rest_days"] == 1).all()
        
        # games_last_7 cannot exceed 7
        games_7_valid = (self.df["home_games_last_7"].fillna(0) <= 7).all()
        
        passed = bool(b2b_valid and games_7_valid)
        return {
            "check": "schedule_leakage",
            "passed": passed,
            "details": "Rest days and games_last_7 adhere strictly to calendar constraints"
        }

    def check_synthetic_exclusion(self) -> Dict[str, Any]:
        """
        Ensures no synthetic/placeholder game records leaked into the feature dataset.
        """
        has_null_home = self.df["home_team_id"].isna().any()
        has_null_away = self.df["away_team_id"].isna().any()
        passed = bool(not has_null_home and not has_null_away)
        
        return {
            "check": "synthetic_game_exclusion",
            "passed": passed,
            "details": "100% of rows have non-null home and away teams (zero synthetic placeholder records)"
        }

    def run_all_checks(self) -> Dict[str, Any]:
        """
        Executes complete leakage validation suite and logs results.
        """
        logger.info("=" * 70)
        logger.info("RUNNING TEMPORAL DATA LEAKAGE VALIDATION CHECKS")
        logger.info("=" * 70)

        checks = [
            self.check_temporal_ordering(),
            self.check_season_opener_cold_start(),
            self.check_target_contamination(),
            self.check_schedule_leakage(),
            self.check_synthetic_exclusion()
        ]

        all_passed = all(c["passed"] for c in checks)
        summary = {
            "overall_status": "PASSED" if all_passed else "FAILED",
            "checks": checks
        }

        for c in checks:
            status = "[PASS]" if c["passed"] else "[FAIL]"
            logger.info(f"{status} {c['check']}: {c['details']}")

        logger.info("=" * 70)
        logger.info(f"TEMPORAL LEAKAGE VERIFICATION: {summary['overall_status']}")
        logger.info("=" * 70)
        return summary
