import logging
import sys

from src.config import settings

# ANSI color codes
COLORS = {
    "DEBUG": "\033[36m",  # Cyan
    "INFO": "\033[32m",  # Green
    "WARNING": "\033[33m",  # Yellow
    "ERROR": "\033[31m",  # Red
    "CRITICAL": "\033[35m",  # Magenta
}
RESET = "\033[0m"

LOG_FORMAT = "[%(levelname)s] %(asctime)s - %(message)s"
DATEFMT = "%Y-%m-%d %H:%M:%S"


class ColoredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Add color to levelname
        levelname = record.levelname
        if levelname in COLORS:
            colored_levelname = f"{COLORS[levelname]}{levelname}{RESET}"
            record.levelname = colored_levelname
        else:
            record.levelname = levelname

        return super().format(record)


def _level_from_string(level_str: str) -> int:
    """
    Convert a logging level name (e.g. "INFO") to the numeric level.
    Defaults to logging.INFO for unknown values.
    """
    if not level_str:
        return logging.INFO
    return getattr(logging, level_str.upper(), logging.INFO)


def logger(name: str = "TradeMCP") -> logging.Logger:
    """
    Factory that returns a configured logger instance with colored output.

    Usage:
        from src.utils.logger import logger
        log = logger(__name__)   # preferred
        # or keep the default name:
        log = logger()
    """
    lvl = _level_from_string(settings.logging_level)

    _logger = logging.getLogger(name)

    if not _logger.handlers:
        _logger.setLevel(lvl)

        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(lvl)
        handler.setFormatter(ColoredFormatter(fmt=LOG_FORMAT, datefmt=DATEFMT))

        _logger.addHandler(handler)

    return _logger