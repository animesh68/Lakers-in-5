"""
CLI Script: Run data validation and integrity verification.
Usage:
    python scripts/validate_data.py [--db-url DB_URL]
"""

import os
import sys
import argparse

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils.db import get_engine
from src.validation.validator import DataValidator
from src.utils.logging import logger

def validate(db_url: str = None):
    engine = get_engine(db_url=db_url)
    validator = DataValidator(engine=engine)
    results = validator.run_all_validations()
    if results["overall_status"] != "PASSED":
        logger.error("Validation checks failed!")
        sys.exit(1)
    else:
        logger.info("All validation checks passed!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Lakers in 5 data validation suite")
    parser.add_argument("--db-url", type=str, default=None, help="Optional database URL override")
    args = parser.parse_args()
    validate(db_url=args.db_url)
