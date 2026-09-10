"""
CLI Script to Update Prediction Outcomes for Lakers in 5.
Scans unsettled predictions and updates actual scores/margins from authoritative game records.
"""

import sys
import json
from src.monitoring.outcomes import OutcomeIngestionService
from src.utils.logging import logger

def main():
    service = OutcomeIngestionService()
    logger.info("Starting prediction outcome settlement job...")
    result = service.update_pending_outcomes()
    print("\n==================================================")
    print("PREDICTION OUTCOME UPDATE REPORT")
    print("==================================================")
    print(f"Pending Checked:    {result.get('checked_count', 0)}")
    print(f"Settled / Updated:  {result.get('updated_count', 0)}")
    print(f"Pending Remaining:  {result.get('pending_remaining', 0)}")
    print("==================================================\n")

if __name__ == "__main__":
    main()
