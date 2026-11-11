"""
src/database/models/feedback.py
=================================
Feedback entity — structured evaluation submitted by an Interviewer
after completing an Interview.

Design
------
- Each (interview_id, interviewer_id) pair yields exactly one Feedback row
  (enforced by UNIQUE constraint).
- Score ranges are enforced via CheckConstraints at the database level.
- ``overall_score`` is distinct from sub-scores and must be in [0, 10].
- Sub-scores (technical, communication, problem_solving) are in [0, 10].
- ``recommendation`` captures the interviewer's hiring verdict.
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
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.database.models.interview import Interview, Interviewer


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class HiringRecommendation(str, enum.Enum):
    STRONG_HIRE   = "STRONG_HIRE"
    HIRE          = "HIRE"
    NEUTRAL       = "NEUTRAL"
    NO_HIRE       = "NO_HIRE"
    STRONG_NO_HIRE = "STRONG_NO_HIRE"


# ─────────────────────────────────────────────────────────────
# Feedback
# ─────────────────────────────────────────────────────────────

class Feedback(Base):
    """
    Structured post-interview evaluation by a panel member.

    Business rules
    --------------
    - One feedback per (interview, interviewer) pair.
    - All sub-scores ∈ [0, 10].
    - ``overall_score`` ∈ [0, 10].
    - ``recommendation`` is mandatory.
    - ``submitted_at`` is set on creation and never updated
      (feedback cannot be revised after submission).

    Business ID format: FB-{interview_business_id}-{interviewer_business_id}
    e.g. FB-INT-2026-000001-INTVR-000001
    """

    __tablename__ = "feedbacks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Format: FB-{interview_id}-{interviewer_id}
    feedback_id: Mapped[str] = mapped_column(
        String(70), unique=True, nullable=False, index=True
    )

    # ── Foreign Keys ─────────────────────────────────────────
    interview_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interviews.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    interviewer_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("interviewers.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # ── Scores (all out of 10) ────────────────────────────────
    technical_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    communication_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    problem_solving_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    cultural_fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)

    # ── Qualitative ───────────────────────────────────────────
    recommendation: Mapped[str] = mapped_column(
        Enum(HiringRecommendation, name="hiring_recommendation"),
        nullable=False,
    )
    strengths: Mapped[str | None] = mapped_column(Text, nullable=True)
    areas_for_improvement: Mapped[str | None] = mapped_column(Text, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Timestamps ───────────────────────────────────────────
    submitted_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    interview: Mapped["Interview"] = relationship(
        "Interview", back_populates="feedbacks"
    )
    interviewer: Mapped["Interviewer"] = relationship(
        "Interviewer", back_populates="feedbacks"
    )

    # ── Table Constraints ─────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "interview_id", "interviewer_id",
            name="uq_feedback_interview_interviewer",
        ),
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 10",
            name="ck_feedback_overall_score_range",
        ),
        CheckConstraint(
            "technical_score IS NULL OR (technical_score >= 0 AND technical_score <= 10)",
            name="ck_feedback_technical_score_range",
        ),
        CheckConstraint(
            "communication_score IS NULL OR (communication_score >= 0 AND communication_score <= 10)",
            name="ck_feedback_communication_score_range",
        ),
        CheckConstraint(
            "problem_solving_score IS NULL OR (problem_solving_score >= 0 AND problem_solving_score <= 10)",
            name="ck_feedback_problem_solving_score_range",
        ),
        CheckConstraint(
            "cultural_fit_score IS NULL OR (cultural_fit_score >= 0 AND cultural_fit_score <= 10)",
            name="ck_feedback_cultural_fit_score_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Feedback id={self.feedback_id!r} "
            f"overall={self.overall_score} rec={self.recommendation!r}>"
        )
