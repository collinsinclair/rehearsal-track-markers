"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path


def setup_logging(
    log_level: int = logging.INFO, log_file: Path | None = None
) -> logging.Logger:
    """
    Configure application logging.

    Args:
        log_level: The logging level (e.g., logging.INFO, logging.DEBUG)
        log_file: Optional path to log file. If None, logs only to console.

    Returns:
        The root logger instance
    """
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove any existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler (if log_file specified)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: The name of the logger (typically __name__)

    Returns:
        A logger instance
    """
    return logging.getLogger(name)
