import logging
import logging.config
from typing import Any

from pythonjsonlogger import jsonlogger

from app.core.settings import Settings


class JsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(
        self,
        log_record: dict[str, Any],
        record: logging.LogRecord,
        message_dict: dict[str, Any],
    ) -> None:
        super().add_fields(log_record, record, message_dict)
        log_record["level"] = record.levelname
        log_record["logger"] = record.name


def configure_logging(settings: Settings) -> None:
    formatter: dict[str, Any]
    if settings.log_format == "json":
        formatter = {
            "()": "app.core.logging.JsonFormatter",
            "format": "%(asctime)s %(level)s %(name)s %(message)s",
        }
    else:
        formatter = {
            "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        }

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"default": formatter},
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {
                "handlers": ["default"],
                "level": settings.log_level.upper(),
            },
            "loggers": {
                "uvicorn.access": {
                    "handlers": ["default"],
                    "level": settings.log_level.upper(),
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "handlers": ["default"],
                    "level": "WARNING",
                    "propagate": False,
                },
            },
        }
    )
