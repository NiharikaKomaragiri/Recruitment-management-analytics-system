import csv
import json
import sqlite3
from datetime import datetime, date
from pathlib import Path

import pandas as pd
from sqlalchemy import inspect

from config import DATABASE_PATH, EXPORTS_DIR
from src.database.database import engine
from src.database.models import *


def json_serializer(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    return str(value)


def generate_exports():

    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

    inspector = inspect(engine)
    table_names = sorted(inspector.get_table_names())

    export_summary = []
    manifest = []

    print("\nSTARTING DATABASE EXPORT")
    print("=" * 50)

    for table_name in table_names:

        query = f'SELECT * FROM "{table_name}" ORDER BY id'
        dataframe = pd.read_sql_query(query, engine)

        # CSV export
        csv_path = EXPORTS_DIR / f"{table_name}.csv"
        dataframe.to_csv(csv_path, index=False, encoding="utf-8")

        # JSON export
        json_path = EXPORTS_DIR / f"{table_name}.json"

        records = dataframe.to_dict(orient="records")

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(
                records,
                file,
                indent=4,
                default=json_serializer
            )

        row_count = len(dataframe)

        export_summary.append({
            "table": table_name,
            "records": row_count,
            "csv_file": csv_path.name,
            "json_file": json_path.name
        })

        manifest.append({
            "table": table_name,
            "record_count": row_count,
            "csv_file": csv_path.name,
            "json_file": json_path.name,
        })

        print(f"{table_name:<35} {row_count:>8} records")

    # -------------------------------------------------
    # SQL database dump
    # -------------------------------------------------
    sql_path = EXPORTS_DIR / "recruitment_database.sql"

    connection = sqlite3.connect(str(DATABASE_PATH))

    try:
        with open(sql_path, "w", encoding="utf-8") as file:
            for statement in connection.iterdump():
                file.write(statement + "\n")
    finally:
        connection.close()

    # -------------------------------------------------
    # Export manifest
    # -------------------------------------------------
    manifest_path = EXPORTS_DIR / "export_manifest.json"

    with open(manifest_path, "w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=4)

    # -------------------------------------------------
    # Export summary
    # -------------------------------------------------
    total_records = sum(item["records"] for item in export_summary)

    summary = {
        "project": "Recruitment Management & Analytics System",
        "total_tables": len(export_summary),
        "total_records": total_records,
        "exports": export_summary
    }

    summary_path = EXPORTS_DIR / "export_summary.json"

    with open(summary_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("=" * 50)
    print("EXPORT COMPLETED")
    print("Tables exported:", len(export_summary))
    print("Total records:", total_records)
    print("SQL dump:", sql_path)
    print("Export folder:", EXPORTS_DIR)

    return summary


if __name__ == "__main__":
    generate_exports()