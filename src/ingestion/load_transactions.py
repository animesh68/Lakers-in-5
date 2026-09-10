"""
Ingestion module for 2026 offseason roster transactions.
Loads nba_2026_offseason_transactions.csv into transactions table.
"""

import os
import csv
from typing import Dict, Any, List
from sqlalchemy.engine import Engine
from sqlalchemy import text
from src.utils.logging import logger

def load_transactions(engine: Engine, raw_data_dir: str) -> int:
    """
    Loads 2026 offseason transactions into transactions table.
    """
    transactions_csv = os.path.join(raw_data_dir, "transactions", "nba_2026_offseason_transactions.csv")
    if not os.path.exists(transactions_csv):
        logger.error(f"Transactions CSV not found at {transactions_csv}")
        return 0

    logger.info(f"Ingesting offseason transactions from {transactions_csv}...")
    from src.utils.db import bulk_insert_records
    columns = ["team", "category", "player", "transaction_details", "status"]
    records: List[Dict[str, Any]] = []

    with open(transactions_csv, "r", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        for row in reader:
            team = row.get("Team", "").strip() or row.get("\ufeffTeam", "").strip()
            player = row.get("Player", "").strip()
            category = row.get("Category", "").strip()
            if not team or not player:
                continue

            record = {
                "team": team,
                "category": category,
                "player": player,
                "transaction_details": row.get("Transaction", "").strip() or None,
                "status": row.get("Status", "").strip() or None
            }
            records.append(record)

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM transactions;"))

    bulk_insert_records(engine, "transactions", columns, records)
    logger.info(f"Successfully loaded {len(records)} transaction records.")
    return len(records)
