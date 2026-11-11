"""
src/database/models/skill.py
=============================
Skill taxonomy and the CandidateSkill bridge table.

Design
------
- ``Skill`` is a master list of technical/soft skills.
- ``CandidateSkill`` is a many-to-many bridge between Candidate and Skill,
  carrying proficiency metadata (level, years_of_experience).
- ``RequisitionRequiredSkill`` bridges JobRequisition ↔ Skill (defined in
  requisition.py but imported here to avoid circular refs).
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
    from src.database.models.candidate import Candidate
    from src.database.models.requisition import JobRequisition


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class SkillCategory(str, enum.Enum):
    TECHNICAL   = "TECHNICAL"
    SOFT        = "SOFT"
    DOMAIN      = "DOMAIN"
    LANGUAGE    = "LANGUAGE"
    TOOL        = "TOOL"
    OTHER       = "OTHER"


class ProficiencyLevel(str, enum.Enum):
    BEGINNER     = "BEGINNER"
    INTERMEDIATE = "INTERMEDIATE"
    ADVANCED     = "ADVANCED"
    EXPERT       = "EXPERT"


# ─────────────────────────────────────────────────────────────
# Skill (master list)
# ─────────────────────────────────────────────────────────────

class Skill(Base):
    """
    Master skill taxonomy.  Each row is a distinct, deduplicated skill.

    Business rules
    --------------
    - ``name`` is unique (case-insensitive comparison enforced by application).
    - ``category`` classifies the skill for analytics filtering.
    """

    __tablename__ = "skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    skill_id: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False, index=True
    )  # Format: SKILL-{seq:05d}

    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    category: Mapped[str] = mapped_column(
        Enum(SkillCategory, name="skill_category"),
        nullable=False,
        default=SkillCategory.OTHER,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    candidate_skills: Mapped[List["CandidateSkill"]] = relationship(
        "CandidateSkill", back_populates="skill"
    )
    requisition_skills: Mapped[List["RequisitionRequiredSkill"]] = relationship(
        "RequisitionRequiredSkill", back_populates="skill"
    )

    def __repr__(self) -> str:
        return f"<Skill id={self.skill_id!r} name={self.name!r}>"


# ─────────────────────────────────────────────────────────────
# CandidateSkill  (Candidate ↔ Skill bridge)
# ─────────────────────────────────────────────────────────────

class CandidateSkill(Base):
    """
    Many-to-many association between Candidate and Skill.

    Carries proficiency metadata so we can rank candidates by skill level.

    Business rules
    --------------
    - A candidate can list a skill only once  (UNIQUE candidate_id + skill_id).
    - years_of_experience ≥ 0.
    """

    __tablename__ = "candidate_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    candidate_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("candidates.id", ondelete="CASCADE"), nullable=False
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    proficiency: Mapped[str] = mapped_column(
        Enum(ProficiencyLevel, name="proficiency_level"),
        nullable=False,
        default=ProficiencyLevel.INTERMEDIATE,
    )
    years_of_experience: Mapped[float | None] = mapped_column(nullable=True)
    is_primary: Mapped[bool] = mapped_column(
        default=False, nullable=False,
        comment="Marks the candidate's self-identified primary/headline skill"
    )

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationships ─────────────────────────────────────────
    candidate: Mapped["Candidate"] = relationship(
        "Candidate", back_populates="candidate_skills"
    )
    skill: Mapped["Skill"] = relationship("Skill", back_populates="candidate_skills")

    # ── Constraints ───────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("candidate_id", "skill_id", name="uq_candidate_skill"),
        CheckConstraint(
            "years_of_experience IS NULL OR years_of_experience >= 0",
            name="ck_candidate_skill_yoe_non_negative",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<CandidateSkill candidate_id={self.candidate_id} "
            f"skill_id={self.skill_id} proficiency={self.proficiency!r}>"
        )
