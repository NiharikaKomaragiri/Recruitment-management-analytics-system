import random
from datetime import datetime, timedelta, date

from config import RANDOM_SEED, SCALE_CONFIG


OFFER_STATUSES = [
    "PENDING_APPROVAL",
    "APPROVED",
    "EXTENDED",
    "ACCEPTED",
    "REJECTED",
    "WITHDRAWN",
    "EXPIRED",
    "NEGOTIATING",
]

OFFER_WEIGHTS = [0.10, 0.10, 0.25, 0.30, 0.10, 0.05, 0.05, 0.05]


class OfferGenerator:

    def generate(
        self,
        applications,
        requisitions,
        interviews,
        feedback,
        scale="medium",
    ):

        if scale not in SCALE_CONFIG:
            raise ValueError(f"Invalid scale: {scale}")

        rng = random.Random(RANDOM_SEED)

        target = SCALE_CONFIG[scale]["num_offers"]

        requisition_map = {
            r["requisition_id"]: r for r in requisitions
        }

        # Only completed interviews can lead to an offer.
        completed_interviews = {
            i["interview_id"]: i
            for i in interviews
            if i["status"] == "COMPLETED"
        }

        feedback_by_interview = {}

        for item in feedback:
            feedback_by_interview.setdefault(
                item["interview_business_id"], []
            ).append(item)

        eligible_application_ids = set()

        for interview_id, interview in completed_interviews.items():
            records = feedback_by_interview.get(interview_id, [])

            if records:
                eligible_application_ids.add(
                    interview["application_business_id"]
                )

        eligible = [
            app for app in applications
            if app["application_id"] in eligible_application_ids
            and app["status"] == "ACTIVE"
            and app["requisition_business_id"] in requisition_map
        ]

        if len(eligible) < target:
            raise ValueError(
                f"Only {len(eligible)} eligible applications found; "
                f"{target} offers required."
            )

        # Rank candidates by their average interview feedback.
        application_scores = {}

        for interview_id, interview in completed_interviews.items():
            app_id = interview["application_business_id"]
            records = feedback_by_interview.get(interview_id, [])

            if records:
                average = sum(
                    item["overall_score"] for item in records
                ) / len(records)

                application_scores.setdefault(app_id, []).append(average)

        eligible.sort(
            key=lambda app: (
                sum(application_scores.get(app["application_id"], [0]))
                / max(len(application_scores.get(app["application_id"], [])), 1)
            ),
            reverse=True,
        )

        selected = eligible[:target]

        offers = []

        for number, app in enumerate(selected, start=1):

            requisition = requisition_map[
                app["requisition_business_id"]
            ]

            minimum = requisition["minimum_salary"]
            maximum = requisition["maximum_salary"]

            if minimum is None or maximum is None:
                raise ValueError(
                    f"Salary band missing for {requisition['requisition_id']}"
                )

            salary = round(
                rng.uniform(minimum, maximum), 2
            )

            status = rng.choices(
                OFFER_STATUSES,
                weights=OFFER_WEIGHTS,
                k=1,
            )[0]

            created_at = datetime(2026, 6, 1) + timedelta(
                days=rng.randint(0, 120)
            )

            approved_at = None
            extended_at = None
            accepted_at = None
            rejected_at = None

            if status != "PENDING_APPROVAL":
                approved_at = created_at + timedelta(days=1)

            if status in (
                "EXTENDED", "ACCEPTED", "REJECTED",
                "WITHDRAWN", "EXPIRED", "NEGOTIATING"
            ):
                extended_at = approved_at + timedelta(days=1)

            if status == "ACCEPTED":
                accepted_at = extended_at + timedelta(days=2)

            if status == "REJECTED":
                rejected_at = extended_at + timedelta(days=2)

            expiry_date = (
                (extended_at.date() + timedelta(days=14))
                if extended_at else None
            )

            start_date = (
                (extended_at.date() + timedelta(days=30))
                if extended_at else None
            )

            offers.append({
                "offer_id": f"OFF-2026-{number:06d}",
                "application_business_id": app["application_id"],
                "offered_salary": salary,
                "currency": requisition.get("currency", "INR"),
                "signing_bonus": (
                    round(salary * 0.05, 2)
                    if rng.random() < 0.15 else None
                ),
                "equity_details": None,
                "benefits_summary": (
                    "Health insurance, paid leave and learning allowance"
                ),
                "start_date": start_date,
                "expiry_date": expiry_date,
                "offer_letter_path": None,
                "status": status,
                "rejection_reason": (
                    "Candidate declined the offer"
                    if status == "REJECTED" else None
                ),
                "negotiation_notes": (
                    "Compensation discussion in progress"
                    if status == "NEGOTIATING" else None
                ),
                "created_at": created_at,
                "approved_at": approved_at,
                "extended_at": extended_at,
                "accepted_at": accepted_at,
                "rejected_at": rejected_at,
            })

        return {"offers": offers}