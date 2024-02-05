import logging
import os


# Retrieve log level from an environment variable
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Ensure the provided log level is valid
valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
if log_level not in valid_log_levels:
    log_level = "INFO"

logging.basicConfig(
    level=getattr(logging, log_level),  # Convert log level string to logging level
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)


def get_logger(name) -> logging.Logger:
    """
    Returns a logger instance with the given name.
    """
    return logging.getLogger(name)
