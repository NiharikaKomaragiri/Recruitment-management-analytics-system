import csv
import json
from pathlib import Path
from datetime import timedelta

from config import GROUND_TRUTH_DIR
from src.database.database import SessionLocal

from src.database.models.application import Application
from src.database.models.candidate import Candidate
from src.database.models.interview import (
    Interview,
    InterviewPanelAssignment,
    Interviewer,
)
from src.database.models.feedback import Feedback
from src.database.models.offer import Offer
from src.database.models.requisition import JobRequisition


def generate_anomalies():

    db = SessionLocal()
    anomalies = []

    try:
        # -------------------------------------------------
        # 1. Interview assigned to unavailable interviewer
        # -------------------------------------------------
        assignment = db.query(InterviewPanelAssignment).order_by(InterviewPanelAssignment.id).first()

        if assignment:
            interview = db.query(Interview).filter_by(
                id=assignment.interview_id
            ).order_by(Interview.id).first()

            interviewer = db.query(Interviewer).filter_by(
                id=assignment.interviewer_id
            ).order_by(Interviewer.id).first()

            if interview and interviewer:
                anomalies.append({
                    "anomaly_id": "ANOM-001",
                    "anomaly_type": "INTERVIEWER_UNAVAILABLE",
                    "entity_type": "Interview",
                    "entity_id": interview.interview_id,
                    "related_entity_id": interviewer.interviewer_id,
                    "description": (
                        "Synthetic conflicting interview scheduled "
                        "for an interviewer already occupied."
                    ),
                    "expected_rule": (
                        "An interviewer cannot attend two interviews "
                        "at overlapping times."
                    ),
                    "observed_value": (
                        f"Proposed conflicting slot: "
                        f"{interview.scheduled_start} to "
                        f"{interview.scheduled_end}"
                    ),
                    "is_anomaly": True,
                })

        # -------------------------------------------------
        # 2. Duplicate candidate application
        # -------------------------------------------------
        application = db.query(Application).order_by(Application.id).first()

        if application:
            candidate = db.query(Candidate).filter_by(
                id=application.candidate_id
            ).order_by(Candidate.id).first()

            if candidate:
                anomalies.append({
                    "anomaly_id": "ANOM-002",
                    "anomaly_type": "DUPLICATE_APPLICATION",
                    "entity_type": "Application",
                    "entity_id": application.application_id,
                    "related_entity_id": candidate.candidate_id,
                    "description": (
                        "Synthetic second application created for "
                        "the same candidate and requisition."
                    ),
                    "expected_rule": (
                        "A candidate should not apply twice "
                        "to the same requisition."
                    ),
                    "observed_value": (
                        f"Duplicate of {application.application_id}"
                    ),
                    "is_anomaly": True,
                })

        # -------------------------------------------------
        # 3. Missing feedback despite stage advancement
        # -------------------------------------------------
        interview_without_feedback = (
            db.query(Interview)
            .outerjoin(
                Feedback,
                Feedback.interview_id == Interview.id
            )
            .filter(
                Feedback.id.is_(None),
                Interview.status == "COMPLETED"
            )
            .order_by(Interview.id)
            .first()
        )

        if interview_without_feedback:
            anomalies.append({
                "anomaly_id": "ANOM-003",
                "anomaly_type": "MISSING_FEEDBACK",
                "entity_type": "Interview",
                "entity_id": interview_without_feedback.interview_id,
                "related_entity_id": None,
                "description": (
                    "Completed interview has no submitted feedback."
                ),
                "expected_rule": (
                    "Feedback must be recorded before a candidate "
                    "advances after an interview."
                ),
                "observed_value": "No feedback record found",
                "is_anomaly": True,
            })
        else:
            # Keep a separately labelled synthetic case.
            advanced_app = (
                db.query(Application)
                .filter(Application.current_stage == "INTERVIEW")
                .order_by(Application.id)
                .first()
            )

            if advanced_app:
                anomalies.append({
                    "anomaly_id": "ANOM-003",
                    "anomaly_type": "MISSING_FEEDBACK",
                    "entity_type": "Application",
                    "entity_id": advanced_app.application_id,
                    "related_entity_id": None,
                    "description": (
                        "Synthetic case: application advanced "
                        "without required interview feedback."
                    ),
                    "expected_rule": (
                        "Feedback must be recorded before advancement."
                    ),
                    "observed_value": "Synthetic missing feedback case",
                    "is_anomaly": True,
                })

        # -------------------------------------------------
        # 4. Offer salary outside approved salary band
        # -------------------------------------------------
        offer = db.query(Offer).order_by(Offer.id).first()

        if offer:
            application_for_offer = db.query(Application).filter_by(
                id=offer.application_id
            ).order_by(Application.id).first()

            requisition = None

            if application_for_offer:
                requisition = db.query(JobRequisition).filter_by(
                    id=application_for_offer.requisition_id
                ).order_by(JobRequisition.id).first()

            if requisition and requisition.maximum_salary is not None:
                invalid_salary = round(
                    requisition.maximum_salary * 1.25, 2
                )

                anomalies.append({
                    "anomaly_id": "ANOM-004",
                    "anomaly_type": "SALARY_OUTSIDE_APPROVED_BAND",
                    "entity_type": "Offer",
                    "entity_id": offer.offer_id,
                    "related_entity_id": requisition.requisition_id,
                    "description": (
                        "Synthetic offer salary exceeds the approved "
                        "requisition salary range."
                    ),
                    "expected_rule": (
                        "Offered salary must remain within the "
                        "approved minimum and maximum salary."
                    ),
                    "observed_value": (
                        f"Proposed salary: {invalid_salary}; "
                        f"maximum allowed: {requisition.maximum_salary}"
                    ),
                    "is_anomaly": True,
                })

        # -------------------------------------------------
        # 5. Closed requisition with active applications
        # -------------------------------------------------
        closed_requisition = (
            db.query(JobRequisition)
            .filter(JobRequisition.status == "CLOSED")
            .order_by(JobRequisition.id)
            .first()
        )

        if closed_requisition:
            active_application = (
                db.query(Application)
                .filter(
                    Application.requisition_id == closed_requisition.id,
                    Application.status == "ACTIVE",
                )
                .order_by(Application.id)
                .first()
            )

            if active_application:
                application_id = active_application.application_id
            else:
                application_id = "SYN-ACTIVE-APP-001"

            anomalies.append({
                "anomaly_id": "ANOM-005",
                "anomaly_type": "CLOSED_REQUISITION_ACTIVE_APPLICATION",
                "entity_type": "JobRequisition",
                "entity_id": closed_requisition.requisition_id,
                "related_entity_id": application_id,
                "description": (
                    "Synthetic active application associated with "
                    "a closed requisition."
                ),
                "expected_rule": (
                    "A closed requisition must not have active applications."
                ),
                "observed_value": (
                    f"Requisition status: CLOSED; "
                    f"application reference: {application_id}"
                ),
                "is_anomaly": True,
            })

        # -------------------------------------------------
        # Export labelled anomaly cases
        # -------------------------------------------------
        GROUND_TRUTH_DIR.mkdir(parents=True, exist_ok=True)

        csv_path = GROUND_TRUTH_DIR / "anomaly_cases.csv"
        json_path = GROUND_TRUTH_DIR / "anomaly_cases.json"

        if anomalies:
            with open(csv_path, "w", newline="", encoding="utf-8") as file:
                writer = csv.DictWriter(
                    file,
                    fieldnames=anomalies[0].keys()
                )
                writer.writeheader()
                writer.writerows(anomalies)

        with open(json_path, "w", encoding="utf-8") as file:
            json.dump(anomalies, file, indent=4, default=str)

        print("\nANOMALY GENERATION SUMMARY")
        print("-" * 40)

        for anomaly in anomalies:
            print(
                anomaly["anomaly_id"],
                anomaly["anomaly_type"]
            )

        print("-" * 40)
        print("Total labelled anomalies:", len(anomalies))
        print("CSV:", csv_path)
        print("JSON:", json_path)

        if len(anomalies) != 5:
            print(
                "WARNING: Not all five anomaly cases were generated. "
                "Check the database for missing source records."
            )

        return anomalies

    finally:
        db.close()


if __name__ == "__main__":
    generate_anomalies()