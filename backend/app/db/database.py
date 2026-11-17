# SQLAlchemy setup, engine, and session management
import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.sql_logging import get_sql_logging_enabled

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set. Copy .env.example to .env and fill in your credentials."
    )

SQL_LOGGING_ENABLED = get_sql_logging_enabled()

# PostgreSQL-specific pool args are not valid for SQLite (used in tests).
_is_postgres = DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres")
_engine_kwargs = dict(echo=SQL_LOGGING_ENABLED, pool_pre_ping=True)
if _is_postgres:
    _engine_kwargs.update(pool_size=5, max_overflow=10)
else:
    if "sqlite" in DATABASE_URL:
        _engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in DATABASE_URL:
            _engine_kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **_engine_kwargs)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()
