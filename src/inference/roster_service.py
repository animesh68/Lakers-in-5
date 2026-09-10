"""
Offseason Transaction and Roster Awareness Service for 2026-27 Season.
Parses nba_2026_offseason_transactions.csv to track player additions, departures, and team assignments.
"""

import os
from typing import Dict, Any, Optional, List, Set
import pandas as pd
from src.inference.schedule_service import normalize_team
from src.utils.logging import logger

class RosterService:
    """
    Ingests official 2026 offseason transactions to track player movements,
    re-signings, additions, and departures across all NBA teams.
    """
    def __init__(self, transactions_csv_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.csv_path = transactions_csv_path or os.path.join(
            base_dir, "data", "raw", "transactions", "nba_2026_offseason_transactions.csv"
        )
        self._transactions_df: Optional[pd.DataFrame] = None

    def load_transactions(self) -> pd.DataFrame:
        if self._transactions_df is not None:
            return self._transactions_df
            
        if not os.path.exists(self.csv_path):
            logger.warning(f"Transactions CSV not found at {self.csv_path}")
            return pd.DataFrame()
            
        df = pd.read_csv(self.csv_path)
        # Normalize team names to standard franchise info
        normalized_team_ids = []
        for team_name in df["Team"]:
            try:
                t_info = normalize_team(team_name)
                normalized_team_ids.append(t_info["id"])
            except Exception:
                normalized_team_ids.append(None)
                
        df["team_id"] = normalized_team_ids
        self._transactions_df = df
        return df

    def get_team_transactions(self, team_identifier: str) -> List[Dict[str, Any]]:
        """Retrieves all 2026 offseason transactions for a team."""
        team_info = normalize_team(team_identifier)
        df = self.load_transactions()
        if len(df) == 0:
            return []
            
        match = df[df["team_id"] == team_info["id"]]
        return match.to_dict(orient="records")

    def get_team_additions(self, team_identifier: str) -> List[str]:
        """Returns list of players acquired by the team in the 2026 offseason."""
        txs = self.get_team_transactions(team_identifier)
        return [t["Player"] for t in txs if t.get("Category") == "Additions"]

    def get_team_departures(self, team_identifier: str) -> List[str]:
        """Returns list of players who departed the team in the 2026 offseason."""
        txs = self.get_team_transactions(team_identifier)
        return [t["Player"] for t in txs if t.get("Category") == "Departures"]
