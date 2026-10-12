"""
Roster, Transaction, and Player Eligibility Service for Phase 8.
Tracks 2026 offseason transactions, roster movements, and determines canonical pregame
player eligibility universes as-of target game dates without temporal lookahead.
"""

import os
import re
import unicodedata
from typing import Dict, Any, Optional, List, Set, Tuple
from datetime import datetime, date, timedelta
import pandas as pd
try:
    import duckdb
except Exception:
    duckdb = None

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
        duckdb_conn: Optional[Any] = None
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

        # 1. Load from Players.csv
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

        # 2. Augment from player_game_stats.parquet with lightweight streaming query
        if os.path.exists(self.parquet_path):
            try:
                if duckdb is not None:
                    p_path = os.path.abspath(self.parquet_path).replace("\\", "/")
                    q_conn = self.conn or duckdb.connect(":memory:")
                    rows = q_conn.execute(f"SELECT DISTINCT personId, firstName, lastName FROM read_parquet('{p_path}') WHERE personId IS NOT NULL").fetchall()
                    for pid_raw, fn, ln in rows:
                        pid = str(pid_raw)
                        raw_name = f"{fn or ''} {ln or ''}".strip()
                        norm_name = normalize_player_name(raw_name)
                        id_map[norm_name] = pid
                        id_map[raw_name.lower()] = pid
                        name_map[pid] = raw_name
            except Exception as e:
                logger.warning(f"Failed to load player stats mapping from parquet: {e}")

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

    def get_global_roster_universe(
        self,
        as_of_date: Any
    ) -> Dict[str, Dict[str, Any]]:
        """
        Constructs the global player universe mapping personId -> canonical team assignment
        as of a target date D. Strictly leakage-safe: utilizes historical games strictly before
        as_of_date and chronological 2026 offseason transactions.
        """
        self._init_player_maps()
        df_tx = self.load_transactions()

        dt_target = datetime.strptime(str(as_of_date)[:10], "%Y-%m-%d")
        cutoff_date = str(as_of_date)[:10]
        cutoff_550 = (dt_target - timedelta(days=550)).strftime("%Y-%m-%d")
        is_post_offseason_2026 = dt_target >= datetime(2026, 7, 1)

        try:
            if self.conn is None and duckdb is not None:
                self.conn = duckdb.connect(":memory:")
                self.conn.execute("SET memory_limit = '128MB'")
                self.conn.execute("SET threads = 1")

            if self.conn is not None and os.path.exists(self.parquet_path):
                p_path = os.path.abspath(self.parquet_path).replace("\\", "/")
                
                # Query each player's LATEST team prior to cutoff_date and aggregate recent stats across all teams
                sql = f"""
                    WITH latest_game AS (
                        SELECT 
                            personId as person_id,
                            playerteamId as latest_team_id,
                            playerteamName as latest_team_name,
                            substr(gameDateTimeEst, 1, 10) as last_game_date,
                            ROW_NUMBER() OVER (PARTITION BY personId ORDER BY gameDateTimeEst DESC) as rn
                        FROM read_parquet('{p_path}')
                        WHERE substr(gameDateTimeEst, 1, 10) < '{cutoff_date}'
                          AND substr(gameDateTimeEst, 1, 10) >= '{cutoff_550}'
                          AND playerteamId IS NOT NULL
                          AND numMinutes IS NOT NULL 
                          AND TRY_CAST(numMinutes AS DOUBLE) > 0.0
                    ),
                    recent_stats AS (
                        SELECT 
                            personId as person_id,
                            firstName,
                            lastName,
                            COUNT(*) as total_recent_games,
                            AVG(TRY_CAST(numMinutes AS DOUBLE)) as avg_minutes,
                            AVG(TRY_CAST(points AS DOUBLE)) as avg_points,
                            AVG(TRY_CAST(reboundsTotal AS DOUBLE)) as avg_rebounds,
                            AVG(TRY_CAST(assists AS DOUBLE)) as avg_assists
                        FROM read_parquet('{p_path}')
                        WHERE substr(gameDateTimeEst, 1, 10) < '{cutoff_date}'
                          AND substr(gameDateTimeEst, 1, 10) >= '{cutoff_550}'
                          AND numMinutes IS NOT NULL 
                          AND TRY_CAST(numMinutes AS DOUBLE) > 0.0
                        GROUP BY personId, firstName, lastName
                    )
                    SELECT 
                        l.person_id,
                        COALESCE(r.firstName || ' ' || r.lastName, l.person_id) as player_name,
                        l.latest_team_id,
                        l.latest_team_name,
                        l.last_game_date,
                        COALESCE(r.total_recent_games, 1) as total_recent_games,
                        COALESCE(r.avg_minutes, 15.0) as avg_minutes,
                        COALESCE(r.avg_points, 5.0) as avg_points,
                        COALESCE(r.avg_rebounds, 2.0) as avg_rebounds,
                        COALESCE(r.avg_assists, 1.0) as avg_assists
                    FROM latest_game l
                    LEFT JOIN recent_stats r ON l.person_id = r.person_id
                    WHERE l.rn = 1
                """
                hist_players_df = self.conn.execute(sql).df()
            else:
                hist_players_df = pd.DataFrame()
        except Exception as e:
            logger.warning(f"Error querying historical roster: {e}")
            hist_players_df = pd.DataFrame()

        # Build global player assignments table
        # Key: person_id -> Player Assignment Dict
        global_assignments: Dict[str, Dict[str, Any]] = {}
        for _, row in hist_players_df.iterrows():
            pid = str(row["person_id"])
            p_name = self.resolve_player_name(pid)
            if p_name.startswith("Player #") and row["player_name"]:
                p_name = str(row["player_name"])

            global_assignments[pid] = {
                "person_id": pid,
                "player_name": p_name,
                "team_id": str(row["latest_team_id"]),
                "last_game_date": str(row["last_game_date"]),
                "historical_avg_minutes": float(row["avg_minutes"]),
                "historical_avg_points": float(row["avg_points"]),
                "historical_avg_rebounds": float(row["avg_rebounds"]),
                "historical_avg_assists": float(row["avg_assists"]),
                "is_transition_player": False,
                "prior_team_id": None,
                "prior_team_name": None,
                "transaction_category": "Established Roster",
                "transaction_date": None,
                "days_since_team_change": 0,
                "games_with_current_team": int(row["total_recent_games"])
            }

        # Apply 2026 Offseason Transactions: Step 1: Departures, Step 2: Additions / Re-signing
        if is_post_offseason_2026 and len(df_tx) > 0:
            # Step 1: Process all departures first to vacate prior team roster spots
            departures_df = df_tx[df_tx["Category"] == "Departures"]
            for _, row in departures_df.iterrows():
                t_name = str(row["Team"])
                p_name = str(row["Player"])
                pid = str(row.get("person_id") or self.resolve_player_id(p_name))
                try:
                    t_info = normalize_team(t_name)
                    departing_team_id = t_info["id"]
                except Exception:
                    continue
                if pid in global_assignments and global_assignments[pid]["team_id"] == departing_team_id:
                    global_assignments[pid]["team_id"] = None

            # Step 2: Process additions and re-signings to assign new team spots
            additions_df = df_tx[df_tx["Category"].isin(["Additions", "Re-signing"])]
            for _, row in additions_df.iterrows():
                t_name = str(row["Team"])
                cat = str(row["Category"])
                p_name = str(row["Player"])
                pid = str(row.get("person_id") or self.resolve_player_id(p_name))
                
                try:
                    t_info = normalize_team(t_name)
                    new_team_id = t_info["id"]
                except Exception:
                    continue

                tx_dt = datetime(2026, 7, 1)
                days_since_tx = max(0, (dt_target - tx_dt).days)
                
                if pid in global_assignments:
                    prior_tid = global_assignments[pid]["team_id"]
                    global_assignments[pid]["team_id"] = new_team_id
                    global_assignments[pid]["is_transition_player"] = (cat == "Additions")
                    global_assignments[pid]["transaction_category"] = cat
                    global_assignments[pid]["transaction_date"] = "2026-07-01"
                    global_assignments[pid]["days_since_team_change"] = days_since_tx
                    global_assignments[pid]["player_name"] = p_name
                    global_assignments[pid]["prior_team_id"] = prior_tid
                else:
                    global_assignments[pid] = {
                        "person_id": pid,
                        "player_name": p_name,
                        "team_id": new_team_id,
                        "last_game_date": "2026-07-01",
                        "historical_avg_minutes": 20.0,
                        "historical_avg_points": 10.0,
                        "historical_avg_rebounds": 4.0,
                        "historical_avg_assists": 2.0,
                        "is_transition_player": (cat == "Additions"),
                        "prior_team_id": None,
                        "prior_team_name": None,
                        "transaction_category": cat,
                        "transaction_date": "2026-07-01",
                        "days_since_team_change": days_since_tx,
                        "games_with_current_team": 0
                    }

        return global_assignments

    def get_player_team_as_of(self, person_id: str, as_of_date: Any) -> Optional[str]:
        """Looks up a player's canonical team_id as of a target date."""
        universe = self.get_global_roster_universe(as_of_date)
        info = universe.get(str(person_id))
        return info.get("team_id") if info else None

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
        Ensures players are assigned strictly to their MOST RECENT team without historical contamination.
        """
        team_info = normalize_team(team_identifier)
        target_team_id = team_info["id"]
        target_team_code = team_info["code"]
        target_team_name = team_info["name"]

        global_assignments = self.get_global_roster_universe(as_of_date)

        # Filter players strictly belonging to target_team_id
        team_roster: List[Dict[str, Any]] = []
        for p in global_assignments.values():
            if p.get("team_id") == target_team_id:
                p["team_code"] = target_team_code
                p["team_name"] = target_team_name
                team_roster.append(p)

        # Sort by expected rotation weight (recent average minutes)
        team_roster.sort(key=lambda x: x.get("historical_avg_minutes", 0.0), reverse=True)
        return team_roster[:max_players]
