import logging
from logging.config import dictConfig

from app.core.config import Settings, settings


def setup_logging(app_settings: Settings = settings) -> None:
    log_level = app_settings.log_level.upper()

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                },
                "access": {
                    "format": '%(asctime)s %(levelname)s [%(name)s] %(client_addr)s - "%(request_line)s" %(status_code)s',
                },
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "access": {
                    "class": "logging.StreamHandler",
                    "formatter": "access",
                },
            },
            "root": {
                "handlers": ["default"],
                "level": log_level,
            },
            "loggers": {
                "app": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": False,
                },
                "uvicorn.error": {
                    "handlers": ["default"],
                    "level": log_level,
                    "propagate": False,
                },
                "uvicorn.access": {
                    "handlers": ["access"],
                    "level": log_level,
                    "propagate": False,
                },
                "sqlalchemy.engine": {
                    "level": "WARNING",
                },
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
