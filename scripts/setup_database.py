"""
CLI Script: Initialize and configure PostgreSQL database schema and indexes.
Usage:
    python scripts/setup_database.py [--db-url DB_URL]
"""

import os
import sys
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db import get_engine, execute_sql_file, test_connection
from src.utils.logging import logger

def setup_database(db_url: str = None):
    engine = get_engine(db_url=db_url)
    logger.info(f"Setting up database at {engine.url.drivername}://{engine.url.host or 'local'}...")

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tables_sql = os.path.join(base_dir, "src", "ingestion", "sql", "01_create_tables.sql")
    indexes_sql = os.path.join(base_dir, "src", "ingestion", "sql", "02_create_indexes.sql")

    if not os.path.exists(tables_sql):
        logger.error(f"DDL script not found at {tables_sql}")
        sys.exit(1)

    try:
        execute_sql_file(engine, tables_sql)
        if os.path.exists(indexes_sql):
            execute_sql_file(engine, indexes_sql)
        logger.info("Database schema setup completed successfully!")
    except Exception as e:
        logger.error(f"Failed to set up database schema: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize database schema for Lakers in 5")
    parser.add_argument("--db-url", type=str, default=None, help="Optional database URL override")
    args = parser.parse_args()
    setup_database(db_url=args.db_url)
