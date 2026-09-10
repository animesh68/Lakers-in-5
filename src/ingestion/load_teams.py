"""
Ingestion module for teams dimension table.
Extracts distinct teams from TeamHistories, Games, and TeamStatistics to build a comprehensive teams registry.
"""

import os
import csv
from typing import Dict, Any, List
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.utils.logging import logger

def extract_teams(raw_data_dir: str) -> List[Dict[str, Any]]:
    """
    Extracts and unifies unique team records from TeamHistories.csv, Games.csv, and TeamStatistics.csv.
    """
    teams_dict: Dict[int, Dict[str, Any]] = {}

    # 1. From TeamHistories.csv (best source for official IDs, abbrevs, founded years)
    histories_path = os.path.join(raw_data_dir, "other", "TeamHistories.csv")
    if os.path.exists(histories_path):
        with open(histories_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    t_id = int(row["teamId"])
                    founded = int(row["seasonFounded"]) if row.get("seasonFounded", "").strip().isdigit() else None
                    active = int(row["seasonActiveTill"]) if row.get("seasonActiveTill", "").strip().isdigit() else None
                    teams_dict[t_id] = {
                        "team_id": t_id,
                        "team_abbreviation": row.get("teamAbbrev", "").strip(),
                        "team_city": row.get("teamCity", "").strip(),
                        "team_name": row.get("teamName", "").strip(),
                        "season_founded": founded,
                        "season_active_till": active,
                        "league": row.get("league", "NBA").strip()
                    }
                except (ValueError, KeyError) as e:
                    logger.debug(f"Skipping malformed row in TeamHistories: {e}")

    # 2. From Games.csv to capture any teams in game logs
    games_path = os.path.join(raw_data_dir, "games", "Games.csv")
    if os.path.exists(games_path):
        with open(games_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for prefix in ["home", "away"]:
                    try:
                        t_id_str = row.get(f"{prefix}teamId", "").strip()
                        if t_id_str and t_id_str.isdigit():
                            t_id = int(t_id_str)
                            if t_id not in teams_dict:
                                teams_dict[t_id] = {
                                    "team_id": t_id,
                                    "team_abbreviation": None,
                                    "team_city": row.get(f"{prefix}teamCity", "").strip(),
                                    "team_name": row.get(f"{prefix}teamName", "").strip(),
                                    "season_founded": None,
                                    "season_active_till": None,
                                    "league": "NBA"
                                }
                    except Exception:
                        pass

    # 3. From TeamStatistics.csv
    stats_path = os.path.join(raw_data_dir, "games", "TeamStatistics.csv")
    if os.path.exists(stats_path):
        with open(stats_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    t_id_str = row.get("teamId", "").strip()
                    if t_id_str and t_id_str.isdigit():
                        t_id = int(t_id_str)
                        if t_id not in teams_dict:
                            teams_dict[t_id] = {
                                "team_id": t_id,
                                "team_abbreviation": None,
                                "team_city": row.get("teamCity", "").strip(),
                                "team_name": row.get("teamName", "").strip(),
                                "season_founded": None,
                                "season_active_till": None,
                                "league": "NBA"
                            }
                except Exception:
                    pass

    # 4. From PlayerStatistics.csv (for All-Star / exhibition teams)
    player_stats_path = os.path.join(raw_data_dir, "players", "PlayerStatistics.csv")
    if os.path.exists(player_stats_path):
        with open(player_stats_path, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                for prefix in ["player", "opponent"]:
                    try:
                        t_id_str = row.get(f"{prefix}teamId", "").strip()
                        if t_id_str and t_id_str.isdigit():
                            t_id = int(t_id_str)
                            if t_id not in teams_dict:
                                teams_dict[t_id] = {
                                    "team_id": t_id,
                                    "team_abbreviation": None,
                                    "team_city": row.get(f"{prefix}teamCity", "").strip(),
                                    "team_name": row.get(f"{prefix}teamName", "").strip(),
                                    "season_founded": None,
                                    "season_active_till": None,
                                    "league": "NBA"
                                }
                    except Exception:
                        pass

    return list(teams_dict.values())

def load_teams(engine: Engine, raw_data_dir: str) -> int:
    """
    Ingests unique teams into the teams table.
    """
    logger.info("Starting ingestion of teams dimension...")
    teams = extract_teams(raw_data_dir)
    logger.info(f"Extracted {len(teams)} unique canonical teams.")

    from src.utils.db import bulk_insert_records
    columns = ["team_id", "team_abbreviation", "team_city", "team_name", "season_founded", "season_active_till", "league"]
    on_conflict = """ON CONFLICT (team_id) DO UPDATE SET
        team_abbreviation = COALESCE(EXCLUDED.team_abbreviation, teams.team_abbreviation),
        team_city = COALESCE(EXCLUDED.team_city, teams.team_city),
        team_name = COALESCE(EXCLUDED.team_name, teams.team_name),
        season_founded = COALESCE(EXCLUDED.season_founded, teams.season_founded),
        season_active_till = COALESCE(EXCLUDED.season_active_till, teams.season_active_till),
        league = COALESCE(EXCLUDED.league, teams.league)"""

    bulk_insert_records(engine, "teams", columns, teams, on_conflict=on_conflict)
    logger.info(f"Successfully loaded {len(teams)} teams into database.")
    return len(teams)
