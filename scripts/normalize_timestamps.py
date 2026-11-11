import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[1] / "data" / "database" / "recruitment.db"

FIXED_TIMESTAMP = "2026-01-01 00:00:00"

TIMESTAMP_COLUMNS = {
    "created_at",
    "updated_at",
    "uploaded_at",
    "assigned_at",
    "submitted_at",
}

def normalize_timestamps():
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
    """)

    tables = [row[0] for row in cursor.fetchall()]
    updated = []

    for table in tables:
        cursor.execute(f'PRAGMA table_info("{table}")')
        columns = {row[1] for row in cursor.fetchall()}

        for column in TIMESTAMP_COLUMNS.intersection(columns):
            cursor.execute(
                f'UPDATE "{table}" SET "{column}" = ?',
                (FIXED_TIMESTAMP,)
            )
            updated.append(f"{table}.{column}")

    connection.commit()
    connection.close()

    print("Timestamp normalization completed.")
    print(f"Fixed timestamp: {FIXED_TIMESTAMP}")
    print("Updated columns:")
    for item in sorted(updated):
        print(f"  - {item}")


if __name__ == "__main__":
    normalize_timestamps()