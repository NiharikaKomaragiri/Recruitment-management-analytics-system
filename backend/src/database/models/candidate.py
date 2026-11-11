"""
src/database/models/candidate.py
=================================
Candidate and ResumeArtifact entities.

Design
------
- ``Candidate`` stores contact info, education, and career metadata.
- ``ResumeArtifact`` stores uploaded resume files associated with a candidate.
  One candidate can have multiple resume versions; applications reference
  a specific resume snapshot at the time of submission.
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
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database.database import Base

if TYPE_CHECKING:
    from src.database.models.application import Application
    from src.database.models.skill import CandidateSkill


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class EducationLevel(str, enum.Enum):
    HIGH_SCHOOL  = "HIGH_SCHOOL"
    ASSOCIATE    = "ASSOCIATE"
    BACHELOR     = "BACHELOR"
    MASTER       = "MASTER"
    DOCTORATE    = "DOCTORATE"
    OTHER        = "OTHER"


class CandidateStatus(str, enum.Enum):
    ACTIVE      = "ACTIVE"       # Available and applying
    PLACED      = "PLACED"       # Accepted an offer
    WITHDRAWN   = "WITHDRAWN"    # Self-withdrew from all processes
    BLACKLISTED = "BLACKLISTED"  # Flagged (fraud, misrepresentation)
    ARCHIVED    = "ARCHIVED"     # Historical record


# ─────────────────────────────────────────────────────────────
# Candidate
# ─────────────────────────────────────────────────────────────

class Candidate(Base):
    """
    A job-seeking individual in the recruitment pipeline.

    Business rules
    --------------
    - ``email`` is globally unique (one account per person).
    - ``experience_years`` ≥ 0.
    - ``graduation_year`` is a 4-digit calendar year (1950–2100 guard).
    - No demographic or protected characteristics are stored here.
    """

    __tablename__ = "candidates"

    # ── Primary Key ──────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Business Identifier ──────────────────────────────────
    # Format: CAND-{seq:06d}  e.g. CAND-000001
    candidate_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )

    # ── Contact Information ──────────────────────────────────
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str] = mapped_column(
        String(254), unique=True, nullable=False, index=True
    )
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)

    # ── Education ─────────────────────────────────────────────
    education: Mapped[str] = mapped_column(
        Enum(EducationLevel, name="education_level"),
        nullable=False,
        default=EducationLevel.BACHELOR,
    )
    field_of_study: Mapped[str | None] = mapped_column(String(150), nullable=True)
    institution: Mapped[str | None] = mapped_column(String(200), nullable=True)
    graduation_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # ── Career Profile ────────────────────────────────────────
    experience_years: Mapped[float] = mapped_column(nullable=False, default=0.0)
    current_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    current_company: Mapped[str | None] = mapped_column(String(200), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)

    # ── Status ────────────────────────────────────────────────
    status: Mapped[str] = mapped_column(
        Enum(CandidateStatus, name="candidate_status"),
        nullable=False,
        default=CandidateStatus.ACTIVE,
    )

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
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="candidate", cascade="all, delete-orphan"
    )
    resumes: Mapped[List["ResumeArtifact"]] = relationship(
        "ResumeArtifact", back_populates="candidate", cascade="all, delete-orphan"
    )
    candidate_skills: Mapped[List["CandidateSkill"]] = relationship(
        "CandidateSkill", back_populates="candidate", cascade="all, delete-orphan"
    )

    # ── Table Constraints ─────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "experience_years >= 0",
            name="ck_candidate_experience_non_negative",
        ),
        CheckConstraint(
            "graduation_year IS NULL OR (graduation_year >= 1950 AND graduation_year <= 2100)",
            name="ck_candidate_graduation_year_range",
        ),
        CheckConstraint(
            "length(trim(full_name)) >= 2",
            name="ck_candidate_full_name_min_length",
        ),
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.candidate_id!r} name={self.full_name!r}>"


# ─────────────────────────────────────────────────────────────
# ResumeArtifact
# ─────────────────────────────────────────────────────────────

class ResumeArtifact(Base):
    """
    A versioned resume file uploaded by a candidate.

    Business rules
    --------------
    - ``file_path`` is relative to the data/raw/resumes/ directory.
    - ``file_size_kb`` > 0.
    - ``is_latest`` marks the most-recent version (maintained by service layer).
    - Deleted candidates cascade-delete their resumes.
    """

    __tablename__ = "resume_artifacts"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # Format: RES-{candidate_business_id}-V{version:02d}
    resume_id: Mapped[str] = mapped_column(
        String(40), unique=True, nullable=False, index=True
    )

    candidate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )

    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_kb: Mapped[float | None] = mapped_column(nullable=True)
    file_format: Mapped[str | None] = mapped_column(
        String(10), nullable=True
    )  # e.g. "PDF", "DOCX"
    is_latest: Mapped[bool] = mapped_column(default=True, nullable=False)
    parse_status: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # e.g. "PENDING", "PARSED", "FAILED"
    parsed_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    candidate: Mapped["Candidate"] = relationship(
        "Candidate", back_populates="resumes"
    )

    # ── Constraints ───────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "file_size_kb IS NULL OR file_size_kb > 0",
            name="ck_resume_file_size_positive",
        ),
        CheckConstraint(
            "version >= 1",
            name="ck_resume_version_positive",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ResumeArtifact id={self.resume_id!r} "
            f"candidate_id={self.candidate_id} v={self.version}>"
        )
