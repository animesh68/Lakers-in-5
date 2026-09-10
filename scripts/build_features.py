"""
CLI Script: Build Game-Level Leakage-Safe Feature Dataset for Lakers in 5.
Usage:
    python scripts/build_features.py
"""

import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features.feature_builder import FeatureBuilder
from src.features.leakage_checks import LeakageChecker
from src.utils.logging import logger

def main():
    builder = FeatureBuilder()
    features_df, metadata = builder.build_feature_dataset()

    checker = LeakageChecker(features_df)
    leakage_summary = checker.run_all_checks()

    if leakage_summary["overall_status"] != "PASSED":
        logger.error("CRITICAL: Temporal leakage checks failed!")
        sys.exit(1)

    logger.info("=" * 70)
    logger.info("FEATURE ENGINEERING SUMMARY REPORT")
    logger.info("=" * 70)
    logger.info(f"Feature Rows: {len(features_df):,}")
    logger.info(f"Feature Columns: {len(features_df.columns)}")
    logger.info(f"Earliest Game: {features_df['game_date'].min()}")
    logger.info(f"Latest Game: {features_df['game_date'].max()}")
    logger.info(f"Targets Defined: target_home_win, target_point_margin")
    logger.info(f"Leakage Checks Status: {leakage_summary['overall_status']}")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
