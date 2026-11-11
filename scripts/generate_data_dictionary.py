import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

sys.path.insert(0, str(BACKEND_DIR))

from src.database.database import Base
import src.database.models

OUTPUT_FILE = PROJECT_ROOT / "docs" / "data_dictionary.md"

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)


def generate_dictionary():
    lines = [
        "# Database Data Dictionary",
        "",
        "## Overview",
        "",
        "This document is generated directly from the SQLAlchemy "
        "database models.",
        "",
        f"**Total tables:** {len(Base.metadata.tables)}",
        "",
    ]

    for table_name, table in sorted(Base.metadata.tables.items()):
        lines.extend([
            f"## {table_name}",
            "",
            "| Column | Data Type | Required | Primary Key | Foreign Key | Unique | Default |",
            "|---|---|---|---|---|---|---|",
        ])

        for column in table.columns:
            required = "Yes" if not column.nullable else "No"
            primary_key = "Yes" if column.primary_key else "No"

            foreign_keys = [
                fk.target_fullname for fk in column.foreign_keys
            ]

            foreign_key = ", ".join(foreign_keys) if foreign_keys else "No"
            unique = "Yes" if column.unique else "No"

            default = (
                str(column.default.arg)
                if column.default is not None
                and not callable(column.default.arg)
                else "—"
            )

            lines.append(
                f"| {column.name} | {column.type} | {required} "
                f"| {primary_key} | {foreign_key} | {unique} "
                f"| {default} |"
            )

        lines.append("")

        if table.constraints:
            lines.append("### Constraints")
            lines.append("")

            for constraint in table.constraints:
                lines.append(
                    f"- {type(constraint).__name__}: "
                    f"{constraint.name or 'Unnamed constraint'}"
                )

            lines.append("")

    lines.extend([
        "## Notes",
        "",
        "- Required indicates whether a column is nullable.",
        "- Primary Key identifies a record uniquely.",
        "- Foreign Key identifies a reference to another table.",
        "- Unique indicates a uniqueness constraint.",
        "- Data types are taken from SQLAlchemy model definitions.",
        "- Application-level validation rules may exist outside "
        "the database schema.",
        "",
    ])

    OUTPUT_FILE.write_text("\n".join(lines), encoding="utf-8")

    print("Data dictionary generated successfully!")
    print(f"Tables documented: {len(Base.metadata.tables)}")
    print(f"Output: {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_dictionary()