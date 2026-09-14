"""
Logging configuration for Lakers in 5 data pipeline.
"""

import os
import logging
from typing import Optional

def setup_logger(name: str = "lakers_in_5", log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    Configures and returns a structured logger that writes to console and log files.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)
    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File Handler
    try:
        if log_file is None:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "logs")
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, "ingestion.log")
        else:
            os.makedirs(os.path.dirname(os.path.abspath(log_file)), exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except Exception as e:
        # Gracefully log to standard output if log file creation is not permitted (e.g. read-only container root)
        logger.warning(f"Could not initialize file logger at {log_file}: {e}")

    return logger

logger = setup_logger()
