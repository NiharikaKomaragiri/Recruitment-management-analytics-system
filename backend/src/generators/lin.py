"""
Main data pipeline for Recruitment Management & Analytics System.

Run:
    python -m src.generators.lin

This script regenerates the synthetic database records.
"""

import sys
from pathlib import Path
from datetime import datetime
import pandas as pd

from config import DATASET_SCALE, RAW_DATA_DIR

from src.database.database import Base, engine, SessionLocal
import src.database.models

from src.database.models.department import Department
from src.database.models.skill import Skill, CandidateSkill
from src.database.models.candidate import Candidate, ResumeArtifact
from src.database.models.requisition import (
    JobRequisition,
    RequisitionApproval,
    ScreeningRule,
    RequisitionRequiredSkill,
)
from src.database.models.interview import (
    Interviewer,
    Interview,
    InterviewPanelAssignment,
)
from src.database.models.application import (
    Application,
    ApplicationStageHistory,
)
from src.database.models.feedback import Feedback
from src.database.models.offer import Offer

from src.generators.requisition_generator import RequisitionGenerator
from src.generators.application_generator import ApplicationGenerator
from src.generators.interview_generator import InterviewGenerator
from src.generators.feedback_generator import FeedbackGenerator
from src.generators.offer_generator import OfferGenerator


def read_csv(filename):
    path = RAW_DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    return pd.read_csv(path).fillna(value=pd.NA).to_dict("records")


def value(record, *names, default=None):
    """Read a value using alternative CSV column names."""
    for name in names:
        if name in record:
            result = record[name]
            if result is not None and not pd.isna(result):
                return result
    return default


def clean_date(value):
    if value is None or pd.isna(value):
        return None

    if isinstance(value, datetime):
        return value

    return pd.to_datetime(value).to_pydatetime()


def clean_enum(value):
    if hasattr(value, "value"):
        return value.value
    return str(value)


def reset_database():
    print("\n[1/8] Creating database tables...")

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Database tables ready.")


def load_master_data(db):
    print("\n[2/8] Loading master data...")

    departments_data = read_csv("departments.csv")
    skills_data = read_csv("skills.csv")
    interviewers_data = read_csv("interviewers.csv")

    department_map = {}
    skill_map = {}
    interviewer_map = {}

    for row in departments_data:
        business_id = row["department_id"]

        obj = Department(
            department_id=business_id,
            name=value(row, "name", "department_name"),
            description=value(row, "description"),
            cost_centre=value(row, "cost_centre"),
            location=value(row, "location"),
            head_of_department=value(row, "head_of_department"),
            is_active=True,
        )

        db.add(obj)
        db.flush()

        department_map[business_id] = obj.id

    for row in skills_data:
        business_id = row["skill_id"]

        category = str(value(row, "category", default="OTHER")).upper()

        if category == "PROFESSIONAL":
            category = "SOFT"

        allowed = {
            "TECHNICAL", "SOFT", "DOMAIN",
            "LANGUAGE", "TOOL", "OTHER"
        }

        if category not in allowed:
            category = "OTHER"

        obj = Skill(
            skill_id=business_id,
            name=value(row, "name", "skill_name"),
            category=category,
            description=value(row, "description"),
            is_active=True,
        )

        db.add(obj)
        db.flush()

        skill_map[business_id] = obj.id

    for row in interviewers_data:
        business_id = row["interviewer_id"]

        obj = Interviewer(
            interviewer_id=business_id,
            employee_id=business_id,
            full_name=value(
                row, "full_name", "interviewer_name"
            ),
            email=row["email"],
            department=value(
                row, "department", "department_id"
            ),
            job_title=value(
                row, "job_title", "designation"
            ),
            specialisation=value(row, "specialisation"),
            max_interviews_per_week=5,
            is_active=True,
        )

        db.add(obj)
        db.flush()

        interviewer_map[business_id] = obj.id

    db.commit()

    print("Departments:", len(department_map))
    print("Skills:", len(skill_map))
    print("Interviewers:", len(interviewer_map))

    return department_map, skill_map, interviewer_map


def load_candidates(db, skill_map):
    print("\n[3/8] Loading candidates and resumes...")

    candidates_data = read_csv("candidates.csv")
    skills_data = read_csv("candidate_skills.csv")
    resumes_data = read_csv("resume_artifacts.csv")

    candidate_map = {}
    resume_map = {}

    for row in candidates_data:
        business_id = row["candidate_id"]

        obj = Candidate(
            candidate_id=business_id,
            full_name=row["full_name"],
            email=row["email"],
            phone=value(row, "phone"),
            education=clean_enum(row["education"]),
            field_of_study=value(row, "field_of_study"),
            institution=value(row, "institution"),
            graduation_year=value(row, "graduation_year"),
            experience_years=float(
                value(row, "experience_years", default=0)
            ),
            current_title=value(row, "current_title"),
            current_company=value(row, "current_company"),
            linkedin_url=value(row, "linkedin_url"),
            portfolio_url=value(row, "portfolio_url"),
            summary=value(row, "summary"),
            status=clean_enum(value(row, "status", default="ACTIVE")),
        )

        db.add(obj)
        db.flush()

        candidate_map[business_id] = obj.id

    for row in resumes_data:
        candidate_business_id = row["candidate_id"]

        obj = ResumeArtifact(
            resume_id=row["resume_id"],
            candidate_id=candidate_map[candidate_business_id],
            version=int(row["version"]),
            file_name=row["file_name"],
            file_path=row["file_path"],
            file_size_kb=value(row, "file_size_kb"),
            file_format=value(row, "file_format"),
            is_latest=bool(row["is_latest"]),
            parse_status=value(row, "parse_status"),
            parsed_text=value(row, "parsed_text"),
        )

        db.add(obj)
        db.flush()

        resume_map[row["resume_id"]] = obj.id

    for row in skills_data:
        candidate_id = candidate_map[row["candidate_id"]]
        skill_id = skill_map[row["skill_id"]]

        db.add(
            CandidateSkill(
                candidate_id=candidate_id,
                skill_id=skill_id,
                proficiency=clean_enum(row["proficiency"]),
                years_of_experience=value(
                    row, "years_of_experience"
                ),
                is_primary=bool(row["is_primary"]),
            )
        )

    db.commit()

    print("Candidates:", len(candidate_map))
    print("Resume records:", len(resume_map))
    print("Candidate skills:", len(skills_data))

    return candidate_map, resume_map


def load_requisitions(db, department_map, skill_map):
    print("\n[4/8] Generating and loading requisitions...")

    departments = read_csv("departments.csv")
    skills = read_csv("skills.csv")

    generated = RequisitionGenerator().generate(
        departments,
        skills,
        DATASET_SCALE,
    )

    requisition_map = {}

    for row in generated["requisitions"]:

        obj = JobRequisition(
            requisition_id=row["requisition_id"],
            department_id=department_map[
                row["department_business_id"]
            ],
            job_title=row["job_title"],
            job_description=row["job_description"],
            location=row["location"],
            employment_type=row["employment_type"],
            openings=row["openings"],
            minimum_salary=row["minimum_salary"],
            maximum_salary=row["maximum_salary"],
            currency=row["currency"],
            experience_required=row["experience_required"],
            remote_allowed=row["remote_allowed"],
            status=row["status"],
            created_at=clean_date(row["created_at"]),
            approved_at=clean_date(row["approved_at"]),
            closed_at=clean_date(row["closed_at"]),
        )

        db.add(obj)
        db.flush()

        requisition_map[row["requisition_id"]] = obj.id

    for row in generated["req_approvals"]:
        db.add(
            RequisitionApproval(
                requisition_id=requisition_map[
                    row["requisition_business_id"]
                ],
                approver_name=row["approver_name"],
                approver_role=row["approver_role"],
                decision=row["decision"],
                comments=row["comments"],
                decided_at=clean_date(row["decided_at"]),
            )
        )

    for row in generated["screening_rules"]:
        db.add(
            ScreeningRule(
                rule_id=row["rule_id"],
                requisition_id=requisition_map[
                    row["requisition_business_id"]
                ],
                rule_type=row["rule_type"],
                rule_value=row["rule_value"],
                weight=row["weight"],
                is_knockout=row["is_knockout"],
                is_active=row["is_active"],
                description=row["description"],
            )
        )

    for row in generated["req_required_skills"]:
        db.add(
            RequisitionRequiredSkill(
                requisition_id=requisition_map[
                    row["requisition_business_id"]
                ],
                skill_id=skill_map[
                    row["skill_business_id"]
                ],
                minimum_proficiency=row["minimum_proficiency"],
                is_mandatory=row["is_mandatory"],
            )
        )

    db.commit()

    print("Requisitions:", len(requisition_map))
    print("Approvals:", len(generated["req_approvals"]))
    print("Screening rules:", len(generated["screening_rules"]))
    print("Required skills:", len(generated["req_required_skills"]))

    return generated, requisition_map


def load_applications(
    db,
    candidate_map,
    resume_map,
    requisition_data,
    requisition_map,
):
    print("\n[5/8] Generating and loading applications...")

    candidates = read_csv("candidates.csv")
    resumes = read_csv("resume_artifacts.csv")

    generated = ApplicationGenerator().generate(
        candidates,
        requisition_data["requisitions"],
        resumes,
        DATASET_SCALE,
    )

    application_map = {}

    for row in generated["applications"]:

        obj = Application(
            application_id=row["application_id"],
            requisition_id=requisition_map[
                row["requisition_business_id"]
            ],
            candidate_id=candidate_map[
                row["candidate_business_id"]
            ],
            resume_id=resume_map.get(
                row["resume_business_id"]
            ),
            screening_score=row["screening_score"],
            current_stage=row["current_stage"],
            status=row["status"],
            rejection_reason=row["rejection_reason"],
            recruiter_notes=row["recruiter_notes"],
            applied_at=clean_date(row["applied_at"]),
        )

        db.add(obj)
        db.flush()

        application_map[row["application_id"]] = obj.id

    for row in generated["stage_history"]:
        db.add(
            ApplicationStageHistory(
                application_id=application_map[
                    row["application_business_id"]
                ],
                from_stage=row["from_stage"],
                to_stage=row["to_stage"],
                changed_by=row["changed_by"],
                reason=row["reason"],
                transitioned_at=clean_date(
                    row["transitioned_at"]
                ),
            )
        )

    db.commit()

    print("Applications:", len(application_map))
    print("Stage history:", len(generated["stage_history"]))

    return generated, application_map


def load_interviews(db, application_data, application_map, interviewer_map):
    print("\n[6/8] Generating and loading interviews...")

    interviewer_rows = read_csv("interviewers.csv")

    generated = InterviewGenerator().generate(
        application_data["applications"],
        interviewer_rows,
        DATASET_SCALE,
    )

    interview_map = {}

    for row in generated["interviews"]:

        obj = Interview(
            interview_id=row["interview_id"],
            application_id=application_map[
                row["application_business_id"]
            ],
            round_number=row["round_number"],
            round_name=row["round_name"],
            scheduled_start=clean_date(row["scheduled_start"]),
            scheduled_end=clean_date(row["scheduled_end"]),
            mode=row["mode"],
            location_or_meeting_link=row[
                "location_or_meeting_link"
            ],
            status=row["status"],
        )

        db.add(obj)
        db.flush()

        interview_map[row["interview_id"]] = obj.id

    for row in generated["panel_assignments"]:
        db.add(
            InterviewPanelAssignment(
                interview_id=interview_map[
                    row["interview_business_id"]
                ],
                interviewer_id=interviewer_map[
                    row["interviewer_business_id"]
                ],
                role=row["role"],
                confirmed=row["confirmed"],
            )
        )

    db.commit()

    print("Interviews:", len(interview_map))
    print("Panel assignments:", len(generated["panel_assignments"]))

    return generated, interview_map


def load_feedback(db, interview_data, interview_map, interviewer_map):
    print("\n[7/8] Generating and loading feedback...")

    generated = FeedbackGenerator().generate(
        interview_data["interviews"],
        interview_data["panel_assignments"],
    )

    for row in generated["feedback"]:
        db.add(
            Feedback(
                feedback_id=row["feedback_id"],
                interview_id=interview_map[
                    row["interview_business_id"]
                ],
                interviewer_id=interviewer_map[
                    row["interviewer_business_id"]
                ],
                technical_score=row["technical_score"],
                communication_score=row["communication_score"],
                problem_solving_score=row["problem_solving_score"],
                cultural_fit_score=row["cultural_fit_score"],
                overall_score=row["overall_score"],
                recommendation=row["recommendation"],
                strengths=row["strengths"],
                areas_for_improvement=row["areas_for_improvement"],
                comments=row["comments"],
            )
        )

    db.commit()

    print("Feedback records:", len(generated["feedback"]))

    return generated


def load_offers(
    db,
    application_data,
    requisition_data,
    interview_data,
    feedback_data,
    application_map,
):
    print("\n[8/8] Generating and loading offers...")

    generated = OfferGenerator().generate(
        application_data["applications"],
        requisition_data["requisitions"],
        interview_data["interviews"],
        feedback_data["feedback"],
        DATASET_SCALE,
    )

    for row in generated["offers"]:
        db.add(
            Offer(
                offer_id=row["offer_id"],
                application_id=application_map[
                    row["application_business_id"]
                ],
                offered_salary=row["offered_salary"],
                currency=row["currency"],
                signing_bonus=row["signing_bonus"],
                equity_details=row["equity_details"],
                benefits_summary=row["benefits_summary"],
                start_date=row["start_date"],
                expiry_date=row["expiry_date"],
                offer_letter_path=row["offer_letter_path"],
                status=row["status"],
                rejection_reason=row["rejection_reason"],
                negotiation_notes=row["negotiation_notes"],
                created_at=clean_date(row["created_at"]),
                approved_at=clean_date(row["approved_at"]),
                extended_at=clean_date(row["extended_at"]),
                accepted_at=clean_date(row["accepted_at"]),
                rejected_at=clean_date(row["rejected_at"]),
            )
        )

    db.commit()

    print("Offers:", len(generated["offers"]))


def print_summary(db):
    print("\n" + "=" * 50)
    print("DATABASE GENERATION SUMMARY")
    print("=" * 50)

    models = [
        Department,
        Skill,
        Interviewer,
        Candidate,
        CandidateSkill,
        ResumeArtifact,
        JobRequisition,
        RequisitionApproval,
        ScreeningRule,
        RequisitionRequiredSkill,
        Application,
        ApplicationStageHistory,
        Interview,
        InterviewPanelAssignment,
        Feedback,
        Offer,
    ]

    for model in models:
        count = db.query(model).count()
        print(f"{model.__tablename__:<35} {count:>8}")

    print("=" * 50)
    print("PIPELINE COMPLETED")
    print("=" * 50)


def main():
    print("=" * 55)
    print("RECRUITMENT MANAGEMENT & ANALYTICS SYSTEM")
    print("SCALE:", DATASET_SCALE.upper())
    print("=" * 55)

    reset_database()

    db = SessionLocal()

    try:
        department_map, skill_map, interviewer_map = load_master_data(db)

        candidate_map, resume_map = load_candidates(
            db, skill_map
        )

        requisition_data, requisition_map = load_requisitions(
            db, department_map, skill_map
        )

        application_data, application_map = load_applications(
            db,
            candidate_map,
            resume_map,
            requisition_data,
            requisition_map,
        )

        interview_data, interview_map = load_interviews(
            db,
            application_data,
            application_map,
            interviewer_map,
        )

        feedback_data = load_feedback(
            db,
            interview_data,
            interview_map,
            interviewer_map,
        )

        load_offers(
            db,
            application_data,
            requisition_data,
            interview_data,
            feedback_data,
            application_map,
        )

        print_summary(db)

    except Exception as error:
        db.rollback()
        print("\nPIPELINE FAILED!")
        print(type(error).__name__ + ":", error)
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()