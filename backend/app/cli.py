"""Command-line utilities for SkillFit backend development."""

import argparse
import sys
from pathlib import Path
from typing import Sequence

from app.core.sql_logging import (
    BACKEND_ENV_PATH,
    SQLLoggingConfigurationError,
    get_persisted_sql_logging_enabled,
    set_persisted_sql_logging,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m app.cli",
        description="SkillFit backend command-line utilities.",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    sql_logging = commands.add_parser(
        "sql-logging",
        help="Manage persistent SQLAlchemy query logging.",
    )
    actions = sql_logging.add_subparsers(dest="action", required=True)
    actions.add_parser("enable", help="Enable SQL query logging after restart.")
    actions.add_parser("disable", help="Disable SQL query logging after restart.")
    actions.add_parser("status", help="Show the persisted SQL query logging setting.")

    return parser


def main(
    argv: Sequence[str] | None = None,
    *,
    env_path: Path = BACKEND_ENV_PATH,
) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.action == "enable":
            set_persisted_sql_logging(True, env_path)
            print("SQL query logging is enabled. Restart the backend to apply the change.")
            return 0

        if args.action == "disable":
            set_persisted_sql_logging(False, env_path)
            print("SQL query logging is disabled. Restart the backend to apply the change.")
            return 0

        enabled = get_persisted_sql_logging_enabled(env_path)
        state = "enabled" if enabled else "disabled"
        print(f"SQL query logging is {state}.")
        return 0
    except (SQLLoggingConfigurationError, OSError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
