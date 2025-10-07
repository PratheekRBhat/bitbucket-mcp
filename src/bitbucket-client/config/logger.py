"""
This module configures logging for the application, providing both colored console output
and file logging.

It sets up a logger that outputs formatted log messages to both the console (with colored
log levels) and a rotating log file. The logging level is dynamically set based on the
'APP_ENV' constant (development: DEBUG, production: INFO).
"""

import logging
import os

log_dir = os.path.join(os.getcwd(), "log")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "application.log")

COLOR_RESET = "\033[0m"
COLOR_DEBUG = "\033[34m"
COLOR_INFO = "\033[32m"
COLOR_WARNING = "\033[33m"
COLOR_ERROR = "\033[31m"
COLOR_CRITICAL = "\033[91m"


def colorize_level(levelname: str) -> str:
    """
    Applies ANSI escape codes to colorize the log level in console output.

    Args:
        levelname: The log level name (e.g., 'DEBUG', 'INFO').

    Returns:
        The log level name wrapped in ANSI escape codes for colorization.
    """
    if levelname == "DEBUG":
        return f"{COLOR_DEBUG}{levelname}{COLOR_RESET}"
    elif levelname == "INFO":
        return f"{COLOR_INFO}{levelname}{COLOR_RESET}"
    elif levelname == "WARNING":
        return f"{COLOR_WARNING}{levelname}{COLOR_RESET}"
    elif levelname == "ERROR":
        return f"{COLOR_ERROR}{levelname}{COLOR_RESET}"
    elif levelname == "CRITICAL":
        return f"{COLOR_CRITICAL}{levelname}{COLOR_RESET}"
    return levelname  # Return the original level name if no match is found


class ColorFormatter(logging.Formatter):
    """
    A custom logging formatter that adds color to the log level in console output.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Formats the log record, adding color to the levelname.

        Args:
            record: The LogRecord object to be formatted.

        Returns:
            The formatted log message string.
        """
        record.levelname_colored = colorize_level(record.levelname)
        return logging.Formatter("%(asctime)s %(levelname_colored)s : %(message)s").format(record)


color_formatter = ColorFormatter("%(asctime)s %(levelname)s : %(message)s")

console_handler = logging.StreamHandler()
console_handler.setFormatter(color_formatter)

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s : %(message)s",
    filemode="a",
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(console_handler)


def set_log_level(level: str) -> None:
    """
    Sets the logging level for the application logger.

    Args:
        level: The desired logging level (e.g., 'DEBUG', 'INFO').
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    logger.setLevel(numeric_level)
    logger.info("Logging level set to %s", level)
