"""
CLI Script: Run end-to-end chunked data ingestion pipeline.
Usage:
    python scripts/ingest_data.py [--db-url DB_URL] [--raw-dir RAW_DIR]
"""

import os
import sys
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db import get_engine
from src.ingestion.run_ingestion import run_full_ingestion

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Lakers in 5 data ingestion pipeline")
    parser.add_argument("--db-url", type=str, default=None, help="Optional database URL override")
    parser.add_argument("--raw-dir", type=str, default=None, help="Optional raw data directory override")
    args = parser.parse_args()

    engine = get_engine(db_url=args.db_url)
    run_full_ingestion(engine=engine, raw_data_dir=args.raw_dir)
