"""
Outcome Ingestion Service for Lakers in 5.
Identifies pending predictions, verifies completed game results in the analytical lakehouse,
and idempotently updates actual scores, win indicators, and margins.
"""

import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import duckdb

from src.monitoring.repository import PredictionRepository
from src.monitoring.store import PredictionRecord
from src.utils.logging import logger

class OutcomeIngestionService:
    """
    Settles pending predictions by looking up completed game results in the analytical lakehouse.
    """
    def __init__(
        self,
        repository: Optional[PredictionRepository] = None,
        parquet_games_path: Optional[str] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.repo = repository or PredictionRepository()
        self.games_path = parquet_games_path or os.path.join(
            base_dir, "data", "processed", "parquet", "games.parquet"
        )

    def update_pending_outcomes(self) -> Dict[str, Any]:
        """
        Finds all pending predictions and updates their actual outcomes if the game has completed.
        Returns a summary report of settled and remaining pending predictions.
        """
        pending_preds = self.repo.get_predictions(status="pending", limit=10000)
        if not pending_preds:
            logger.info("No pending predictions found to update.")
            return {
                "checked_count": 0,
                "updated_count": 0,
                "pending_remaining": 0
            }

        if not os.path.exists(self.games_path):
            logger.warning(f"Authoritative games parquet not found at {self.games_path}.")
            return {
                "checked_count": len(pending_preds),
                "updated_count": 0,
                "pending_remaining": len(pending_preds),
                "error": "games_parquet_not_found"
            }

        con = duckdb.connect()
        updates = []
        try:
            # Query column names first to handle both camelCase and snake_case schemas
            con.execute(f"SELECT * FROM '{self.games_path}' LIMIT 1")
            col_names = [desc[0] for desc in con.description]
            
            gid_col = "gameId" if "gameId" in col_names else "game_id"
            gdate_col = "gameDate" if "gameDate" in col_names else "game_date"
            hid_col = "hometeamId" if "hometeamId" in col_names else "home_team_id"
            aid_col = "awayteamId" if "awayteamId" in col_names else "away_team_id"
            hscore_col = "homeScore" if "homeScore" in col_names else "home_score"
            ascore_col = "awayScore" if "awayScore" in col_names else "away_score"

            query = f"""
                SELECT 
                    CAST({gid_col} AS VARCHAR) AS game_id,
                    CAST({gdate_col} AS VARCHAR) AS game_date,
                    CAST({hid_col} AS VARCHAR) AS home_team_id,
                    CAST({aid_col} AS VARCHAR) AS away_team_id,
                    {hscore_col} AS home_score,
                    {ascore_col} AS away_score
                FROM '{self.games_path}'
                WHERE {hscore_col} IS NOT NULL AND {ascore_col} IS NOT NULL
            """
            games_df = con.execute(query).df()

            for pred in pending_preds:
                match = None
                # 1. Match by game_id if available
                if pred.game_id:
                    m = games_df[games_df["game_id"] == str(pred.game_id)]
                    if not m.empty:
                        match = m.iloc[0]

                # 2. Match by teams and date if game_id didn't match
                if match is None:
                    p_date = pred.game_date[:10]
                    m = games_df[
                        (games_df["game_date"].str[:10] == p_date) &
                        (games_df["home_team_id"] == str(pred.home_team_id)) &
                        (games_df["away_team_id"] == str(pred.away_team_id))
                    ]
                    if not m.empty:
                        match = m.iloc[0]

                if match is not None:
                    h_score = int(match["home_score"])
                    a_score = int(match["away_score"])
                    h_win = 1 if h_score > a_score else 0
                    margin = float(h_score - a_score)

                    updates.append({
                        "prediction_id": pred.prediction_id,
                        "actual_home_score": h_score,
                        "actual_away_score": a_score,
                        "actual_home_win": h_win,
                        "actual_home_margin": margin,
                    })

            updated_count = self.repo.update_outcomes(updates)
            remaining = len(pending_preds) - updated_count
            logger.info(f"Outcome ingestion complete: {updated_count} settled, {remaining} pending.")
            return {
                "checked_count": len(pending_preds),
                "updated_count": updated_count,
                "pending_remaining": remaining
            }
        finally:
            con.close()
