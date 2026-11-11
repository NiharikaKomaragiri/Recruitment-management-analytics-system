"""
src/database/models/__init__.py
=================================
Central import aggregator for all ORM models.

Importing this package guarantees that every model class is registered
with ``Base.metadata`` before ``create_all()`` is called in init_db.py.

Usage::

    from src.database.models import (
        Department,
        JobRequisition,
        Candidate,
        ...
    )
"""

# ── Core Entities ─────────────────────────────────────────────
from src.database.models.department import Department
from src.database.models.skill import CandidateSkill, Skill
from src.database.models.candidate import Candidate, ResumeArtifact
from src.database.models.requisition import (
    JobRequisition,
    RequisitionApproval,
    RequisitionRequiredSkill,
    ScreeningRule,
)
from src.database.models.application import Application, ApplicationStageHistory
from src.database.models.interview import (
    Interview,
    InterviewPanelAssignment,
    Interviewer,
)
from src.database.models.feedback import Feedback
from src.database.models.offer import Offer

# ── Audit ─────────────────────────────────────────────────────
from src.database.models.audit import AuditEvent

__all__ = [
    # Core
    "Department",
    "Skill",
    "CandidateSkill",
    "Candidate",
    "ResumeArtifact",
    "JobRequisition",
    "RequisitionApproval",
    "RequisitionRequiredSkill",
    "ScreeningRule",
    "Application",
    "ApplicationStageHistory",
    "Interviewer",
    "Interview",
    "InterviewPanelAssignment",
    "Feedback",
    "Offer",
    # Audit
    "AuditEvent",
]
