"""
Analytical Parquet Converter for Lakers in 5.
High-throughput, zero-data-loss conversion from raw CSVs to compressed columnar Parquet format using DuckDB.
"""

import os
import time
from typing import Dict, Any, List
import duckdb
from src.utils.logging import logger

class ParquetConverter:
    """
    Converts raw historical CSV datasets into snappy/zstd compressed Parquet datasets.
    """
    def __init__(self, raw_dir: str = None, processed_dir: str = None):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.raw_dir = raw_dir or os.path.join(base_dir, "data", "raw")
        self.processed_dir = processed_dir or os.path.join(base_dir, "data", "processed", "parquet")
        os.makedirs(self.processed_dir, exist_ok=True)

    def convert_dataset(self, csv_relative_path: str, parquet_filename: str, compression: str = "ZSTD") -> Dict[str, Any]:
        """
        Converts a single raw CSV file to an optimized Parquet file with verification.
        """
        csv_path = os.path.join(self.raw_dir, csv_relative_path)
        parquet_path = os.path.join(self.processed_dir, parquet_filename)

        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Raw CSV not found at: {csv_path}")

        start_time = time.time()
        logger.info(f"Starting Parquet conversion: {csv_relative_path} -> {parquet_filename} (Compression: {compression})...")

        con = duckdb.connect()
        
        # Count raw rows and stream to Parquet with explicit quote parsing
        sql_csv = csv_path.replace(os.sep, "/")
        sql_parquet = parquet_path.replace(os.sep, "/")
        
        # DuckDB high-speed parsing with explicit quote handling and string preservation for mixed types
        query = f"""
            COPY (
                SELECT * FROM read_csv_auto(
                    '{sql_csv}',
                    header=True,
                    quote='"',
                    escape='"',
                    null_padding=True,
                    all_varchar=True
                )
            ) TO '{sql_parquet}' (FORMAT PARQUET, COMPRESSION '{compression}', ROW_GROUP_SIZE 100000)
        """
        con.execute(query)

        # Verify Parquet output
        parquet_rows = con.execute(f"SELECT COUNT(*) FROM read_parquet('{sql_parquet}')").fetchone()[0]
        con.close()

        elapsed = time.time() - start_time
        raw_size_mb = os.path.getsize(csv_path) / (1024 * 1024)
        parquet_size_mb = os.path.getsize(parquet_path) / (1024 * 1024)
        compression_ratio = (1.0 - (parquet_size_mb / raw_size_mb)) * 100 if raw_size_mb > 0 else 0

        logger.info(f"✅ Converted {parquet_filename}: {parquet_rows:,} rows in {elapsed:.2f}s | Raw: {raw_size_mb:.1f} MB -> Parquet: {parquet_size_mb:.1f} MB ({compression_ratio:.1f}% space saved)")

        return {
            "dataset": parquet_filename,
            "parquet_rows": parquet_rows,
            "raw_size_mb": round(raw_size_mb, 2),
            "parquet_size_mb": round(parquet_size_mb, 2),
            "compression_savings_pct": round(compression_ratio, 1),
            "elapsed_seconds": round(elapsed, 2),
            "parquet_path": parquet_path
        }

    def convert_all_historical_datasets(self) -> List[Dict[str, Any]]:
        """
        Converts all key analytical datasets to Parquet.
        """
        datasets = [
            ("players/PlayerStatistics.csv", "player_game_stats.parquet"),
            ("players/PlayerStatisticsExtended.csv", "player_game_stats_extended.parquet"),
            ("games/Games.csv", "games.parquet"),
            ("games/TeamStatistics.csv", "team_game_stats.parquet"),
            ("games/TeamStatisticsExtended.csv", "team_game_stats_extended.parquet"),
        ]
        
        results = []
        for csv_rel, parquet_name in datasets:
            res = self.convert_dataset(csv_rel, parquet_name)
            results.append(res)
        return results

if __name__ == "__main__":
    converter = ParquetConverter()
    results = converter.convert_all_historical_datasets()
    print("All Parquet conversions completed successfully!")
