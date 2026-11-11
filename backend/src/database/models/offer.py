"""
src/database/models/offer.py
==============================
Offer entity — a formal compensation offer extended to a candidate
who has passed all interview rounds.

Design
------
- An application can receive multiple offer iterations (negotiations),
  but at most ONE offer may be in ACTIVE / EXTENDED / PENDING_APPROVAL
  state at any time — enforced via a partial unique index.
- ``offered_salary`` must be strictly positive.
- Lifecycle timestamps (approved_at, accepted_at, rejected_at) are
  set by the service layer as the offer progresses.
"""

from __future__ import annotations

import datetime
import enum
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.database.models.application import Application


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class OfferStatus(str, enum.Enum):
    PENDING_APPROVAL = "PENDING_APPROVAL"  # Created, awaiting internal approval
    APPROVED         = "APPROVED"          # Internally approved, not yet sent
    EXTENDED         = "EXTENDED"          # Sent to candidate
    ACCEPTED         = "ACCEPTED"          # Candidate accepted
    REJECTED         = "REJECTED"          # Candidate declined
    WITHDRAWN        = "WITHDRAWN"         # Employer rescinded
    EXPIRED          = "EXPIRED"           # Deadline passed without response
    NEGOTIATING      = "NEGOTIATING"       # Counter-offer in progress


# ─────────────────────────────────────────────────────────────
# Offer
# ─────────────────────────────────────────────────────────────

class Offer(Base):
    """
    A formal job offer extended to a candidate through an Application.

    Business rules
    --------------
    - ``offered_salary`` > 0.
    - ``offer_id`` uses the format OFF-{YYYY}-{seq:06d}.
    - At most one offer may be PENDING_APPROVAL, APPROVED, EXTENDED, or
      NEGOTIATING at the same time for a given application.  This is
      enforced by a partial unique index on (application_id) WHERE
      status IN ('PENDING_APPROVAL','APPROVED','EXTENDED','NEGOTIATING').
    - ``expiry_date`` must be in the future when the offer is EXTENDED
      (enforced at service layer).
    """

    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Format: OFF-{YYYY}-{seq:06d}  e.g. OFF-2026-000001
    offer_id: Mapped[str] = mapped_column(
        String(25), unique=True, nullable=False, index=True
    )

    # ── Foreign Key ───────────────────────────────────────────
    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Compensation ─────────────────────────────────────────
    offered_salary: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="USD"
    )
    signing_bonus: Mapped[float | None] = mapped_column(Float, nullable=True)
    equity_details: Mapped[str | None] = mapped_column(Text, nullable=True)
    benefits_summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Terms ─────────────────────────────────────────────────
    start_date: Mapped[datetime.date | None] = mapped_column(nullable=True)
    expiry_date: Mapped[datetime.date | None] = mapped_column(nullable=True)
    offer_letter_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # ── Status / Lifecycle ───────────────────────────────────
    status: Mapped[str] = mapped_column(
        Enum(OfferStatus, name="offer_status"),
        nullable=False,
        default=OfferStatus.PENDING_APPROVAL,
        index=True,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    negotiation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ───────────────────────────────────────────
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approved_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    extended_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    accepted_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    rejected_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationship ─────────────────────────────────────────
    application: Mapped["Application"] = relationship(
        "Application", back_populates="offers"
    )

    # ── Table Constraints ─────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "offered_salary > 0",
            name="ck_offer_salary_positive",
        ),
        CheckConstraint(
            "signing_bonus IS NULL OR signing_bonus >= 0",
            name="ck_offer_signing_bonus_non_negative",
        ),
        # Partial unique index: at most ONE active offer per application.
        # "Active" means status is in the set that represents an in-flight offer.
        # SQLite evaluates the WHERE clause of a partial index on INSERT/UPDATE.
        Index(
            "uix_offer_one_active_per_application",
            "application_id",
            unique=True,
            sqlite_where=text(
                "status IN ('PENDING_APPROVAL','APPROVED','EXTENDED','NEGOTIATING')"
            ),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Offer id={self.offer_id!r} "
            f"salary={self.offered_salary} status={self.status!r}>"
        )
