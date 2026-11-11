"""
src/database/models/interview.py
==================================
Interview, Interviewer, and InterviewPanelAssignment entities.

Design
------
- ``Interview`` represents a scheduled interview round for an Application.
- ``Interviewer`` is an internal employee who conducts interviews.
- ``InterviewPanelAssignment`` is the M:N bridge: an interview can have
  multiple panel members, and an interviewer can appear in many interviews.
"""

from __future__ import annotations

import datetime
import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
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
    from src.database.models.application import Application
    from src.database.models.feedback import Feedback


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class InterviewStatus(str, enum.Enum):
    SCHEDULED   = "SCHEDULED"
    CONFIRMED   = "CONFIRMED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED   = "COMPLETED"
    CANCELLED   = "CANCELLED"
    NO_SHOW     = "NO_SHOW"
    RESCHEDULED = "RESCHEDULED"


class InterviewRound(str, enum.Enum):
    SCREENING      = "SCREENING"       # Initial HR phone/video screen
    TECHNICAL_1    = "TECHNICAL_1"     # First technical round
    TECHNICAL_2    = "TECHNICAL_2"     # Second technical round
    SYSTEM_DESIGN  = "SYSTEM_DESIGN"
    CASE_STUDY     = "CASE_STUDY"
    BEHAVIORAL     = "BEHAVIORAL"
    MANAGERIAL     = "MANAGERIAL"
    HR_FINAL       = "HR_FINAL"
    EXECUTIVE      = "EXECUTIVE"
    CUSTOM         = "CUSTOM"


class InterviewMode(str, enum.Enum):
    IN_PERSON  = "IN_PERSON"
    VIDEO      = "VIDEO"
    PHONE      = "PHONE"
    ASYNC      = "ASYNC"       # Recorded/asynchronous video interview


class InterviewerRole(str, enum.Enum):
    LEAD        = "LEAD"       # Leads the panel, owns the hiring decision
    PANELIST    = "PANELIST"   # Regular panel member
    OBSERVER    = "OBSERVER"   # Shadow/training observer, no vote


# ─────────────────────────────────────────────────────────────
# Interviewer
# ─────────────────────────────────────────────────────────────

class Interviewer(Base):
    """
    An internal employee registered as a qualified interviewer.

    Business rules
    --------------
    - ``employee_id`` is unique (maps to HR system).
    - ``email`` is unique.
    - ``is_active`` can be set False when an employee leaves.
    """

    __tablename__ = "interviewers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Format: INTVR-{seq:06d}  e.g. INTVR-000001
    interviewer_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )
    employee_id: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True,
        comment="HR system employee reference"
    )

    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True
    )
    department: Mapped[str | None] = mapped_column(String(150), nullable=True)
    job_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    specialisation: Mapped[str | None] = mapped_column(
        String(200), nullable=True,
        comment="Domain expertise e.g. 'Backend / Distributed Systems'"
    )
    max_interviews_per_week: Mapped[int] = mapped_column(
        Integer, nullable=False, default=5
    )
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

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
    panel_assignments: Mapped[List["InterviewPanelAssignment"]] = relationship(
        "InterviewPanelAssignment",
        back_populates="interviewer",
        cascade="all, delete-orphan",
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        "Feedback", back_populates="interviewer"
    )

    __table_args__ = (
        CheckConstraint(
            "max_interviews_per_week >= 1",
            name="ck_interviewer_max_interviews_positive",
        ),
    )

    def __repr__(self) -> str:
        return f"<Interviewer id={self.interviewer_id!r} name={self.full_name!r}>"


# ─────────────────────────────────────────────────────────────
# Interview
# ─────────────────────────────────────────────────────────────

class Interview(Base):
    """
    A scheduled interview session for a specific Application.

    Business rules
    --------------
    - ``scheduled_end`` must be strictly after ``scheduled_start``.
    - ``round_number`` increases monotonically within an application.
    - ``interview_id`` uses the business format INT-{YYYY}-{seq}.
    """

    __tablename__ = "interviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Format: INT-{YYYY}-{seq:06d}  e.g. INT-2026-000001
    interview_id: Mapped[str] = mapped_column(
        String(25), unique=True, nullable=False, index=True
    )

    application_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    round_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    round_name: Mapped[str] = mapped_column(
        Enum(InterviewRound, name="interview_round"),
        nullable=False,
        default=InterviewRound.SCREENING,
    )
    custom_round_name: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Used when round_name = CUSTOM"
    )

    # ── Scheduling ────────────────────────────────────────────
    scheduled_start: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    scheduled_end: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    actual_start: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    actual_end: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # ── Location ──────────────────────────────────────────────
    mode: Mapped[str] = mapped_column(
        Enum(InterviewMode, name="interview_mode"),
        nullable=False,
        default=InterviewMode.VIDEO,
    )
    location_or_meeting_link: Mapped[str | None] = mapped_column(
        String(500), nullable=True
    )

    # ── Status ────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        Enum(InterviewStatus, name="interview_status"),
        nullable=False,
        default=InterviewStatus.SCHEDULED,
        index=True,
    )
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

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
    application: Mapped["Application"] = relationship(
        "Application", back_populates="interviews"
    )
    panel_assignments: Mapped[List["InterviewPanelAssignment"]] = relationship(
        "InterviewPanelAssignment",
        back_populates="interview",
        cascade="all, delete-orphan",
    )
    feedbacks: Mapped[List["Feedback"]] = relationship(
        "Feedback", back_populates="interview", cascade="all, delete-orphan"
    )

    # ── Table Constraints ─────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "scheduled_end > scheduled_start",
            name="ck_interview_end_after_start",
        ),
        CheckConstraint(
            "actual_end IS NULL OR actual_start IS NULL OR actual_end > actual_start",
            name="ck_interview_actual_end_after_start",
        ),
        CheckConstraint(
            "round_number >= 1",
            name="ck_interview_round_number_positive",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Interview id={self.interview_id!r} "
            f"round={self.round_name!r} status={self.status!r}>"
        )


# ─────────────────────────────────────────────────────────────
# InterviewPanelAssignment  (Interview ↔ Interviewer bridge)
# ─────────────────────────────────────────────────────────────

class InterviewPanelAssignment(Base):
    """
    Many-to-many association between Interview and Interviewer.

    Business rules
    --------------
    - Each interviewer appears at most once per interview panel
      (UNIQUE interview_id + interviewer_id).
    - ``role`` distinguishes LEAD / PANELIST / OBSERVER for scoring purposes.
    """

    __tablename__ = "interview_panel_assignments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    interview_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
    )
    interviewer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interviewers.id", ondelete="RESTRICT"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(
        Enum(InterviewerRole, name="interviewer_role"),
        nullable=False,
        default=InterviewerRole.PANELIST,
    )
    confirmed: Mapped[bool] = mapped_column(default=False, nullable=False)
    assigned_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    interview: Mapped["Interview"] = relationship(
        "Interview", back_populates="panel_assignments"
    )
    interviewer: Mapped["Interviewer"] = relationship(
        "Interviewer", back_populates="panel_assignments"
    )

    # ── Constraints ───────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "interview_id", "interviewer_id",
            name="uq_panel_interview_interviewer",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<InterviewPanelAssignment interview_id={self.interview_id} "
            f"interviewer_id={self.interviewer_id} role={self.role!r}>"
        )
