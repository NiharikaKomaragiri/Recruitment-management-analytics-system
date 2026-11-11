"""
src/database/init_db.py
========================
Database initialisation script.

Run this module directly to:
  1. Import all ORM models (registers them with Base.metadata).
  2. Create all tables in the SQLite database (idempotent — skips
     existing tables).
  3. Verify SQLite foreign key enforcement is ON.
  4. Print a human-readable summary of every table that now exists.

Usage::

    python src/database/init_db.py

Or from the project root::

    .venv\\Scripts\\python src/database/init_db.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# ── Make project root importable ─────────────────────────────
# When running as a script, Python may not have the project root on sys.path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# ── Imports ───────────────────────────────────────────────────
from sqlalchemy import inspect, text

from config import DATABASE_PATH, DATABASE_URL
from src.database.database import Base, SessionLocal, engine, verify_foreign_keys

# Import ALL models — this populates Base.metadata
import src.database.models  # noqa: F401  (side-effect import)


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _separator(char: str = "─", width: int = 60) -> str:
    return char * width


def _print_header(title: str) -> None:
    print(_separator("═"))
    print(f"  {title}")
    print(_separator("═"))


def _print_section(title: str) -> None:
    print(f"\n{_separator()}")
    print(f"  {title}")
    print(_separator())


# ─────────────────────────────────────────────────────────────
# Initialisation Steps
# ─────────────────────────────────────────────────────────────

def create_tables() -> list[str]:
    """
    Create all tables defined in Base.metadata.

    Returns the sorted list of table names that now exist in the DB.
    """
    Base.metadata.create_all(bind=engine)
    inspector = inspect(engine)
    return sorted(inspector.get_table_names())


def verify_fk_enforcement() -> bool:
    """
    Open a session and confirm PRAGMA foreign_keys = 1.
    """
    db = SessionLocal()
    try:
        return verify_foreign_keys(db)
    finally:
        db.close()


def print_table_summary(table_names: list[str]) -> None:
    """
    Print a formatted summary of every table with its column count.
    """
    inspector = inspect(engine)
    _print_section("TABLE SUMMARY")
    print(f"  {'#':<4} {'Table Name':<45} {'Columns':>8}")
    print(f"  {'-'*4} {'-'*45} {'-'*8}")

    for idx, name in enumerate(table_names, start=1):
        columns = inspector.get_columns(name)
        col_count = len(columns)
        print(f"  {idx:<4} {name:<45} {col_count:>8}")

    print(f"\n  Total tables : {len(table_names)}")


def print_fk_summary() -> None:
    """
    Print foreign key counts per table for verification.
    """
    inspector = inspect(engine)
    _print_section("FOREIGN KEY RELATIONSHIPS")
    total_fks = 0

    for table_name in sorted(inspector.get_table_names()):
        fks = inspector.get_foreign_keys(table_name)
        if fks:
            for fk in fks:
                referred = f"{fk['referred_table']}.{fk['referred_columns']}"
                local    = ", ".join(fk["constrained_columns"])
                print(f"  {table_name}.{local} --> {referred}")
                total_fks += 1

    print(f"\n  Total FK relationships : {total_fks}")


def print_index_summary() -> None:
    """
    Print unique / partial indexes per table.
    """
    inspector = inspect(engine)
    _print_section("UNIQUE INDEXES")

    for table_name in sorted(inspector.get_table_names()):
        indexes = inspector.get_indexes(table_name)
        for idx in indexes:
            if idx.get("unique"):
                cols = ", ".join(idx["column_names"])
                print(f"  [{table_name}]  UNIQUE ({cols})")


# ─────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────

def main() -> None:
    _print_header("Recruitment Management & Analytics System — Database Init")

    print(f"\n  Database URL  : {DATABASE_URL}")
    print(f"  Database file : {DATABASE_PATH}")
    print(f"  DB file exists: {DATABASE_PATH.exists()}")

    # Step 1 — Create tables
    print("\n[1/4] Creating tables ...")
    table_names = create_tables()
    print(f"      Done. {len(table_names)} tables in database.")

    # Step 2 — Verify FK enforcement
    print("\n[2/4] Verifying foreign key enforcement ...")
    fk_on = verify_fk_enforcement()
    if fk_on:
        print("      PRAGMA foreign_keys = ON  [OK]")
    else:
        print("      WARNING: PRAGMA foreign_keys = OFF — FK enforcement inactive!")
        sys.exit(1)

    # Step 3 — Print summaries
    print("\n[3/4] Printing schema summary ...")
    print_table_summary(table_names)
    print_fk_summary()
    print_index_summary()

    # Step 4 — Done
    _print_section("INITIALISATION COMPLETE")
    print("  The database is ready for use.\n")


if __name__ == "__main__":
    main()
