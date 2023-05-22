import os
import sys
import logging

from rich.logging import RichHandler

LOG_PATH = os.getenv("CENSAR_LOG_PATH", "")
LOG_LEVEL = os.getenv("CENSAR_LOG_LEVEL", "info")
LOG_LEVEL_MAP = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def get_logger(name: str) -> logging.Logger:
    if LOG_PATH:
        logging.basicConfig(
            filename=LOG_PATH,
            level=LOG_LEVEL_MAP.get(LOG_LEVEL, "info"),
        )
    else:
        logging.basicConfig(
            level=LOG_LEVEL_MAP.get(LOG_LEVEL, "info"),
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(markup=True)],
        )

    logger = logging.getLogger(name)

    if LOG_PATH:
        sys.stdout.write = logger.debug
        sys.stdout.write = logger.info
        sys.stdout.write = logger.warning
        sys.stderr.write = logger.error

    return logger
