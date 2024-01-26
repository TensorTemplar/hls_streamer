import logging


logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%dT%H:%M:%SZ"
)


def get_logger(name) -> logging.Logger:
    """
    Returns a logger instance with the given name.
    """
    return logging.getLogger(name)
