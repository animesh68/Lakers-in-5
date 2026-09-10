"""
Ingestion module for historical team franchise lineage.
Loads TeamHistories.csv into team_histories table.
"""

import os
import csv
from typing import Dict, Any, List
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.utils.logging import logger

def load_team_histories(engine: Engine, raw_data_dir: str) -> int:
    """
    Loads TeamHistories.csv into team_histories table.
    """
    histories_csv = os.path.join(raw_data_dir, "other", "TeamHistories.csv")
    if not os.path.exists(histories_csv):
        logger.error(f"TeamHistories.csv not found at {histories_csv}")
        return 0

    logger.info(f"Ingesting team histories from {histories_csv}...")
    from src.utils.db import bulk_insert_records
    columns = ["team_id", "team_city", "team_name", "team_abbrev", "season_founded", "season_active_till", "league"]
    records: List[Dict[str, Any]] = []

    with open(histories_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                t_id = int(row["teamId"])
                founded = int(row["seasonFounded"]) if row.get("seasonFounded", "").strip().isdigit() else None
                record = {
                    "team_id": t_id,
                    "team_city": row.get("teamCity", "").strip(),
                    "team_name": row.get("teamName", "").strip(),
                    "team_abbrev": row.get("teamAbbrev", "").strip(),
                    "season_founded": founded,
                    "season_active_till": row.get("seasonActiveTill", "").strip() or None,
                    "league": row.get("league", "NBA").strip()
                }
                records.append(record)
            except Exception as e:
                logger.warning(f"Error parsing row in TeamHistories: {e}")

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM team_histories;"))

    bulk_insert_records(engine, "team_histories", columns, records)
    logger.info(f"Successfully loaded {len(records)} team history records.")
    return len(records)
