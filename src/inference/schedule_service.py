"""
Schedule Ingestion and Lookup Service for 2026-27 NBA Season.
Parses the official PDF schedule, normalizes team identifiers, and caches structured game records.
"""

import os
import re
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import pandas as pd
import pypdf
from src.inference.schemas import ScheduledGame
from src.utils.logging import logger

# Comprehensive NBA Team Normalization Table (30 Modern NBA Franchises)
NBA_TEAMS = [
    {"id": "1610612737", "code": "ATL", "city": "Atlanta", "name": "Hawks", "aliases": ["atlanta", "hawks", "atl"]},
    {"id": "1610612738", "code": "BOS", "city": "Boston", "name": "Celtics", "aliases": ["boston", "celtics", "bos"]},
    {"id": "1610612751", "code": "BKN", "city": "Brooklyn", "name": "Nets", "aliases": ["brooklyn", "nets", "bkn"]},
    {"id": "1610612766", "code": "CHA", "city": "Charlotte", "name": "Hornets", "aliases": ["charlotte", "hornets", "cha"]},
    {"id": "1610612741", "code": "CHI", "city": "Chicago", "name": "Bulls", "aliases": ["chicago", "bulls", "chi"]},
    {"id": "1610612739", "code": "CLE", "city": "Cleveland", "name": "Cavaliers", "aliases": ["cleveland", "cavaliers", "cavs", "cle"]},
    {"id": "1610612742", "code": "DAL", "city": "Dallas", "name": "Mavericks", "aliases": ["dallas", "mavericks", "mavs", "dal"]},
    {"id": "1610612743", "code": "DEN", "city": "Denver", "name": "Nuggets", "aliases": ["denver", "nuggets", "den"]},
    {"id": "1610612765", "code": "DET", "city": "Detroit", "name": "Pistons", "aliases": ["detroit", "pistons", "det"]},
    {"id": "1610612744", "code": "GSW", "city": "Golden State", "name": "Warriors", "aliases": ["golden state", "warriors", "gsw", "gs"]},
    {"id": "1610612745", "code": "HOU", "city": "Houston", "name": "Rockets", "aliases": ["houston", "rockets", "hou"]},
    {"id": "1610612754", "code": "IND", "city": "Indiana", "name": "Pacers", "aliases": ["indiana", "pacers", "ind"]},
    {"id": "1610612746", "code": "LAC", "city": "LA Clippers", "name": "Clippers", "aliases": ["la clippers", "los angeles clippers", "clippers", "lac"]},
    {"id": "1610612747", "code": "LAL", "city": "Los Angeles", "name": "Lakers", "aliases": ["la lakers", "los angeles lakers", "lakers", "lal", "la"]},
    {"id": "1610612763", "code": "MEM", "city": "Memphis", "name": "Grizzlies", "aliases": ["memphis", "grizzlies", "mem"]},
    {"id": "1610612748", "code": "MIA", "city": "Miami", "name": "Heat", "aliases": ["miami", "heat", "mia"]},
    {"id": "1610612749", "code": "MIL", "city": "Milwaukee", "name": "Bucks", "aliases": ["milwaukee", "bucks", "mil"]},
    {"id": "1610612750", "code": "MIN", "city": "Minnesota", "name": "Timberwolves", "aliases": ["minnesota", "timberwolves", "wolves", "min"]},
    {"id": "1610612740", "code": "NOP", "city": "New Orleans", "name": "Pelicans", "aliases": ["new orleans", "pelicans", "nop", "no"]},
    {"id": "1610612752", "code": "NYK", "city": "New York", "name": "Knicks", "aliases": ["new york", "knicks", "nyk", "ny"]},
    {"id": "1610612760", "code": "OKC", "city": "Oklahoma City", "name": "Thunder", "aliases": ["oklahoma city", "thunder", "okc"]},
    {"id": "1610612753", "code": "ORL", "city": "Orlando", "name": "Magic", "aliases": ["orlando", "magic", "orl"]},
    {"id": "1610612755", "code": "PHI", "city": "Philadelphia", "name": "76ers", "aliases": ["philadelphia", "76ers", "sixers", "phi"]},
    {"id": "1610612756", "code": "PHX", "city": "Phoenix", "name": "Suns", "aliases": ["phoenix", "suns", "phx"]},
    {"id": "1610612757", "code": "POR", "city": "Portland", "name": "Trail Blazers", "aliases": ["portland", "trail blazers", "blazers", "por"]},
    {"id": "1610612758", "code": "SAC", "city": "Sacramento", "name": "Kings", "aliases": ["sacramento", "kings", "sac"]},
    {"id": "1610612759", "code": "SAS", "city": "San Antonio", "name": "Spurs", "aliases": ["san antonio", "spurs", "sas", "sa"]},
    {"id": "1610612761", "code": "TOR", "city": "Toronto", "name": "Raptors", "aliases": ["toronto", "raptors", "tor"]},
    {"id": "1610612762", "code": "UTA", "city": "Utah", "name": "Jazz", "aliases": ["utah", "jazz", "uta"]},
    {"id": "1610612764", "code": "WAS", "city": "Washington", "name": "Wizards", "aliases": ["washington", "wizards", "was"]},
]

LAKERS_TEAM_ID = "1610612747"

def normalize_team(team_str: str) -> Dict[str, str]:
    """
    Normalizes any team name, city, nickname, or 3-letter code to its official NBA franchise info.
    """
    clean = str(team_str).strip().lower()
    
    # 1. Direct ID match
    for t in NBA_TEAMS:
        if t["id"] == str(team_str).strip():
            return {"id": t["id"], "name": f"{t['city']} {t['name']}", "code": t["code"], "city": t["city"], "nickname": t["name"]}
            
    # 2. Code match
    for t in NBA_TEAMS:
        if t["code"].lower() == clean:
            return {"id": t["id"], "name": f"{t['city']} {t['name']}", "code": t["code"], "city": t["city"], "nickname": t["name"]}
            
    # 3. Alias / substring match
    for t in NBA_TEAMS:
        if clean in t["aliases"] or clean == f"{t['city']} {t['name']}".lower():
            return {"id": t["id"], "name": f"{t['city']} {t['name']}", "code": t["code"], "city": t["city"], "nickname": t["name"]}
            
    # 4. Partial fallback
    for t in NBA_TEAMS:
        if t["name"].lower() in clean or t["city"].lower() in clean:
            return {"id": t["id"], "name": f"{t['city']} {t['name']}", "code": t["code"], "city": t["city"], "nickname": t["name"]}
            
    raise ValueError(f"Unknown NBA team identifier: '{team_str}'")


class ScheduleService:
    """
    Parses and serves the official 2026-27 NBA Regular Season Schedule.
    """
    def __init__(self, pdf_path: Optional[str] = None, cache_path: Optional[str] = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.pdf_path = pdf_path or os.path.join(base_dir, "data", "raw", "schedules", "2026-27-NBA-Regular-Season-Schedule-By-Date.pdf")
        self.cache_path = cache_path or os.path.join(base_dir, "data", "processed", "parquet", "schedule_2026_27.parquet")
        self._schedule_df: Optional[pd.DataFrame] = None

    def load_schedule(self, force_reparse: bool = False) -> pd.DataFrame:
        """
        Loads the 2026-27 schedule from cache or parses from raw PDF.
        """
        if self._schedule_df is not None and not force_reparse:
            return self._schedule_df
            
        if os.path.exists(self.cache_path) and not force_reparse:
            logger.info(f"Loading 2026-27 schedule from cache: {self.cache_path}")
            self._schedule_df = pd.read_parquet(self.cache_path)
            return self._schedule_df
            
        logger.info(f"Parsing 2026-27 schedule from PDF: {self.pdf_path}")
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"Schedule PDF not found at {self.pdf_path}")
            
        reader = pypdf.PdfReader(self.pdf_path)
        lines = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                for line in text.split("\n"):
                    lines.append(line.strip())
                    
        # Regex to parse game rows e.g. "5 Wed. 10/21/26 Golden State at LA Lakers 7:00 PM 10:00 PM ESPN"
        pattern = re.compile(r"^(\d+)\s+([A-Za-z]+\.?)\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.+?)\s+at\s+(.+?)\s+(\d{1,2}:\d{2}\s+[AP]M)")
        parsed_games = []
        
        for line in lines:
            m = pattern.search(line)
            if m:
                g_num, day_str, date_str, away_raw, home_raw, time_str = m.groups()
                try:
                    home_info = normalize_team(home_raw)
                    away_info = normalize_team(away_raw)
                    
                    # Convert M/D/YY to YYYY-MM-DD
                    dt = datetime.strptime(date_str, "%m/%d/%y")
                    iso_date = dt.strftime("%Y-%m-%d")
                    
                    parsed_games.append({
                        "game_num": int(g_num),
                        "game_date": iso_date,
                        "home_team": home_info["name"],
                        "away_team": away_info["name"],
                        "home_team_id": home_info["id"],
                        "away_team_id": away_info["id"],
                        "home_team_code": home_info["code"],
                        "away_team_code": away_info["code"],
                        "game_time": time_str.strip(),
                        "is_lakers_game": (home_info["id"] == LAKERS_TEAM_ID or away_info["id"] == LAKERS_TEAM_ID)
                    })
                except Exception as e:
                    logger.warning(f"Could not parse game row '{line}': {e}")
                    
        df = pd.DataFrame(parsed_games)
        df = df.sort_values(by=["game_date", "game_num"]).reset_index(drop=True)
        
        os.makedirs(os.path.dirname(self.cache_path), exist_ok=True)
        df.to_parquet(self.cache_path, index=False)
        logger.info(f"Successfully parsed and cached {len(df)} scheduled games to {self.cache_path}.")
        self._schedule_df = df
        return df

    def get_game_by_num(self, game_num: int) -> Optional[Dict[str, Any]]:
        """Finds a game by official schedule game number."""
        df = self.load_schedule()
        match = df[df["game_num"] == int(game_num)]
        if len(match) == 0:
            return None
        return match.iloc[0].to_dict()

    def get_next_lakers_game(self, as_of_date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves the next unplayed Lakers game occurring on or after as_of_date.
        If as_of_date is not provided, defaults to the start of the 2026-27 season (2026-10-20).
        """
        df = self.load_schedule()
        as_of = as_of_date or "2026-10-20"
        
        lakers_games = df[df["is_lakers_game"] & (df["game_date"] >= as_of)].sort_values(by=["game_date", "game_num"])
        if len(lakers_games) == 0:
            return None
        return lakers_games.iloc[0].to_dict()

    def get_games_for_team(self, team_str: str, as_of_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieves all scheduled games for a given team on or after as_of_date."""
        team_info = normalize_team(team_str)
        t_id = team_info["id"]
        df = self.load_schedule()
        
        mask = (df["home_team_id"] == t_id) | (df["away_team_id"] == t_id)
        if as_of_date:
            mask = mask & (df["game_date"] >= as_of_date)
            
        team_games = df[mask].sort_values(by=["game_date", "game_num"])
        return team_games.to_dict(orient="records")
