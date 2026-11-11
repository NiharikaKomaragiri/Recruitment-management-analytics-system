"""
src/database/models/application.py
====================================
Application and ApplicationStageHistory entities.

Design
------
- ``Application`` links a Candidate to a JobRequisition and tracks the
  full lifecycle of a submission through the recruitment funnel.
- ``ApplicationStageHistory`` is an append-only log of every stage
  transition — previous decisions are never overwritten.
"""

from __future__ import annotations

import datetime
import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.database.models.candidate import Candidate, ResumeArtifact
    from src.database.models.interview import Interview
    from src.database.models.offer import Offer
    from src.database.models.requisition import JobRequisition


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class ApplicationStage(str, enum.Enum):
    APPLIED        = "APPLIED"          # Submitted, not yet screened
    SCREENING      = "SCREENING"        # Under automated/manual screening
    SHORTLISTED    = "SHORTLISTED"      # Passed screening, awaiting interview
    INTERVIEW      = "INTERVIEW"        # Active interview rounds
    ASSESSMENT     = "ASSESSMENT"       # Technical / cognitive assessment
    OFFER          = "OFFER"            # Offer extended
    HIRED          = "HIRED"            # Accepted and onboarding
    REJECTED       = "REJECTED"         # Rejected at any stage
    WITHDRAWN      = "WITHDRAWN"        # Candidate withdrew
    ON_HOLD        = "ON_HOLD"          # Paused by recruiter


class ApplicationStatus(str, enum.Enum):
    ACTIVE     = "ACTIVE"      # Progressing through the funnel
    CLOSED     = "CLOSED"      # Final terminal state (hired/rejected/withdrawn)
    ON_HOLD    = "ON_HOLD"     # Temporarily paused


# ─────────────────────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────────────────────

class Application(Base):
    """
    A candidate's formal application for a specific job requisition.

    Business rules
    --------------
    - A candidate can apply only once per requisition
      (UNIQUE requisition_id + candidate_id).
    - ``screening_score`` ∈ [0, 100] when set.
    - ``resume_id`` references the specific resume version submitted.
    - ``application_id`` encodes both parent IDs for traceability.
    """

    __tablename__ = "applications"

    # ── Primary Key ──────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Business Identifier ──────────────────────────────────
    # Format: APP-{requisition_business_id}-{candidate_business_id}
    # e.g. APP-REQ-2026-000001-CAND-000001
    application_id: Mapped[str] = mapped_column(
        String(80), unique=True, nullable=False, index=True
    )

    # ── Foreign Keys ─────────────────────────────────────────
    requisition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_requisitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    candidate_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("candidates.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    resume_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("resume_artifacts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Screening ─────────────────────────────────────────────
    screening_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    # ── Stage / Status ────────────────────────────────────────
    current_stage: Mapped[str] = mapped_column(
        Enum(ApplicationStage, name="application_stage"),
        nullable=False,
        default=ApplicationStage.APPLIED,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        nullable=False,
        default=ApplicationStatus.ACTIVE,
    )
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    recruiter_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ───────────────────────────────────────────
    applied_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────
    requisition: Mapped["JobRequisition"] = relationship(
        "JobRequisition", back_populates="applications"
    )
    candidate: Mapped["Candidate"] = relationship(
        "Candidate", back_populates="applications"
    )
    resume: Mapped["ResumeArtifact | None"] = relationship("ResumeArtifact")
    interviews: Mapped[List["Interview"]] = relationship(
        "Interview", back_populates="application", cascade="all, delete-orphan"
    )
    offers: Mapped[List["Offer"]] = relationship(
        "Offer", back_populates="application", cascade="all, delete-orphan"
    )
    stage_history: Mapped[List["ApplicationStageHistory"]] = relationship(
        "ApplicationStageHistory",
        back_populates="application",
        cascade="all, delete-orphan",
        order_by="ApplicationStageHistory.transitioned_at",
    )

    # ── Table Constraints ─────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "requisition_id", "candidate_id",
            name="uq_application_requisition_candidate",
        ),
        CheckConstraint(
            "screening_score IS NULL OR "
            "(screening_score >= 0 AND screening_score <= 100)",
            name="ck_application_screening_score_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Application id={self.application_id!r} "
            f"stage={self.current_stage!r} status={self.status!r}>"
        )


# ─────────────────────────────────────────────────────────────
# ApplicationStageHistory  (append-only audit log)
# ─────────────────────────────────────────────────────────────

class ApplicationStageHistory(Base):
    """
    Immutable log of every stage transition for an Application.

    Every time an application moves from one stage to another, a new row
    is appended here.  Rows are never updated or deleted.
    """

    __tablename__ = "application_stage_history"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_stage: Mapped[str | None] = mapped_column(
        Enum(ApplicationStage, name="application_stage"),
        nullable=True,  # NULL for the initial APPLIED entry
    )
    to_stage: Mapped[str] = mapped_column(
        Enum(ApplicationStage, name="application_stage"), nullable=False
    )
    changed_by: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="User or system process that triggered the transition"
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    transitioned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationship ─────────────────────────────────────────
    application: Mapped["Application"] = relationship(
        "Application", back_populates="stage_history"
    )

    def __repr__(self) -> str:
        return (
            f"<ApplicationStageHistory app_id={self.application_id} "
            f"{self.from_stage!r} -> {self.to_stage!r}>"
        )
