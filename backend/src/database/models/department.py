"""
src/database/models/department.py
==================================
Department entity — the top-level organisational unit that owns
job requisitions.
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.database.models.requisition import JobRequisition


class Department(Base):
    """
    Represents a business department that raises job requisitions.

    Business rules
    --------------
    - ``name`` must be unique across the organisation.
    - ``cost_centre`` is an optional internal finance code.
    """

    __tablename__ = "departments"

    # ── Primary Key ──────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Business Identifier ──────────────────────────────────
    # Format: DEPT-{seq:04d}  e.g. DEPT-0001
    department_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    # ── Core Fields ──────────────────────────────────────────
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_centre: Mapped[str | None] = mapped_column(String(30), nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    head_of_department: Mapped[str | None] = mapped_column(String(150), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # ── Audit Timestamps ─────────────────────────────────────
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────
    requisitions: Mapped[List["JobRequisition"]] = relationship(
        "JobRequisition",
        back_populates="department",
        cascade="all, delete-orphan",
    )

    # ── Table Constraints ─────────────────────────────────────
    __table_args__ = (
        CheckConstraint("length(name) >= 2", name="ck_department_name_min_length"),
    )

    def __repr__(self) -> str:
        return f"<Department id={self.department_id!r} name={self.name!r}>"
