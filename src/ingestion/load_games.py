"""
Ingestion module for games table.
Loads official NBA matchup outcomes and venue information from Games.csv.
"""

import os
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.utils.logging import logger

def parse_datetime(val: Optional[str]) -> Optional[str]:
    if not val or not str(val).strip():
        return None
    val = str(val).strip()
    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"]:
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
    return None

def parse_date(val: Optional[str]) -> Optional[str]:
    if not val or not str(val).strip():
        return None
    val = str(val).strip()
    for fmt in ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%m/%d/%Y"]:
        try:
            return datetime.strptime(val, fmt).strftime("%Y-%m-%d")
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

def load_games(engine: Engine, raw_data_dir: str, batch_size: int = 5000) -> int:
    """
    Loads Games.csv and populates the games table in chunked batches.
    """
    games_csv = os.path.join(raw_data_dir, "games", "Games.csv")
    if not os.path.exists(games_csv):
        logger.error(f"Games.csv not found at {games_csv}")
        return 0

    logger.info(f"Ingesting historical games from {games_csv}...")
    records: List[Dict[str, Any]] = []
    seen_ids = set()
    total_processed = 0

    from src.utils.db import bulk_insert_records
    columns = [
        "game_id", "game_datetime_est", "game_date",
        "home_team_id", "home_team_city", "home_team_name",
        "away_team_id", "away_team_city", "away_team_name",
        "home_score", "away_score", "winner",
        "game_type", "game_subtype", "game_label", "game_sub_label",
        "series_game_number", "attendance", "arena_id", "arena_name",
        "arena_city", "arena_state", "officials"
    ]
    on_conflict = """ON CONFLICT (game_id) DO UPDATE SET
        game_datetime_est = EXCLUDED.game_datetime_est,
        game_date = EXCLUDED.game_date,
        home_team_id = EXCLUDED.home_team_id,
        home_team_city = EXCLUDED.home_team_city,
        home_team_name = EXCLUDED.home_team_name,
        away_team_id = EXCLUDED.away_team_id,
        away_team_city = EXCLUDED.away_team_city,
        away_team_name = EXCLUDED.away_team_name,
        home_score = EXCLUDED.home_score,
        away_score = EXCLUDED.away_score,
        winner = EXCLUDED.winner,
        game_type = EXCLUDED.game_type,
        game_subtype = EXCLUDED.game_subtype,
        game_label = EXCLUDED.game_label,
        game_sub_label = EXCLUDED.game_sub_label,
        series_game_number = EXCLUDED.series_game_number,
        attendance = EXCLUDED.attendance,
        arena_id = EXCLUDED.arena_id,
        arena_name = EXCLUDED.arena_name,
        arena_city = EXCLUDED.arena_city,
        arena_state = EXCLUDED.arena_state,
        officials = EXCLUDED.officials"""

    with open(games_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g_id = row.get("gameId", "").strip()
            if not g_id or g_id in seen_ids:
                continue
            seen_ids.add(g_id)

            dt_est = parse_datetime(row.get("gameDateTimeEst"))
            d_date = parse_date(row.get("gameDate")) or (dt_est[:10] if dt_est else None)

            record = {
                "game_id": g_id,
                "game_datetime_est": dt_est,
                "game_date": d_date,
                "home_team_id": parse_int(row.get("hometeamId")),
                "home_team_city": row.get("hometeamCity", "").strip() or None,
                "home_team_name": row.get("hometeamName", "").strip() or None,
                "away_team_id": parse_int(row.get("awayteamId")),
                "away_team_city": row.get("awayteamCity", "").strip() or None,
                "away_team_name": row.get("awayteamName", "").strip() or None,
                "home_score": parse_int(row.get("homeScore")),
                "away_score": parse_int(row.get("awayScore")),
                "winner": row.get("winner", "").strip() or None,
                "game_type": row.get("gameType", "").strip() or None,
                "game_subtype": row.get("gameSubtype", "").strip() or None,
                "game_label": row.get("gameLabel", "").strip() or None,
                "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                "series_game_number": parse_int(row.get("seriesGameNumber")),
                "attendance": parse_int(row.get("attendance")),
                "arena_id": row.get("arenaId", "").strip() or None,
                "arena_name": row.get("arenaName", "").strip() or None,
                "arena_city": row.get("arenaCity", "").strip() or None,
                "arena_state": row.get("arenaState", "").strip() or None,
                "officials": row.get("officials", "").strip() or None,
            }
            records.append(record)

            if len(records) >= batch_size:
                bulk_insert_records(engine, "games", columns, records, on_conflict=on_conflict, batch_size=batch_size)
                total_processed += len(records)
                records.clear()
                logger.info(f"Loaded {total_processed:,} games...")

    # Also check PlayerStatistics.csv for any exhibition / All-Star games not present in Games.csv
    player_stats_csv = os.path.join(raw_data_dir, "players", "PlayerStatistics.csv")
    if os.path.exists(player_stats_csv):
        with open(player_stats_csv, "r", encoding="utf-8-sig", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                g_id = row.get("gameId", "").strip()
                if not g_id or g_id in seen_ids:
                    continue
                seen_ids.add(g_id)

                dt_est = parse_datetime(row.get("gameDateTimeEst"))
                d_date = parse_date(row.get("gameDate")) or (dt_est[:10] if dt_est else None)

                record = {
                    "game_id": g_id,
                    "game_datetime_est": dt_est,
                    "game_date": d_date,
                    "home_team_id": None,
                    "home_team_city": None,
                    "home_team_name": None,
                    "away_team_id": None,
                    "away_team_city": None,
                    "away_team_name": None,
                    "home_score": None,
                    "away_score": None,
                    "winner": None,
                    "game_type": row.get("gameType", "").strip() or "Exhibition",
                    "game_subtype": None,
                    "game_label": row.get("gameLabel", "").strip() or None,
                    "game_sub_label": row.get("gameSubLabel", "").strip() or None,
                    "series_game_number": parse_int(row.get("seriesGameNumber")),
                    "attendance": None,
                    "arena_id": None,
                    "arena_name": None,
                    "arena_city": None,
                    "arena_state": None,
                    "officials": None,
                }
                records.append(record)

    if records:
        bulk_insert_records(engine, "games", columns, records, on_conflict=on_conflict, batch_size=batch_size)
        total_processed += len(records)

    logger.info(f"Successfully loaded {total_processed:,} games into database.")
    return total_processed
