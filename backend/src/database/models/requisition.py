"""
src/database/models/requisition.py
====================================
JobRequisition, RequisitionApproval, ScreeningRule, and
RequisitionRequiredSkill entities.

Design
------
- ``JobRequisition`` captures an open position raised by a Department.
- ``RequisitionApproval`` is an append-only approval-decision log (history).
- ``ScreeningRule`` lets HR attach automated pass/fail rules to a requisition.
- ``RequisitionRequiredSkill`` is the M:N bridge between JobRequisition and Skill.
"""

from __future__ import annotations

import datetime
import enum
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    Boolean,
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
    from src.database.models.application import Application
    from src.database.models.department import Department
    from src.database.models.skill import Skill


# ─────────────────────────────────────────────────────────────
# Enumerations
# ─────────────────────────────────────────────────────────────

class RequisitionStatus(str, enum.Enum):
    DRAFT      = "DRAFT"       # Created, not yet submitted for approval
    PENDING    = "PENDING"     # Submitted, awaiting approval
    APPROVED   = "APPROVED"    # Approved, actively accepting applications
    ON_HOLD    = "ON_HOLD"     # Temporarily paused
    FILLED     = "FILLED"      # Position filled
    CANCELLED  = "CANCELLED"   # Cancelled before filling
    CLOSED     = "CLOSED"      # Closed (time-expired or manually)


class EmploymentType(str, enum.Enum):
    FULL_TIME  = "FULL_TIME"
    PART_TIME  = "PART_TIME"
    CONTRACT   = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    FREELANCE  = "FREELANCE"


class ApprovalDecision(str, enum.Enum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REVISED  = "REVISED"   # Returned for revision


class ScreeningRuleType(str, enum.Enum):
    MIN_EXPERIENCE   = "MIN_EXPERIENCE"    # Minimum years of experience
    MIN_EDUCATION    = "MIN_EDUCATION"     # Minimum education level
    REQUIRED_SKILL   = "REQUIRED_SKILL"   # Must have a specific skill
    KEYWORD_MATCH    = "KEYWORD_MATCH"     # Resume keyword presence
    MAX_SALARY_EXPECT = "MAX_SALARY_EXPECT" # Maximum expected salary


# ─────────────────────────────────────────────────────────────
# JobRequisition
# ─────────────────────────────────────────────────────────────

class JobRequisition(Base):
    """
    An open position raised by a Department.

    Business rules
    --------------
    - ``minimum_salary`` must be ≤ ``maximum_salary`` when both are provided.
    - ``experience_required`` ≥ 0.
    - ``openings`` ≥ 1.
    - ``status`` drives the lifecycle workflow.
    """

    __tablename__ = "job_requisitions"

    # ── Primary Key ──────────────────────────────────────────
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Business Identifier ──────────────────────────────────
    # Format: REQ-{YYYY}-{seq:06d}  e.g. REQ-2026-000001
    requisition_id: Mapped[str] = mapped_column(
        String(25), unique=True, nullable=False, index=True
    )

    # ── Foreign Keys ─────────────────────────────────────────
    department_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False
    )

    # ── Core Fields ──────────────────────────────────────────
    job_title: Mapped[str] = mapped_column(String(200), nullable=False)
    job_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    location: Mapped[str | None] = mapped_column(String(150), nullable=True)
    employment_type: Mapped[str] = mapped_column(
        Enum(EmploymentType, name="employment_type"),
        nullable=False,
        default=EmploymentType.FULL_TIME,
    )
    openings: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # ── Compensation ─────────────────────────────────────────
    minimum_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    maximum_salary: Mapped[float | None] = mapped_column(Float, nullable=True)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")

    # ── Requirements ──────────────────────────────────────────
    experience_required: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    remote_allowed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # ── Status / Lifecycle ───────────────────────────────────
    status: Mapped[str] = mapped_column(
        Enum(RequisitionStatus, name="requisition_status"),
        nullable=False,
        default=RequisitionStatus.DRAFT,
        index=True,
    )

    # ── Timestamps ───────────────────────────────────────────
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    approved_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # ── Relationships ─────────────────────────────────────────
    department: Mapped["Department"] = relationship(
        "Department", back_populates="requisitions"
    )
    applications: Mapped[List["Application"]] = relationship(
        "Application", back_populates="requisition", cascade="all, delete-orphan"
    )
    approvals: Mapped[List["RequisitionApproval"]] = relationship(
        "RequisitionApproval",
        back_populates="requisition",
        cascade="all, delete-orphan",
        order_by="RequisitionApproval.decided_at",
    )
    screening_rules: Mapped[List["ScreeningRule"]] = relationship(
        "ScreeningRule", back_populates="requisition", cascade="all, delete-orphan"
    )
    required_skills: Mapped[List["RequisitionRequiredSkill"]] = relationship(
        "RequisitionRequiredSkill",
        back_populates="requisition",
        cascade="all, delete-orphan",
    )

    # ── Table Constraints ─────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "(minimum_salary IS NULL OR maximum_salary IS NULL) "
            "OR minimum_salary <= maximum_salary",
            name="ck_req_salary_min_lte_max",
        ),
        CheckConstraint(
            "experience_required >= 0",
            name="ck_req_experience_non_negative",
        ),
        CheckConstraint(
            "openings >= 1",
            name="ck_req_openings_at_least_one",
        ),
        CheckConstraint(
            "minimum_salary IS NULL OR minimum_salary >= 0",
            name="ck_req_min_salary_non_negative",
        ),
        CheckConstraint(
            "maximum_salary IS NULL OR maximum_salary >= 0",
            name="ck_req_max_salary_non_negative",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<JobRequisition id={self.requisition_id!r} "
            f"title={self.job_title!r} status={self.status!r}>"
        )


# ─────────────────────────────────────────────────────────────
# RequisitionApproval  (append-only history)
# ─────────────────────────────────────────────────────────────

class RequisitionApproval(Base):
    """
    Immutable approval decision log for a JobRequisition.

    Each approval action (APPROVE / REJECT / REVISE) appends a new row.
    Records are never updated or deleted (audit integrity).
    """

    __tablename__ = "requisition_approvals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    requisition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_requisitions.id", ondelete="CASCADE"), nullable=False
    )
    approver_name: Mapped[str] = mapped_column(String(200), nullable=False)
    approver_role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    decision: Mapped[str] = mapped_column(
        Enum(ApprovalDecision, name="approval_decision"), nullable=False
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    decided_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationship ─────────────────────────────────────────
    requisition: Mapped["JobRequisition"] = relationship(
        "JobRequisition", back_populates="approvals"
    )

    def __repr__(self) -> str:
        return (
            f"<RequisitionApproval req_id={self.requisition_id} "
            f"decision={self.decision!r} by={self.approver_name!r}>"
        )


# ─────────────────────────────────────────────────────────────
# ScreeningRule
# ─────────────────────────────────────────────────────────────

class ScreeningRule(Base):
    """
    An automated pass/fail rule attached to a JobRequisition.

    Rules are evaluated by the screening service to compute
    each application's screening score.

    Business rules
    --------------
    - ``weight`` must be between 0.0 and 1.0 (percentage contribution).
    - ``is_knockout`` marks a rule whose failure immediately disqualifies
      an application, regardless of other scores.
    """

    __tablename__ = "screening_rules"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, index=True
    )  # Format: RULE-{req_business_id}-{seq:03d}

    requisition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("job_requisitions.id", ondelete="CASCADE"), nullable=False
    )
    rule_type: Mapped[str] = mapped_column(
        Enum(ScreeningRuleType, name="screening_rule_type"), nullable=False
    )
    rule_value: Mapped[str] = mapped_column(
        String(255), nullable=False,
        comment="Threshold or keyword — interpreted by rule_type"
    )
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    is_knockout: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # ── Relationship ─────────────────────────────────────────
    requisition: Mapped["JobRequisition"] = relationship(
        "JobRequisition", back_populates="screening_rules"
    )

    # ── Constraints ───────────────────────────────────────────
    __table_args__ = (
        CheckConstraint(
            "weight >= 0.0 AND weight <= 1.0",
            name="ck_screening_rule_weight_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<ScreeningRule id={self.rule_id!r} "
            f"type={self.rule_type!r} knockout={self.is_knockout}>"
        )


# ─────────────────────────────────────────────────────────────
# RequisitionRequiredSkill  (JobRequisition ↔ Skill bridge)
# ─────────────────────────────────────────────────────────────

class RequisitionRequiredSkill(Base):
    """
    Many-to-many association between JobRequisition and Skill.

    Carries metadata about whether the skill is mandatory and
    the minimum expected proficiency level.
    """

    __tablename__ = "requisition_required_skills"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    requisition_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("job_requisitions.id", ondelete="CASCADE"),
        nullable=False,
    )
    skill_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False
    )
    is_mandatory: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    minimum_proficiency: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # Refers to ProficiencyLevel values

    # ── Relationships ─────────────────────────────────────────
    requisition: Mapped["JobRequisition"] = relationship(
        "JobRequisition", back_populates="required_skills"
    )
    skill: Mapped["Skill"] = relationship(
        "Skill", back_populates="requisition_skills"
    )

    # ── Constraints ───────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "requisition_id", "skill_id", name="uq_req_required_skill"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<RequisitionRequiredSkill req_id={self.requisition_id} "
            f"skill_id={self.skill_id} mandatory={self.is_mandatory}>"
        )
