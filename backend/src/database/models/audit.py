"""
src/database/models/audit.py
==============================
AuditEvent entity — a system-wide, append-only audit trail.

Design
------
- Every significant state change (create / update / delete / workflow action)
  should append an AuditEvent row.
- Rows are NEVER updated or deleted.
- ``entity_type`` + ``entity_id`` identify the target record.
- ``old_value`` and ``new_value`` store JSON-serialised before/after snapshots.
"""

from __future__ import annotations

import datetime
import enum

from sqlalchemy import DateTime, Enum, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database.database import Base


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class AuditAction(str, enum.Enum):
    CREATE   = "CREATE"
    UPDATE   = "UPDATE"
    DELETE   = "DELETE"
    APPROVE  = "APPROVE"
    REJECT   = "REJECT"
    SUBMIT   = "SUBMIT"
    ADVANCE  = "ADVANCE"   # Stage/status advancement
    WITHDRAW = "WITHDRAW"
    LOGIN    = "LOGIN"


# ─────────────────────────────────────────────────────────────
# AuditEvent
# ─────────────────────────────────────────────────────────────

class AuditEvent(Base):
    """
    System-wide immutable audit log.

    Every row represents a single auditable action taken against
    any entity in the system.

    Fields
    ------
    entity_type : str
        The model class name (e.g. "JobRequisition", "Application").
    entity_id : str
        The business identifier of the affected record.
    action : AuditAction
        The type of action performed.
    actor : str
        Who performed the action (user email, system process name, etc.).
    old_value : str (JSON)
        Serialised snapshot of the record before the change. NULL for CREATE.
    new_value : str (JSON)
        Serialised snapshot of the record after the change. NULL for DELETE.
    metadata_json : str (JSON)
        Additional context (IP address, session ID, reason codes, etc.).
    occurred_at : datetime
        Immutable UTC timestamp of when the event occurred.
    """

    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    entity_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    action: Mapped[str] = mapped_column(
        Enum(AuditAction, name="audit_action"), nullable=False, index=True
    )
    actor: Mapped[str] = mapped_column(
        String(254), nullable=False,
        comment="Email or system identifier of the actor"
    )

    old_value: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON snapshot before change"
    )
    new_value: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="JSON snapshot after change"
    )
    metadata_json: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Additional context as JSON"
    )

    occurred_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    def __repr__(self) -> str:
        return (
            f"<AuditEvent action={self.action!r} "
            f"entity={self.entity_type}/{self.entity_id} "
            f"by={self.actor!r}>"
        )
