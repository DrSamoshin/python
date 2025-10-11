import sys
import logging
from pythonjsonlogger import json as json_logging


def setup_logging(log_level: str = "INFO"):
    formatter = json_logging.JsonFormatter(
        '%(asctime)s %(name)s %(levelname)s %(message)s'
    )
    level = getattr(logging, log_level.upper(), logging.INFO)

    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger = logging.getLogger(logger_name)
        logger.handlers.clear()
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(level)
        logger.propagate = False

    root = logging.getLogger()
    root.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)
