"""Central logging setup, called once (from `config.py`) before any other
project module runs.

Why this lives here instead of each module calling `logging.basicConfig()`:

- stdlib `logging` is what Sentry's `LoggingIntegration` (and most log
  aggregators) hooks into automatically
- as long as call sites use `logging.getLogger(__name__)` instead of
  `print()`, adding Sentry later is just `sentry_sdk.init(...,
  integrations=[LoggingIntegration(...)])` -- no call sites need to change
- same story for an AWS move: CloudWatch (via the ECS/Fargate `awslogs`
  driver, same as Railway) ingests stdout/stderr as text, so emitting JSON
  here means both Railway's log viewer today and CloudWatch Logs Insights
  later can filter/query on fields instead of grepping raw text

`ENV="local"` is your laptop only:

- `dev`/`stage`/`prod` are all cloud stages and get identical,
  production-grade log handling
    - only their *content* (log level, verbosity) should ever differ
      between them, via `LOG_LEVEL`, not their format or destination
"""

import json
import logging
import logging.config
from datetime import datetime, timezone
from pathlib import Path

# Where local-mode logs are written, one file per calendar day (see setup_logging).
LOG_DIR = Path("logs")

# Attributes present on every stdlib LogRecord. Anything else on the record
# was passed in via `logger.info(..., extra={...})` and is treated as
# structured, application-specific context.
_RESERVED_LOG_RECORD_ATTRS = frozenset(
    {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        # important if debugging thread realted
        "thread",
        "threadName",
        # important if debugging multi processing/worker related
        "processName",
        "process",
        # important if debugging concurrency related
        "taskName",
        "message",
    }
)


class JSONFormatter(logging.Formatter):
    """One JSON object per line -- easy for Railway/CloudWatch/Sentry to parse."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        extra = {
            key: value
            for key, value in record.__dict__.items()
            if key not in _RESERVED_LOG_RECORD_ATTRS
        }
        if extra:
            payload["extra"] = extra

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


_configured = False


def setup_logging(env: str, level: str = "INFO") -> None:
    """Configure the root logger once per process.

    - `env == "local"`: human-readable one-liner formatter for
      Docker-compose use on your laptop, plus a `logs/YYYY-MM-DD.log` file
      (created if missing, appended to otherwise) so logs are readable
      straight from the repo instead of via `docker compose logs`/Docker
      Desktop
    - every cloud stage (`dev`, `stage`, `prod`, ...): single-line JSON to
      stdout only, no file handler
        - Docker, Railway, and CloudWatch's `awslogs` driver all just
          capture the container's stdout/stderr stream, and
          `PYTHONUNBUFFERED=1` (already set in both Dockerfiles) ensures
          lines aren't held back in a buffer
        - those container filesystems are ephemeral, so a log file there
          would just be lost on every redeploy
    """
    global _configured
    if _configured:
        return
    _configured = True

    formatter = "plain" if env == "local" else "json"

    handlers = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": formatter,
            "stream": "ext://sys.stdout",
        },
    }
    root_handlers = ["console"]

    if env == "local":
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        today = datetime.now().strftime("%Y-%m-%d")
        handlers["file"] = {
            "class": "logging.FileHandler",
            "formatter": formatter,
            "filename": str(LOG_DIR / f"{today}.log"),
            "mode": "a",
            "encoding": "utf-8",
        }
        root_handlers.append("file")

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "plain": {
                    "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                },
                "json": {"()": f"{__name__}.JSONFormatter"},
            },
            "handlers": handlers,
            "root": {
                "handlers": root_handlers,
                "level": level,
            },
            "loggers": {
                # SQLAlchemy's own query/pool logging is extremely verbose at
                # INFO -- keep it opt-in rather than drowning out app logs.
                "sqlalchemy.engine": {"level": "WARNING"},
                "sqlalchemy.pool": {"level": "WARNING"},
                # The Supabase SDK logs every HTTP call at INFO via httpx/httpcore,
                # and httpx's HTTP/2 support (hpack/h2) logs every header frame at DEBUG.
                "httpx": {"level": "WARNING"},
                "httpcore": {"level": "WARNING"},
                "hpack": {"level": "WARNING"},
                "h2": {"level": "WARNING"},
                # uvicorn --reload's file watcher logs every detected filesystem
                # change (including our own log file being written to) at DEBUG.
                "watchfiles": {"level": "WARNING"},
            },
        }
    )
