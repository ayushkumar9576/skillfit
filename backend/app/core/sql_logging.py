"""Persistent SQLAlchemy query-logging configuration."""

import os
import re
from pathlib import Path
from typing import Mapping

from dotenv import dotenv_values


SQL_LOGGING_ENV_KEY = "SQL_LOGGING"
BACKEND_ENV_PATH = Path(__file__).resolve().parents[2] / ".env"


class SQLLoggingConfigurationError(ValueError):
    """Raised when SQL_LOGGING contains an unsupported value."""


def parse_sql_logging_value(raw_value: str | None) -> bool:
    """Parse the strict true/false value used by SQL_LOGGING."""
    if raw_value is None:
        return False

    normalized = raw_value.strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False

    raise SQLLoggingConfigurationError(
        f"Invalid {SQL_LOGGING_ENV_KEY} value {raw_value!r}. Expected 'true' or 'false'."
    )


def get_sql_logging_enabled(environment: Mapping[str, str] | None = None) -> bool:
    """Return the effective SQL logging setting after environment loading."""
    values = os.environ if environment is None else environment
    return parse_sql_logging_value(values.get(SQL_LOGGING_ENV_KEY))


def get_persisted_sql_logging_enabled(env_path: Path = BACKEND_ENV_PATH) -> bool:
    """Read SQL_LOGGING directly from the backend .env file."""
    if not env_path.exists():
        return False
    values = dotenv_values(env_path)
    return parse_sql_logging_value(values.get(SQL_LOGGING_ENV_KEY))


def set_persisted_sql_logging(enabled: bool, env_path: Path = BACKEND_ENV_PATH) -> None:
    """Persist SQL_LOGGING while preserving every other .env entry."""
    env_path.parent.mkdir(parents=True, exist_ok=True)
    env_path.touch(exist_ok=True)

    lines = env_path.read_text(encoding="utf-8").splitlines(keepends=True)
    setting_pattern = re.compile(
        rf"^\s*(?:export\s+)?{re.escape(SQL_LOGGING_ENV_KEY)}\s*="
    )
    setting = f"{SQL_LOGGING_ENV_KEY}={'true' if enabled else 'false'}"
    updated_lines: list[str] = []
    setting_written = False

    for line in lines:
        if setting_pattern.match(line):
            if not setting_written:
                newline = "\r\n" if line.endswith("\r\n") else "\n"
                updated_lines.append(setting + newline)
                setting_written = True
            continue
        updated_lines.append(line)

    if not setting_written:
        if updated_lines and not updated_lines[-1].endswith(("\n", "\r")):
            updated_lines[-1] += os.linesep
        updated_lines.append(setting + os.linesep)

    env_path.write_text("".join(updated_lines), encoding="utf-8", newline="")
