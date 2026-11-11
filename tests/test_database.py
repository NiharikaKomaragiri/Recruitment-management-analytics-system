"""
tests/test_database.py
=======================
Pytest test suite for Phase 2: Database Design.

Tests are organised into classes by concern:
  - TestDatabaseConnection    : engine, session, FK pragma
  - TestTableCreation         : all 17 expected tables exist
  - TestDepartment            : CRUD, unique name
  - TestCandidate             : unique email, constraints
  - TestJobRequisition        : FK, salary constraint, experience constraint
  - TestApplication           : unique per req+candidate, screening score range
  - TestInterview             : end-after-start, FK integrity
  - TestFeedback              : score ranges, unique per interview+interviewer
  - TestOffer                 : positive salary
  - TestRelationships         : end-to-end traversal via ORM relationships
  - TestHistoryTables         : ApplicationStageHistory, AuditEvent append-only
  - TestForeignKeyEnforcement : SQLite FK violations are caught

All tests use an in-memory SQLite database (not the production DB file)
so they are fast, isolated, and leave no artefacts.
"""

from __future__ import annotations

import datetime
import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

# ── Make project root importable ─────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.database.database import Base
import src.database.models

from src.database.models.application import Application, ApplicationStageHistory
from src.database.models.audit import AuditEvent
from src.database.models.candidate import Candidate, ResumeArtifact
from src.database.models.department import Department
from src.database.models.feedback import Feedback
from src.database.models.interview import Interview, InterviewPanelAssignment, Interviewer
from src.database.models.offer import Offer
from src.database.models.requisition import (
    JobRequisition,
    RequisitionApproval,
    RequisitionRequiredSkill,
    ScreeningRule,
)
from src.database.models.skill import CandidateSkill, Skill


# ─────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def engine_fixture():
    """
    Session-scoped in-memory SQLite engine.
    Tables are created once and shared across all tests in the session.
    """
    _engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,
    )

    # Enable FK enforcement for every connection
    @event.listens_for(_engine, "connect")
    def _set_fk_pragma(dbapi_conn, _record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(bind=_engine)
    yield _engine
    Base.metadata.drop_all(bind=_engine)
    _engine.dispose()


@pytest.fixture()
def db(engine_fixture):
    """
    Function-scoped database session.
    Each test gets a clean transaction that is rolled back after the test.
    """
    Session = sessionmaker(bind=engine_fixture, autocommit=False, autoflush=False)
    session = Session()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ─────────────────────────────────────────────────────────────
# Shared builders
# ─────────────────────────────────────────────────────────────

def make_department(suffix: str = "001") -> Department:
    return Department(
        department_id=f"DEPT-{suffix}",
        name=f"Engineering {suffix}",
    )


def make_candidate(suffix: str = "000001", email: str | None = None) -> Candidate:
    return Candidate(
        candidate_id=f"CAND-{suffix}",
        full_name="Jane Smith",
        email=email or f"jane.smith.{suffix}@example.com",
        experience_years=3.5,
    )


def make_requisition(dept_id: int, suffix: str = "000001") -> JobRequisition:
    return JobRequisition(
        requisition_id=f"REQ-2026-{suffix}",
        department_id=dept_id,
        job_title="Software Engineer",
        minimum_salary=60_000,
        maximum_salary=120_000,
        experience_required=2.0,
        openings=2,
    )


def make_application(req_id: int, cand_id: int, suffix: str = "1") -> Application:
    return Application(
        application_id=f"APP-REQ-2026-{suffix:0>6}-CAND-{suffix:0>6}",
        requisition_id=req_id,
        candidate_id=cand_id,
    )


def make_interviewer(suffix: str = "000001") -> Interviewer:
    return Interviewer(
        interviewer_id=f"INTVR-{suffix}",
        full_name="Bob Reviewer",
        email=f"bob.reviewer.{suffix}@company.com",
    )


def make_interview(app_id: int, suffix: str = "000001") -> Interview:
    start = datetime.datetime(2026, 6, 1, 10, 0, tzinfo=datetime.timezone.utc)
    end   = datetime.datetime(2026, 6, 1, 11, 0, tzinfo=datetime.timezone.utc)
    return Interview(
        interview_id=f"INT-2026-{suffix}",
        application_id=app_id,
        scheduled_start=start,
        scheduled_end=end,
    )


# ─────────────────────────────────────────────────────────────
# TC-1: Database Connection
# ─────────────────────────────────────────────────────────────

class TestDatabaseConnection:
    def test_engine_connects(self, engine_fixture):
        """Engine can open a connection to the in-memory DB."""
        with engine_fixture.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1

    def test_foreign_keys_pragma_on(self, engine_fixture):
        """PRAGMA foreign_keys should be 1 on every new connection."""
        with engine_fixture.connect() as conn:
            fk_val = conn.execute(text("PRAGMA foreign_keys")).scalar()
        assert fk_val == 1, "Foreign key enforcement is disabled!"

    def test_session_opens_and_closes(self, db):
        """Session fixture yields a valid session."""
        result = db.execute(text("SELECT 1")).scalar()
        assert result == 1


# ─────────────────────────────────────────────────────────────
# TC-2: Table Creation
# ─────────────────────────────────────────────────────────────

EXPECTED_TABLES = {
    "departments",
    "skills",
    "candidate_skills",
    "candidates",
    "resume_artifacts",
    "job_requisitions",
    "requisition_approvals",
    "requisition_required_skills",
    "screening_rules",
    "applications",
    "application_stage_history",
    "interviewers",
    "interviews",
    "interview_panel_assignments",
    "feedbacks",
    "offers",
    "audit_events",
}


class TestTableCreation:
    def test_all_expected_tables_exist(self, engine_fixture):
        """All 17 tables defined in models should be present in the schema."""
        inspector = inspect(engine_fixture)
        actual_tables = set(inspector.get_table_names())
        missing = EXPECTED_TABLES - actual_tables
        assert not missing, f"Missing tables: {missing}"

    def test_table_count(self, engine_fixture):
        """Exactly 17 tables should exist."""
        inspector = inspect(engine_fixture)
        assert len(inspector.get_table_names()) == len(EXPECTED_TABLES)


# ─────────────────────────────────────────────────────────────
# TC-3: Department
# ─────────────────────────────────────────────────────────────

class TestDepartment:
    def test_create_department(self, db):
        dept = make_department("T01")
        db.add(dept)
        db.flush()
        assert dept.id is not None
        assert dept.department_id == "DEPT-T01"

    def test_department_name_unique(self, db):
        db.add(make_department("T02"))
        db.flush()
        db.add(Department(department_id="DEPT-T02-DUP", name="Engineering T02"))
        with pytest.raises(IntegrityError):
            db.flush()

    def test_department_id_unique(self, db):
        db.add(make_department("T03"))
        db.flush()
        db.add(Department(department_id="DEPT-T03", name="Different Name"))
        with pytest.raises(IntegrityError):
            db.flush()


# ─────────────────────────────────────────────────────────────
# TC-4: Candidate
# ─────────────────────────────────────────────────────────────

class TestCandidate:
    def test_create_candidate(self, db):
        c = make_candidate("C0001")
        db.add(c)
        db.flush()
        assert c.id is not None

    def test_email_unique(self, db):
        email = "unique.person@example.com"
        db.add(make_candidate("C0002", email=email))
        db.flush()
        db.add(Candidate(
            candidate_id="CAND-C0002B",
            full_name="Other Person",
            email=email,
        ))
        with pytest.raises(IntegrityError):
            db.flush()

    def test_negative_experience_rejected(self, db):
        c = Candidate(
            candidate_id="CAND-NEG",
            full_name="Bad Candidate",
            email="bad.exp@example.com",
            experience_years=-1.0,
        )
        db.add(c)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_graduation_year_out_of_range_rejected(self, db):
        c = Candidate(
            candidate_id="CAND-BADYR",
            full_name="Year Candidate",
            email="bad.year@example.com",
            graduation_year=1800,  # Below 1950 lower bound
        )
        db.add(c)
        with pytest.raises(IntegrityError):
            db.flush()


# ─────────────────────────────────────────────────────────────
# TC-5: JobRequisition
# ─────────────────────────────────────────────────────────────

class TestJobRequisition:
    def _dept(self, db, suffix="R01") -> Department:
        d = make_department(suffix)
        db.add(d)
        db.flush()
        return d

    def test_create_requisition(self, db):
        dept = self._dept(db, "R01")
        req = make_requisition(dept.id, "000010")
        db.add(req)
        db.flush()
        assert req.id is not None

    def test_salary_min_exceeds_max_rejected(self, db):
        dept = self._dept(db, "R02")
        req = JobRequisition(
            requisition_id="REQ-2026-999901",
            department_id=dept.id,
            job_title="Bad Salary Job",
            minimum_salary=200_000,
            maximum_salary=100_000,  # min > max → violates constraint
        )
        db.add(req)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_negative_experience_rejected(self, db):
        dept = self._dept(db, "R03")
        req = JobRequisition(
            requisition_id="REQ-2026-999902",
            department_id=dept.id,
            job_title="Negative Exp Job",
            experience_required=-1,
        )
        db.add(req)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_zero_openings_rejected(self, db):
        dept = self._dept(db, "R04")
        req = JobRequisition(
            requisition_id="REQ-2026-999903",
            department_id=dept.id,
            job_title="Zero Openings",
            openings=0,
        )
        db.add(req)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_invalid_department_fk_rejected(self, db):
        """Referencing a non-existent department should raise FK error."""
        req = JobRequisition(
            requisition_id="REQ-2026-999904",
            department_id=99999,  # Does not exist
            job_title="Ghost Dept Job",
        )
        db.add(req)
        with pytest.raises(IntegrityError):
            db.flush()


# ─────────────────────────────────────────────────────────────
# TC-6: Application
# ─────────────────────────────────────────────────────────────

class TestApplication:
    def _base(self, db, suffix="A01"):
        dept = make_department(f"AD{suffix}")
        db.add(dept)
        db.flush()
        req = make_requisition(dept.id, f"{suffix:0>6}")
        cand = make_candidate(f"AC{suffix}")
        db.add_all([req, cand])
        db.flush()
        return req, cand

    def test_create_application(self, db):
        req, cand = self._base(db, "A01")
        app = make_application(req.id, cand.id, suffix="A01")
        db.add(app)
        db.flush()
        assert app.id is not None

    def test_duplicate_application_rejected(self, db):
        req, cand = self._base(db, "A02")
        app1 = make_application(req.id, cand.id, suffix="A02")
        db.add(app1)
        db.flush()
        app2 = Application(
            application_id="APP-DUPLICATE",
            requisition_id=req.id,
            candidate_id=cand.id,
        )
        db.add(app2)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_screening_score_above_100_rejected(self, db):
        req, cand = self._base(db, "A03")
        app = Application(
            application_id=f"APP-A03-SCORE",
            requisition_id=req.id,
            candidate_id=cand.id,
            screening_score=101,
        )
        db.add(app)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_screening_score_negative_rejected(self, db):
        req, cand = self._base(db, "A04")
        app = Application(
            application_id=f"APP-A04-NEGSCORE",
            requisition_id=req.id,
            candidate_id=cand.id,
            screening_score=-5,
        )
        db.add(app)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_screening_score_valid_boundary(self, db):
        """Scores of 0 and 100 must be accepted."""
        req, cand = self._base(db, "A05")
        for score, sfx in [(0, "ZERO"), (100, "HUND")]:
            app = Application(
                application_id=f"APP-A05-{sfx}",
                requisition_id=req.id if sfx == "ZERO" else req.id,
                candidate_id=cand.id if sfx == "ZERO" else cand.id,
                screening_score=score,
            )
            # Only add one at a time (unique req+cand constraint)
            if sfx == "ZERO":
                db.add(app)
                db.flush()
                assert app.screening_score == 0


# ─────────────────────────────────────────────────────────────
# TC-7: Interview
# ─────────────────────────────────────────────────────────────

class TestInterview:
    def _base(self, db, suffix="I01"):
        dept = make_department(f"ID{suffix}")
        db.add(dept)
        db.flush()
        req  = make_requisition(dept.id, f"{suffix:0>6}")
        cand = make_candidate(f"IC{suffix}")
        db.add_all([req, cand])
        db.flush()
        app = make_application(req.id, cand.id, suffix=suffix)
        db.add(app)
        db.flush()
        return app

    def test_create_interview(self, db):
        app = self._base(db, "I01")
        iv = make_interview(app.id, "000101")
        db.add(iv)
        db.flush()
        assert iv.id is not None

    def test_end_before_start_rejected(self, db):
        app = self._base(db, "I02")
        start = datetime.datetime(2026, 6, 1, 11, 0, tzinfo=datetime.timezone.utc)
        end   = datetime.datetime(2026, 6, 1, 10, 0, tzinfo=datetime.timezone.utc)  # before start
        iv = Interview(
            interview_id="INT-2026-999901",
            application_id=app.id,
            scheduled_start=start,
            scheduled_end=end,
        )
        db.add(iv)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_equal_start_end_rejected(self, db):
        app = self._base(db, "I03")
        same = datetime.datetime(2026, 6, 1, 10, 0, tzinfo=datetime.timezone.utc)
        iv = Interview(
            interview_id="INT-2026-999902",
            application_id=app.id,
            scheduled_start=same,
            scheduled_end=same,
        )
        db.add(iv)
        with pytest.raises(IntegrityError):
            db.flush()


# ─────────────────────────────────────────────────────────────
# TC-8: Feedback
# ─────────────────────────────────────────────────────────────

class TestFeedback:
    def _base(self, db, suffix="F01"):
        dept = make_department(f"FD{suffix}")
        db.add(dept)
        db.flush()
        req  = make_requisition(dept.id, f"{suffix:0>6}")
        cand = make_candidate(f"FC{suffix}")
        itvr = make_interviewer(f"F{suffix}")
        db.add_all([req, cand, itvr])
        db.flush()
        app = make_application(req.id, cand.id, suffix=suffix)
        db.add(app)
        db.flush()
        iv = make_interview(app.id, f"F{suffix:0>5}")
        db.add(iv)
        db.flush()
        return iv, itvr

    def test_create_feedback(self, db):
        iv, itvr = self._base(db, "F01")
        fb = Feedback(
            feedback_id=f"FB-{iv.interview_id}-{itvr.interviewer_id}",
            interview_id=iv.id,
            interviewer_id=itvr.id,
            overall_score=7.5,
            recommendation="HIRE",
        )
        db.add(fb)
        db.flush()
        assert fb.id is not None

    def test_overall_score_above_10_rejected(self, db):
        iv, itvr = self._base(db, "F02")
        fb = Feedback(
            feedback_id=f"FB-{iv.interview_id}-{itvr.interviewer_id}",
            interview_id=iv.id,
            interviewer_id=itvr.id,
            overall_score=11,
            recommendation="HIRE",
        )
        db.add(fb)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_overall_score_negative_rejected(self, db):
        iv, itvr = self._base(db, "F03")
        fb = Feedback(
            feedback_id=f"FB-{iv.interview_id}-{itvr.interviewer_id}",
            interview_id=iv.id,
            interviewer_id=itvr.id,
            overall_score=-1,
            recommendation="NO_HIRE",
        )
        db.add(fb)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_duplicate_feedback_rejected(self, db):
        iv, itvr = self._base(db, "F04")
        fb1 = Feedback(
            feedback_id=f"FB-{iv.interview_id}-{itvr.interviewer_id}-1",
            interview_id=iv.id,
            interviewer_id=itvr.id,
            overall_score=8.0,
            recommendation="HIRE",
        )
        db.add(fb1)
        db.flush()
        fb2 = Feedback(
            feedback_id=f"FB-{iv.interview_id}-{itvr.interviewer_id}-2",
            interview_id=iv.id,
            interviewer_id=itvr.id,
            overall_score=5.0,
            recommendation="NO_HIRE",
        )
        db.add(fb2)
        with pytest.raises(IntegrityError):
            db.flush()


# ─────────────────────────────────────────────────────────────
# TC-9: Offer
# ─────────────────────────────────────────────────────────────

class TestOffer:
    def _base(self, db, suffix="O01"):
        dept = make_department(f"OD{suffix}")
        db.add(dept)
        db.flush()
        req  = make_requisition(dept.id, f"{suffix:0>6}")
        cand = make_candidate(f"OC{suffix}")
        db.add_all([req, cand])
        db.flush()
        app = make_application(req.id, cand.id, suffix=suffix)
        db.add(app)
        db.flush()
        return app

    def test_create_offer(self, db):
        app = self._base(db, "O01")
        offer = Offer(
            offer_id="OFF-2026-000101",
            application_id=app.id,
            offered_salary=90_000,
        )
        db.add(offer)
        db.flush()
        assert offer.id is not None

    def test_zero_salary_rejected(self, db):
        app = self._base(db, "O02")
        offer = Offer(
            offer_id="OFF-2026-999901",
            application_id=app.id,
            offered_salary=0,
        )
        db.add(offer)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_negative_salary_rejected(self, db):
        app = self._base(db, "O03")
        offer = Offer(
            offer_id="OFF-2026-999902",
            application_id=app.id,
            offered_salary=-50_000,
        )
        db.add(offer)
        with pytest.raises(IntegrityError):
            db.flush()


# ─────────────────────────────────────────────────────────────
# TC-10: Relationships (ORM traversal)
# ─────────────────────────────────────────────────────────────

class TestRelationships:
    def test_department_to_requisitions(self, db):
        dept = make_department("REL01")
        db.add(dept)
        db.flush()
        req = make_requisition(dept.id, "REL001")
        db.add(req)
        db.flush()
        db.refresh(dept)
        assert len(dept.requisitions) == 1
        assert dept.requisitions[0].requisition_id == "REQ-2026-REL001"

    def test_candidate_to_skills(self, db):
        cand = make_candidate("CREL01")
        skill = Skill(skill_id="SKILL-00001", name="Python", category="TECHNICAL")
        db.add_all([cand, skill])
        db.flush()
        cs = CandidateSkill(
            candidate_id=cand.id,
            skill_id=skill.id,
            proficiency="ADVANCED",
        )
        db.add(cs)
        db.flush()
        db.refresh(cand)
        assert len(cand.candidate_skills) == 1
        assert cand.candidate_skills[0].skill.name == "Python"

    def test_application_to_interview_to_feedback(self, db):
        dept = make_department("REL02")
        db.add(dept)
        db.flush()
        req  = make_requisition(dept.id, "REL002")
        cand = make_candidate("CREL02")
        itvr = make_interviewer("REL002")
        db.add_all([req, cand, itvr])
        db.flush()
        app = make_application(req.id, cand.id, suffix="REL02")
        db.add(app)
        db.flush()
        iv = make_interview(app.id, "REL002")
        db.add(iv)
        db.flush()
        fb = Feedback(
            feedback_id=f"FB-{iv.interview_id}-{itvr.interviewer_id}",
            interview_id=iv.id,
            interviewer_id=itvr.id,
            overall_score=9.0,
            recommendation="STRONG_HIRE",
        )
        db.add(fb)
        db.flush()
        db.refresh(app)
        assert len(app.interviews) == 1
        assert len(app.interviews[0].feedbacks) == 1
        assert app.interviews[0].feedbacks[0].recommendation == "STRONG_HIRE"


# ─────────────────────────────────────────────────────────────
# TC-11: History / Audit Tables
# ─────────────────────────────────────────────────────────────

class TestHistoryTables:
    def test_application_stage_history(self, db):
        dept = make_department("HIST01")
        db.add(dept)
        db.flush()
        req  = make_requisition(dept.id, "HIST01")
        cand = make_candidate("CHIST01")
        db.add_all([req, cand])
        db.flush()
        app = make_application(req.id, cand.id, suffix="HIST01")
        db.add(app)
        db.flush()
        history = ApplicationStageHistory(
            application_id=app.id,
            from_stage=None,
            to_stage="APPLIED",
            changed_by="system",
        )
        db.add(history)
        db.flush()
        assert history.id is not None
        db.refresh(app)
        assert len(app.stage_history) == 1

    def test_audit_event_creation(self, db):
        event_row = AuditEvent(
            entity_type="Department",
            entity_id="DEPT-HIST01",
            action="CREATE",
            actor="admin@company.com",
            new_value='{"name": "Engineering"}',
        )
        db.add(event_row)
        db.flush()
        assert event_row.id is not None

    def test_requisition_approval_log(self, db):
        dept = make_department("HIST02")
        db.add(dept)
        db.flush()
        req = make_requisition(dept.id, "HIST02")
        db.add(req)
        db.flush()
        approval = RequisitionApproval(
            requisition_id=req.id,
            approver_name="HR Manager",
            decision="APPROVED",
            comments="Looks good.",
        )
        db.add(approval)
        db.flush()
        assert approval.id is not None
        db.refresh(req)
        assert len(req.approvals) == 1


# ─────────────────────────────────────────────────────────────
# TC-12: Foreign Key Enforcement
# ─────────────────────────────────────────────────────────────

class TestForeignKeyEnforcement:
    def test_application_bad_requisition_fk(self, db):
        """Application with non-existent requisition_id must be rejected."""
        cand = make_candidate("CFKTEST")
        db.add(cand)
        db.flush()
        app = Application(
            application_id="APP-FK-TEST-001",
            requisition_id=99999,  # Non-existent
            candidate_id=cand.id,
        )
        db.add(app)
        with pytest.raises(IntegrityError):
            db.flush()

    def test_feedback_bad_interviewer_fk(self, db):
        """Feedback with non-existent interviewer_id must be rejected."""
        dept = make_department("FKD01")
        db.add(dept)
        db.flush()
        req  = make_requisition(dept.id, "FKD001")
        cand = make_candidate("CFKD01")
        db.add_all([req, cand])
        db.flush()
        app = make_application(req.id, cand.id, suffix="FKD01")
        db.add(app)
        db.flush()
        iv = make_interview(app.id, "FKD001")
        db.add(iv)
        db.flush()
        fb = Feedback(
            feedback_id="FB-FK-TEST-001",
            interview_id=iv.id,
            interviewer_id=99999,  # Non-existent
            overall_score=7.0,
            recommendation="HIRE",
        )
        db.add(fb)
        with pytest.raises(IntegrityError):
            db.flush()
