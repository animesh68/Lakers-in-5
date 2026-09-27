"""
Roster, Transaction, and Player Eligibility Service for Phase 8.
Tracks 2026 offseason transactions, roster movements, and determines canonical pregame
player eligibility universes as-of target game dates without temporal lookahead.
"""

import os
import re
import unicodedata
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, date
import pandas as pd
import duckdb

from src.inference.schedule_service import normalize_team
from src.utils.logging import logger


def normalize_player_name(name: str) -> str:
    """Strips accents, typographic punctuation, and lowercases for canonical matching."""
    if not isinstance(name, str):
        return ""
    s = name.replace("’", "'").replace("`", "'").replace("´", "'")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return s.replace("'", "").replace(".", "").replace("-", " ").lower().strip()


class RosterService:
    """
    Roster & Transaction Resolver.
    Maintains player franchise assignments, tracks offseason player additions/departures,
    and produces the canonical pregame player universe as of any target game date.
    """
    def __init__(
        self,
        transactions_csv_path: Optional[str] = None,
        parquet_path: Optional[str] = None,
        duckdb_conn: Optional[duckdb.DuckDBPyConnection] = None
    ):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.csv_path = transactions_csv_path or os.path.join(
            base_dir, "data", "raw", "transactions", "nba_2026_offseason_transactions.csv"
        )
        self.parquet_path = parquet_path or os.path.join(
            base_dir, "data", "processed", "parquet", "player_game_stats.parquet"
        )
        self.players_csv_path = os.path.join(base_dir, "data", "raw", "players", "Players.csv")
        self.conn = duckdb_conn
        
        self._transactions_df: Optional[pd.DataFrame] = None
        self._player_id_map: Optional[Dict[str, str]] = None
        self._id_to_name_map: Optional[Dict[str, str]] = None
        self._player_positions: Optional[Dict[str, str]] = None

    def _init_player_maps(self):
        """Initializes player name <-> personId bidirectional lookup tables."""
        if self._player_id_map is not None:
            return

        id_map: Dict[str, str] = {}
        name_map: Dict[str, str] = {}
        pos_map: Dict[str, str] = {}

        # 1. Load from player_game_stats.parquet (most authoritative)
        if os.path.exists(self.parquet_path):
            con = self.conn or duckdb.connect()
            try:
                p_df = con.execute(f"""
                    SELECT DISTINCT 
                        personId, 
                        concat(firstName, ' ', lastName) as full_name
                    FROM '{self.parquet_path}'
                """).df()
                for _, row in p_df.iterrows():
                    pid = str(row['personId'])
                    raw_name = str(row['full_name']).strip()
                    norm_name = normalize_player_name(raw_name)
                    id_map[norm_name] = pid
                    id_map[raw_name.lower()] = pid
                    name_map[pid] = raw_name
            except Exception as e:
                logger.warning(f"Failed to load player stats mapping from parquet: {e}")
            finally:
                if self.conn is None:
                    con.close()

        # 2. Augment from Players.csv
        if os.path.exists(self.players_csv_path):
            try:
                csv_df = pd.read_csv(self.players_csv_path)
                for _, row in csv_df.iterrows():
                    pid = str(row['personId'])
                    raw_name = f"{row.get('firstName', '')} {row.get('lastName', '')}".strip()
                    norm_name = normalize_player_name(raw_name)
                    if norm_name not in id_map:
                        id_map[norm_name] = pid
                    if raw_name.lower() not in id_map:
                        id_map[raw_name.lower()] = pid
                    if pid not in name_map and raw_name:
                        name_map[pid] = raw_name
                    
                    # Position
                    pos = "F" if row.get("forward") == 1 else "C" if row.get("center") == 1 else "G"
                    pos_map[pid] = pos
            except Exception as e:
                logger.warning(f"Failed to load Players.csv mapping: {e}")

        self._player_id_map = id_map
        self._id_to_name_map = name_map
        self._player_positions = pos_map

    def resolve_player_id(self, player_name: str) -> str:
        """Resolves a player full name to canonical personId."""
        self._init_player_maps()
        norm = normalize_player_name(player_name)
        if norm in self._player_id_map:
            return self._player_id_map[norm]
        if player_name.lower().strip() in self._player_id_map:
            return self._player_id_map[player_name.lower().strip()]
        
        # Deterministic hash fallback for international/untracked rookies
        synthetic_id = f"R-{abs(hash(norm)) % 10000000:07d}"
        self._player_id_map[norm] = synthetic_id
        self._id_to_name_map[synthetic_id] = player_name
        return synthetic_id

    def resolve_player_name(self, person_id: str) -> str:
        """Resolves personId to human-readable player name."""
        self._init_player_maps()
        return self._id_to_name_map.get(str(person_id), f"Player #{person_id}")

    def load_transactions(self) -> pd.DataFrame:
        """Loads and normalizes 2026 offseason transactions."""
        if self._transactions_df is not None:
            return self._transactions_df

        if not os.path.exists(self.csv_path):
            logger.warning(f"Transactions CSV not found at {self.csv_path}")
            return pd.DataFrame()

        df = pd.read_csv(self.csv_path)
        self._init_player_maps()

        team_ids = []
        team_codes = []
        person_ids = []

        for _, row in df.iterrows():
            t_name = str(row["Team"])
            try:
                t_info = normalize_team(t_name)
                team_ids.append(t_info["id"])
                team_codes.append(t_info["code"])
            except Exception:
                team_ids.append(None)
                team_codes.append(None)
            
            p_name = str(row["Player"])
            person_ids.append(self.resolve_player_id(p_name))

        df["team_id"] = team_ids
        df["team_code"] = team_codes
        df["person_id"] = person_ids
        # Canonical transaction date for 2026 offseason is July 1, 2026
        df["transaction_date"] = "2026-07-01"

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

    def get_team_additions(self, team_identifier: str) -> List[Dict[str, Any]]:
        """Returns list of player additions acquired by the team in the 2026 offseason."""
        txs = self.get_team_transactions(team_identifier)
        return [t for t in txs if t.get("Category") == "Additions"]

    def get_team_departures(self, team_identifier: str) -> List[Dict[str, Any]]:
        """Returns list of players who departed the team in the 2026 offseason."""
        txs = self.get_team_transactions(team_identifier)
        return [t for t in txs if t.get("Category") == "Departures"]

    def get_active_roster_universe(
        self,
        team_identifier: str,
        as_of_date: str,
        max_players: int = 15
    ) -> List[Dict[str, Any]]:
        """
        Constructs the canonical pregame eligible player universe for a team as-of target date D.
        Strictly leakage-safe: utilizes historical games strictly before as_of_date and
        chronological 2026 offseason transaction state.
        """
        team_info = normalize_team(team_identifier)
        team_id = team_info["id"]
        team_code = team_info["code"]
        team_name = team_info["name"]

        self._init_player_maps()
        df_tx = self.load_transactions()

        # Check if as_of_date reflects post-2026-offseason state (2026-07-01 onwards)
        dt_target = datetime.strptime(str(as_of_date)[:10], "%Y-%m-%d")
        is_post_offseason_2026 = dt_target >= datetime(2026, 7, 1)

        # 1. Query recent historical rotation players for this team strictly before as_of_date
        con = self.conn or duckdb.connect()
        cutoff_date = str(as_of_date)[:10]

        try:
            # Query players who logged minutes for this team in the most recent active window before cutoff
            hist_query = f"""
            WITH player_team_games AS (
                SELECT 
                    personId AS person_id,
                    playerteamId AS team_id,
                    TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) AS game_date,
                    TRY_CAST(numMinutes AS DOUBLE) AS minutes,
                    TRY_CAST(points AS DOUBLE) AS points,
                    TRY_CAST(reboundsTotal AS DOUBLE) AS rebounds,
                    TRY_CAST(assists AS DOUBLE) AS assists
                FROM '{self.parquet_path}'
                WHERE playerteamId = '{team_id}'
                  AND TRY_CAST(SUBSTRING(gameDateTimeEst, 1, 10) AS DATE) < '{cutoff_date}'
            ),
            player_agg AS (
                SELECT 
                    person_id,
                    COUNT(*) as games_with_team,
                    MAX(game_date) as last_game_date,
                    AVG(minutes) as avg_minutes,
                    AVG(points) as avg_points,
                    AVG(rebounds) as avg_rebounds,
                    AVG(assists) as avg_assists
                FROM player_team_games
                GROUP BY person_id
            )
            SELECT *
            FROM player_agg
            WHERE games_with_team >= 1
            ORDER BY last_game_date DESC, avg_minutes DESC
            """
            hist_players_df = con.execute(hist_query).df()
        except Exception as e:
            logger.warning(f"Error querying historical roster: {e}")
            hist_players_df = pd.DataFrame()
        finally:
            if self.conn is None:
                con.close()

        # Build active roster dictionary keyed by person_id
        active_roster: Dict[str, Dict[str, Any]] = {}

        # Populate from historical roster if player active within 18 months of cutoff
        for _, row in hist_players_df.iterrows():
            pid = str(row["person_id"])
            last_date = str(row["last_game_date"])
            dt_last = datetime.strptime(last_date[:10], "%Y-%m-%d")
            days_since_last = (dt_target - dt_last).days

            # Only retain players who played in the prior 18 months for this team
            if days_since_last <= 550 and row["avg_minutes"] >= 5.0:
                p_name = self.resolve_player_name(pid)
                active_roster[pid] = {
                    "person_id": pid,
                    "player_name": p_name,
                    "team_id": team_id,
                    "team_code": team_code,
                    "team_name": team_name,
                    "is_transition_player": False,
                    "prior_team_id": None,
                    "prior_team_name": None,
                    "transaction_category": "Established Roster",
                    "transaction_date": None,
                    "days_since_team_change": days_since_last,
                    "games_with_current_team": int(row["games_with_team"]),
                    "historical_avg_minutes": float(row["avg_minutes"]),
                    "historical_avg_points": float(row["avg_points"]),
                    "historical_avg_rebounds": float(row["avg_rebounds"]),
                    "historical_avg_assists": float(row["avg_assists"])
                }

        # 2. Apply 2026 Offseason Transactions if target date is in the 2026-27 season
        if is_post_offseason_2026 and len(df_tx) > 0:
            # A. Process Departures (Remove players leaving the team)
            departures = self.get_team_departures(team_identifier)
            for dep in departures:
                pid = dep["person_id"]
                if pid in active_roster:
                    del active_roster[pid]

            # B. Process Additions (Add players arriving at the team)
            additions = self.get_team_additions(team_identifier)
            for add in additions:
                pid = add["person_id"]
                p_name = add["Player"]
                tx_desc = add.get("Transaction", "")
                
                # Deduce prior team from transaction text (e.g. "Trade with Raptors", "Free agency to Lakers")
                prior_team_name = None
                prior_team_id = None
                for candidate_t in df_tx["Team"].unique():
                    if candidate_t != team_name and candidate_t.split()[-1].lower() in tx_desc.lower():
                        try:
                            c_info = normalize_team(candidate_t)
                            prior_team_name = c_info["name"]
                            prior_team_id = c_info["id"]
                            break
                        except Exception:
                            pass

                # Calculate days since trade (from 2026-07-01 to game date)
                tx_dt = datetime(2026, 7, 1)
                days_since_tx = max(0, (dt_target - tx_dt).days)

                active_roster[pid] = {
                    "person_id": pid,
                    "player_name": p_name,
                    "team_id": team_id,
                    "team_code": team_code,
                    "team_name": team_name,
                    "is_transition_player": True,
                    "prior_team_id": prior_team_id,
                    "prior_team_name": prior_team_name,
                    "transaction_category": "Additions",
                    "transaction_date": "2026-07-01",
                    "days_since_team_change": days_since_tx,
                    "games_with_current_team": 0, # Zero games with new franchise prior to season opener
                    "historical_avg_minutes": 25.0, # Baseline prior rotation weight
                    "historical_avg_points": 12.0,
                    "historical_avg_rebounds": 4.0,
                    "historical_avg_assists": 2.5
                }

            # C. Process Re-signings (Ensure key re-signed core players remain on active roster)
            re_signings = [t for t in self.get_team_transactions(team_identifier) if t.get("Category") == "Re-signing"]
            for rs in re_signings:
                pid = rs["person_id"]
                p_name = rs["Player"]
                if pid not in active_roster:
                    active_roster[pid] = {
                        "person_id": pid,
                        "player_name": p_name,
                        "team_id": team_id,
                        "team_code": team_code,
                        "team_name": team_name,
                        "is_transition_player": False,
                        "prior_team_id": None,
                        "prior_team_name": None,
                        "transaction_category": "Re-signing",
                        "transaction_date": "2026-07-01",
                        "days_since_team_change": 0,
                        "games_with_current_team": 30,
                        "historical_avg_minutes": 22.0,
                        "historical_avg_points": 10.0,
                        "historical_avg_rebounds": 4.0,
                        "historical_avg_assists": 2.0
                    }

        # Convert to sorted list by expected rotation minutes
        roster_list = list(active_roster.values())
        roster_list.sort(key=lambda x: x.get("historical_avg_minutes", 0.0), reverse=True)

        return roster_list[:max_players]
