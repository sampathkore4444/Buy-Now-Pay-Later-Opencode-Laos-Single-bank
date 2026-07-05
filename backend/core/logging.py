import logging
import sys

from core.config import settings


def setup_logging():
    level = logging.DEBUG if settings.DEBUG else logging.INFO
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(handler)

    for lib in ("uvicorn", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(lib).setLevel(logging.WARNING)
