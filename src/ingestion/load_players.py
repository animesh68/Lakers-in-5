"""
Ingestion module for players dimension table.
Loads player biographical and physical data from Players.csv into the players table.
"""

import os
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.utils.logging import logger

def parse_date(date_str: Optional[str]) -> Optional[str]:
    if not date_str or not date_str.strip():
        return None
    date_str = date_str.strip()
    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y", "%Y"]:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return None

def parse_int(val: Optional[str]) -> Optional[int]:
    if not val or not str(val).strip():
        return None
    try:
        return int(float(str(val).strip()))
    except (ValueError, TypeError):
        return None

def parse_bool(val: Optional[str]) -> bool:
    if not val:
        return False
    val_str = str(val).strip().lower()
    return val_str in ("1", "true", "t", "yes", "y")

def load_players(engine: Engine, raw_data_dir: str) -> int:
    """
    Loads Players.csv and populates the players table.
    """
    players_csv = os.path.join(raw_data_dir, "players", "Players.csv")
    if not os.path.exists(players_csv):
        logger.error(f"Players.csv not found at {players_csv}")
        return 0

    logger.info(f"Ingesting player biographical profiles from {players_csv}...")
    records: List[Dict[str, Any]] = []
    seen_ids = set()

    with open(players_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            p_id_str = row.get("personId", "").strip()
            if not p_id_str or not p_id_str.isdigit():
                continue
            p_id = int(p_id_str)
            if p_id in seen_ids:
                continue
            seen_ids.add(p_id)

            record = {
                "person_id": p_id,
                "first_name": row.get("firstName", "").strip() or None,
                "last_name": row.get("lastName", "").strip() or None,
                "birth_date": parse_date(row.get("birthDate")),
                "school": row.get("school", "").strip() or None,
                "country": row.get("country", "").strip() or None,
                "height_inches": parse_int(row.get("heightInches")),
                "body_weight_lbs": parse_int(row.get("bodyWeightLbs")),
                "jersey": row.get("jersey", "").strip() or None,
                "is_guard": parse_bool(row.get("guard")),
                "is_forward": parse_bool(row.get("forward")),
                "is_center": parse_bool(row.get("center")),
                "draft_year": parse_int(row.get("draftYear")),
                "draft_round": parse_int(row.get("draftRound")),
                "draft_number": parse_int(row.get("draftNumber")),
                "from_year": parse_int(row.get("fromYear")),
                "to_year": parse_int(row.get("toYear")),
            }
            records.append(record)

    logger.info(f"Parsed {len(records)} player profiles from Players.csv.")

    # Check for any historical players in PlayerStatistics.csv that might not be in Players.csv
    player_stats_csv = os.path.join(raw_data_dir, "players", "PlayerStatistics.csv")
    if os.path.exists(player_stats_csv):
        with open(player_stats_csv, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                p_id_str = row.get("personId", "").strip()
                if p_id_str and p_id_str.isdigit():
                    p_id = int(p_id_str)
                    if p_id not in seen_ids:
                        seen_ids.add(p_id)
                        records.append({
                            "person_id": p_id,
                            "first_name": row.get("firstName", "").strip() or None,
                            "last_name": row.get("lastName", "").strip() or None,
                            "birth_date": None,
                            "school": None,
                            "country": None,
                            "height_inches": None,
                            "body_weight_lbs": None,
                            "jersey": None,
                            "is_guard": False,
                            "is_forward": False,
                            "is_center": False,
                            "draft_year": None,
                            "draft_round": None,
                            "draft_number": None,
                            "from_year": None,
                            "to_year": None,
                        })

    logger.info(f"Total unique players to insert (including historical logs): {len(records)}")

    from src.utils.db import bulk_insert_records
    columns = [
        "person_id", "first_name", "last_name", "birth_date", "school", "country",
        "height_inches", "body_weight_lbs", "jersey", "is_guard", "is_forward", "is_center",
        "draft_year", "draft_round", "draft_number", "from_year", "to_year"
    ]
    on_conflict = """ON CONFLICT (person_id) DO UPDATE SET
        first_name = COALESCE(EXCLUDED.first_name, players.first_name),
        last_name = COALESCE(EXCLUDED.last_name, players.last_name),
        birth_date = COALESCE(EXCLUDED.birth_date, players.birth_date),
        school = COALESCE(EXCLUDED.school, players.school),
        country = COALESCE(EXCLUDED.country, players.country),
        height_inches = COALESCE(EXCLUDED.height_inches, players.height_inches),
        body_weight_lbs = COALESCE(EXCLUDED.body_weight_lbs, players.body_weight_lbs),
        jersey = COALESCE(EXCLUDED.jersey, players.jersey),
        is_guard = EXCLUDED.is_guard,
        is_forward = EXCLUDED.is_forward,
        is_center = EXCLUDED.is_center,
        draft_year = COALESCE(EXCLUDED.draft_year, players.draft_year),
        draft_round = COALESCE(EXCLUDED.draft_round, players.draft_round),
        draft_number = COALESCE(EXCLUDED.draft_number, players.draft_number),
        from_year = COALESCE(EXCLUDED.from_year, players.from_year),
        to_year = COALESCE(EXCLUDED.to_year, players.to_year)"""

    bulk_insert_records(engine, "players", columns, records, on_conflict=on_conflict, batch_size=5000)
    logger.info(f"Successfully loaded {len(records)} players into database.")
    return len(records)
