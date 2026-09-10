"""
Master orchestration script for the Lakers in 5 data ingestion pipeline.
Executes loaders in topological order with structured timing, logging, and summary reporting.
"""

import os
import time
from typing import Dict, Any, Optional
from sqlalchemy.engine import Engine
from src.utils.db import get_engine, test_connection
from src.utils.logging import logger
from src.ingestion.load_teams import load_teams
from src.ingestion.load_players import load_players
from src.ingestion.load_team_histories import load_team_histories
from src.ingestion.load_transactions import load_transactions
from src.ingestion.load_games import load_games
from src.ingestion.load_team_stats import load_team_stats, load_team_stats_extended
from src.ingestion.load_player_stats import load_player_stats, load_player_stats_extended

def run_full_ingestion(engine: Optional[Engine] = None, raw_data_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes the end-to-end ingestion pipeline.
    """
    start_time = time.time()
    eng = engine or get_engine()
    
    if raw_data_dir is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        raw_data_dir = os.path.join(base_dir, "data", "raw")

    logger.info("=" * 70)
    logger.info("Starting Lakers in 5 Data Ingestion Pipeline")
    logger.info(f"Target Database: {eng.url.drivername} ({eng.url.host if eng.url.host else 'local'})")
    logger.info(f"Raw Data Directory: {raw_data_dir}")
    logger.info("=" * 70)

    summary: Dict[str, Dict[str, Any]] = {}

    # Stage 1: Dimension Tables
    stages = [
        ("teams", lambda: load_teams(eng, raw_data_dir)),
        ("players", lambda: load_players(eng, raw_data_dir)),
        ("team_histories", lambda: load_team_histories(eng, raw_data_dir)),
        ("transactions", lambda: load_transactions(raw_data_dir=raw_data_dir, engine=eng)),
        ("games", lambda: load_games(eng, raw_data_dir)),
        ("team_game_stats", lambda: load_team_stats(eng, raw_data_dir)),
        ("team_game_stats_extended", lambda: load_team_stats_extended(eng, raw_data_dir)),
        ("player_game_stats", lambda: load_player_stats(eng, raw_data_dir)),
        ("player_game_stats_extended", lambda: load_player_stats_extended(eng, raw_data_dir)),
    ]

    for table_name, loader_func in stages:
        t0 = time.time()
        try:
            logger.info(f"--> Ingesting table: {table_name}...")
            count = loader_func()
            elapsed = time.time() - t0
            summary[table_name] = {"rows": count, "time_seconds": round(elapsed, 2), "status": "SUCCESS"}
            logger.info(f"[DONE] {table_name}: {count:,} rows in {elapsed:.2f}s")
        except Exception as e:
            elapsed = time.time() - t0
            logger.error(f"[FAILED] Error ingesting {table_name}: {e}", exc_info=True)
            summary[table_name] = {"rows": 0, "time_seconds": round(elapsed, 2), "status": "FAILED", "error": str(e)}

    total_time = time.time() - start_time
    logger.info("=" * 70)
    logger.info("INGESTION PIPELINE SUMMARY")
    logger.info("=" * 70)
    for tbl, info in summary.items():
        logger.info(f"{tbl:<30}: {info['rows']:>10,} rows | {info['time_seconds']:>6.2f}s | {info['status']}")
    logger.info(f"Total Execution Time: {total_time:.2f} seconds")
    logger.info("=" * 70)

    return {"summary": summary, "total_seconds": round(total_time, 2)}

if __name__ == "__main__":
    run_full_ingestion()
