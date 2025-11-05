import os
from pathlib import Path
from logging.config import dictConfig

LOG_DIR = Path(os.getenv("LOG_DIR", "logs"))
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "app.log"


def setup_logging():
    dictConfig({
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": "%(levelname)s %(asctime)s %(name)s: %(message)s"},
        },
        "handlers": {
            "console": {"class": "logging.StreamHandler", "formatter": "default"},
            "file": {
                "class": "logging.handlers.TimedRotatingFileHandler",
                "formatter": "default",
                "filename": str(LOG_FILE),
                "when": "midnight",
                "backupCount": 11,
                "encoding": "utf-8",
            },
        },
        "loggers": {
            "": {"handlers": ["console", "file"], "level": "INFO"},
        },
    })
