"""
Run this script once to create every SkillFit table inside skillfit_db.
Usage (from the backend/ directory): python -m scripts.create_tables
"""

import sys
from sqlalchemy import inspect, text

from app.db.database import Base, engine
import app.db.base  # noqa: F401  (import side-effect: registers all models)


def verify_connection() -> None:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Connected to PostgreSQL successfully.")


def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    print("Base.metadata.create_all() completed.")


def list_tables() -> None:
    inspector = inspect(engine)
    tables = sorted(inspector.get_table_names())
    print("\nTables currently in the database:")
    for table in tables:
        print(f"  - {table}")

    expected = {
        "users", "faculty", "students", "student_projects", "student_skills",
        "certifications", "drives", "recommendations",
    }
    missing = expected - set(tables)
    if missing:
        print(f"\nWARNING: missing expected tables: {sorted(missing)}")
    else:
        print("\nAll expected SkillFit tables are present.")


def main() -> int:
    try:
        verify_connection()
        create_tables()
        list_tables()
    except Exception as exc:
        print(f"\nDatabase setup failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())