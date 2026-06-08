from contextvars import ContextVar
from logging.config import dictConfig

from src.core.config import Settings

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def configure_logging(settings: Settings) -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "json": {
                    "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                    "fmt": "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
                },
                "plain": {
                    "format": "%(asctime)s %(levelname)s [%(name)s] [%(request_id)s] %(message)s",
                },
            },
            "filters": {
                "request_id": {
                    "()": "src.core.logging.RequestIDFilter",
                }
            },
            "handlers": {
                "default": {
                    "class": "logging.StreamHandler",
                    "formatter": "json",
                    "filters": ["request_id"],
                }
            },
            "root": {
                "level": settings.log_level.upper(),
                "handlers": ["default"],
            },
        }
    )


class RequestIDFilter:
    def filter(self, record) -> bool:  # noqa: ANN001
        record.request_id = request_id_var.get()
        return True
