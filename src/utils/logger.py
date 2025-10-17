"""
Centralized logging configuration for the application.

Provides consistent logging across all modules with proper formatting,
levels, and file output.
"""
import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colored output for console."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record):
        """Format log record with colors."""
        # Add color to level name
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = (
                f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            )

        return super().format(record)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
    max_file_size_mb: int = 10,
    backup_count: int = 5
) -> None:
    """
    Configure application-wide logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        format_string: Custom format string
        max_file_size_mb: Maximum size of log file before rotation
        backup_count: Number of backup files to keep

    Example:
        >>> setup_logging(level="DEBUG", log_file="app.log")
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    root_logger.handlers = []

    # Default format
    if format_string is None:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Use colored formatter for console
    console_formatter = ColoredFormatter(format_string)
    console_handler.setFormatter(console_formatter)

    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            # Create log directory if it doesn't exist
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            # Rotating file handler
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=max_file_size_mb * 1024 * 1024,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, level.upper()))

            # Use plain formatter for file
            file_formatter = logging.Formatter(format_string)
            file_handler.setFormatter(file_formatter)

            root_logger.addHandler(file_handler)

            root_logger.info(f"Logging to file: {log_file}")

        except Exception as e:
            root_logger.error(f"Failed to setup file logging: {e}")

    root_logger.info(f"Logging configured at {level.upper()} level")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Hello world")
    """
    return logging.getLogger(name)


class LogContext:
    """Context manager for temporary logging level changes."""

    def __init__(self, logger: logging.Logger, level: str):
        """
        Initialize log context.

        Args:
            logger: Logger to modify
            level: Temporary logging level
        """
        self.logger = logger
        self.new_level = getattr(logging, level.upper())
        self.old_level = None

    def __enter__(self):
        """Enter context - change logging level."""
        self.old_level = self.logger.level
        self.logger.setLevel(self.new_level)
        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context - restore original logging level."""
        self.logger.setLevel(self.old_level)


# Convenience function for temporary log level changes
def with_log_level(logger: logging.Logger, level: str):
    """
    Context manager for temporary logging level changes.

    Args:
        logger: Logger to modify
        level: Temporary logging level

    Example:
        >>> logger = get_logger(__name__)
        >>> with with_log_level(logger, "DEBUG"):
        ...     logger.debug("This will be logged")
    """
    return LogContext(logger, level)


# Module-level configuration on import
_initialized = False


def init_logging_from_config():
    """Initialize logging from configuration."""
    global _initialized

    if _initialized:
        return

    try:
        from src.utils.config import get_config

        config = get_config()
        setup_logging(
            level=config.log.level,
            log_file=config.log.file,
            format_string=config.log.format
        )

        _initialized = True

    except Exception as e:
        # Fallback to default logging if config fails
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        logging.getLogger(__name__).warning(
            f"Failed to load logging from config: {e}. Using defaults."
        )
        _initialized = True


# Example usage and testing
if __name__ == "__main__":
    # Test basic logging
    setup_logging(level="DEBUG")

    logger = get_logger(__name__)

    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")

    # Test file logging
    print("\n--- Testing file logging ---")
    setup_logging(level="INFO", log_file="./logs/test.log")

    logger = get_logger("test_module")
    logger.info("Testing file logging")

    # Test log level context
    print("\n--- Testing log level context ---")
    logger.setLevel(logging.WARNING)
    logger.info("This won't appear (level is WARNING)")

    with with_log_level(logger, "DEBUG"):
        logger.debug("This will appear (temporarily DEBUG)")

    logger.info("This won't appear again (back to WARNING)")
