from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.database.database import get_db
from src.database.models import (
    Candidate,
    JobRequisition,
    Application,
    ApplicationStageHistory,
    Interview,
    InterviewPanelAssignment,
    Interviewer,
    Offer,
    ResumeArtifact,
)

from src.database.models.application import (
    ApplicationStage,
    ApplicationStatus,
)
from src.database.models.requisition import RequisitionStatus


# ---------------------------------------------------------
# FASTAPI APPLICATION
# ---------------------------------------------------------

app = FastAPI(
    title="Recruitment Management & Analytics System",
    description=(
        "REST API for managing candidates, job requisitions, "
        "applications, interviews, and recruitment offers."
    ),
    version="1.0.0",
)


# ---------------------------------------------------------
# REQUEST SCHEMA
# ---------------------------------------------------------

class ApplicationRequest(BaseModel):
    candidate_id: str = Field(
        ...,
        description="Candidate business ID, e.g. CAND-000001"
    )

    requisition_id: str = Field(
        ...,
        description="Requisition business ID"
    )

    resume_id: Optional[str] = Field(
        default=None,
        description="Optional resume business ID"
    )


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def candidate_response(candidate):
    return {
        "candidate_id": candidate.candidate_id,
        "full_name": candidate.full_name,
        "email": candidate.email,
        "phone": candidate.phone,
        "education": candidate.education,
        "field_of_study": candidate.field_of_study,
        "institution": candidate.institution,
        "graduation_year": candidate.graduation_year,
        "experience_years": candidate.experience_years,
        "current_title": candidate.current_title,
        "current_company": candidate.current_company,
        "status": candidate.status,
    }


def requisition_response(req):
    return {
        "requisition_id": req.requisition_id,
        "job_title": req.job_title,
        "job_description": req.job_description,
        "location": req.location,
        "employment_type": req.employment_type,
        "openings": req.openings,
        "minimum_salary": req.minimum_salary,
        "maximum_salary": req.maximum_salary,
        "currency": req.currency,
        "experience_required": req.experience_required,
        "remote_allowed": req.remote_allowed,
        "status": req.status,
    }


# ---------------------------------------------------------
# ROOT ENDPOINT
# ---------------------------------------------------------

@app.get("/")
def home():
    return {
        "message": "Recruitment Management API is running",
        "documentation": "/docs",
        "version": "1.0.0",
    }


# ---------------------------------------------------------
# 1. VIEW ALL CANDIDATES
# ---------------------------------------------------------

@app.get("/api/v1/candidates")
def get_candidates(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):

    candidates = (
        db.query(Candidate)
        .order_by(Candidate.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    total = db.query(Candidate).count()

    return {
        "total": total,
        "count": len(candidates),
        "candidates": [
            candidate_response(candidate)
            for candidate in candidates
        ],
    }


# ---------------------------------------------------------
# 2. VIEW SINGLE CANDIDATE
# ---------------------------------------------------------

@app.get("/api/v1/candidates/{candidate_id}")
def get_candidate(
    candidate_id: str,
    db: Session = Depends(get_db),
):

    candidate = (
        db.query(Candidate)
        .filter(Candidate.candidate_id == candidate_id)
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    return candidate_response(candidate)


# ---------------------------------------------------------
# 3. VIEW ALL JOB REQUISITIONS
# ---------------------------------------------------------

@app.get("/api/v1/requisitions")
def get_requisitions(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):

    query = db.query(JobRequisition)

    if status:
        allowed_statuses = {
            item.value for item in RequisitionStatus
        }

        if status.upper() not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail="Invalid requisition status"
            )

        query = query.filter(
            JobRequisition.status == status.upper()
        )

    total = query.count()

    requisitions = (
        query.order_by(JobRequisition.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return {
        "total": total,
        "count": len(requisitions),
        "requisitions": [
            requisition_response(req)
            for req in requisitions
        ],
    }


# ---------------------------------------------------------
# 4. SUBMIT AN APPLICATION
# ---------------------------------------------------------

@app.post("/api/v1/applications", status_code=201)
def submit_application(
    request: ApplicationRequest,
    db: Session = Depends(get_db),
):

    candidate = (
        db.query(Candidate)
        .filter(
            Candidate.candidate_id == request.candidate_id
        )
        .first()
    )

    if not candidate:
        raise HTTPException(
            status_code=404,
            detail="Candidate not found"
        )

    requisition = (
        db.query(JobRequisition)
        .filter(
            JobRequisition.requisition_id == request.requisition_id
        )
        .first()
    )

    if not requisition:
        raise HTTPException(
            status_code=404,
            detail="Job requisition not found"
        )

    if requisition.status != RequisitionStatus.APPROVED:
        raise HTTPException(
            status_code=400,
            detail="Applications are accepted only for approved requisitions"
        )

    resume = None

    if request.resume_id:
        resume = (
            db.query(ResumeArtifact)
            .filter(
                ResumeArtifact.resume_id == request.resume_id,
                ResumeArtifact.candidate_id == candidate.id,
            )
            .first()
        )

        if not resume:
            raise HTTPException(
                status_code=404,
                detail="Resume not found for this candidate"
            )
    else:
        resume = (
            db.query(ResumeArtifact)
            .filter(
                ResumeArtifact.candidate_id == candidate.id,
                ResumeArtifact.is_latest.is_(True),
            )
            .first()
        )

    existing_application = (
        db.query(Application)
        .filter(
            Application.candidate_id == candidate.id,
            Application.requisition_id == requisition.id,
        )
        .first()
    )

    if existing_application:
        raise HTTPException(
            status_code=409,
            detail="Candidate has already applied for this requisition"
        )

    application_id = (
        f"APP-{requisition.requisition_id}-{candidate.candidate_id}"
    )

    application = Application(
        application_id=application_id,
        candidate_id=candidate.id,
        requisition_id=requisition.id,
        resume_id=resume.id if resume else None,
        current_stage=ApplicationStage.APPLIED,
        status=ApplicationStatus.ACTIVE,
    )

    try:
        db.add(application)
        db.flush()

        # Record the initial application stage in history.
        history = ApplicationStageHistory(
            application_id=application.id,
            from_stage=None,
            to_stage=ApplicationStage.APPLIED,
            changed_by="API",
            notes="Application submitted through REST API",
        )

        db.add(history)
        db.commit()
        db.refresh(application)

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Application already exists or violates a database constraint"
        )

    return {
        "message": "Application submitted successfully",
        "application_id": application.application_id,
        "candidate_id": candidate.candidate_id,
        "requisition_id": requisition.requisition_id,
        "current_stage": application.current_stage,
        "status": application.status,
    }


# ---------------------------------------------------------
# 5. RETRIEVE APPLICATIONS
# ---------------------------------------------------------

@app.get("/api/v1/applications")
def get_applications(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):

    query = db.query(Application)

    total = query.count()

    applications = (
        query.order_by(Application.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []

    for application in applications:
        result.append({
            "application_id": application.application_id,
            "candidate_id": application.candidate.candidate_id,
            "candidate_name": application.candidate.full_name,
            "requisition_id": application.requisition.requisition_id,
            "job_title": application.requisition.job_title,
            "screening_score": application.screening_score,
            "current_stage": application.current_stage,
            "status": application.status,
            "applied_at": application.applied_at,
        })

    return {
        "total": total,
        "count": len(result),
        "applications": result,
    }


# ---------------------------------------------------------
# 6. VIEW INTERVIEW SCHEDULES
# ---------------------------------------------------------

@app.get("/api/v1/interviews")
def get_interviews(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):

    query = db.query(Interview)

    if status:
        query = query.filter(
            Interview.status == status.upper()
        )

    total = query.count()

    interviews = (
        query.order_by(Interview.scheduled_start)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []

    for interview in interviews:

        application = interview.application

        panel = []

        for assignment in interview.panel_assignments:
            panel.append({
                "interviewer_id": assignment.interviewer.interviewer_id,
                "name": assignment.interviewer.full_name,
                "role": assignment.role,
                "confirmed": assignment.confirmed,
            })

        result.append({
            "interview_id": interview.interview_id,
            "application_id": application.application_id,
            "candidate_name": application.candidate.full_name,
            "job_title": application.requisition.job_title,
            "round_name": interview.round_name,
            "scheduled_start": interview.scheduled_start,
            "scheduled_end": interview.scheduled_end,
            "mode": interview.mode,
            "location_or_meeting_link": interview.location_or_meeting_link,
            "status": interview.status,
            "panel": panel,
        })

    return {
        "total": total,
        "count": len(result),
        "interviews": result,
    }


# ---------------------------------------------------------
# 7. RETRIEVE OFFERS
# ---------------------------------------------------------

@app.get("/api/v1/offers")
def get_offers(
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):

    query = db.query(Offer)

    if status:
        query = query.filter(
            Offer.status == status.upper()
        )

    total = query.count()

    offers = (
        query.order_by(Offer.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []

    for offer in offers:

        application = offer.application

        result.append({
            "offer_id": offer.offer_id,
            "application_id": application.application_id,
            "candidate_id": application.candidate.candidate_id,
            "candidate_name": application.candidate.full_name,
            "job_title": application.requisition.job_title,
            "offered_salary": offer.offered_salary,
            "currency": offer.currency,
            "signing_bonus": offer.signing_bonus,
            "start_date": offer.start_date,
            "expiry_date": offer.expiry_date,
            "status": offer.status,
            "created_at": offer.created_at,
        })

    return {
        "total": total,
        "count": len(result),
        "offers": result,
    }


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Recruitment Management API",
    }