import random
from datetime import timedelta

from config import RANDOM_SEED, SCALE_CONFIG


STAGES = [
    "APPLIED",
    "SCREENING",
    "SHORTLISTED",
    "INTERVIEW",
    "ASSESSMENT",
    "OFFER",
    "REJECTED",
    "WITHDRAWN",
    "ON_HOLD",
]

STAGE_WEIGHTS = [0.10, 0.12, 0.18, 0.18, 0.10, 0.05, 0.15, 0.07, 0.05]


class ApplicationGenerator:

    def generate(self, candidates, requisitions, resumes, scale="medium"):

        if scale not in SCALE_CONFIG:
            raise ValueError(f"Invalid scale: {scale}")

        rng = random.Random(RANDOM_SEED)

        target_count = SCALE_CONFIG[scale]["num_applications"]

        eligible_requisitions = [
            r for r in requisitions
            if r["status"] == "APPROVED"
        ]

        if not eligible_requisitions:
            raise ValueError("No approved requisitions available.")

        if len(candidates) == 0 or len(resumes) == 0:
            raise ValueError("Candidate or resume data is empty.")

        candidates_by_id = {
            c["candidate_id"]: c for c in candidates
        }

        resumes_by_candidate = {}

        for resume in resumes:
            resumes_by_candidate.setdefault(
                resume["candidate_id"], []
            ).append(resume)

        applications = []
        stage_history = []
        used_pairs = set()

        attempts = 0
        max_attempts = target_count * 20

        while len(applications) < target_count and attempts < max_attempts:

            attempts += 1

            requisition = rng.choice(eligible_requisitions)
            candidate = rng.choice(candidates)

            req_id = requisition["requisition_id"]
            candidate_id = candidate["candidate_id"]

            pair = (req_id, candidate_id)

            if pair in used_pairs:
                continue

            if candidate_id not in resumes_by_candidate:
                continue

            used_pairs.add(pair)

            application_id = (
                f"APP-{req_id}-{candidate_id}"
            )

            resume = rng.choice(
                resumes_by_candidate[candidate_id]
            )

            req_created = requisition["created_at"]

            if isinstance(req_created, str):
                from datetime import datetime
                req_created = datetime.fromisoformat(req_created)

            applied_at = req_created + timedelta(
                days=rng.randint(1, 45)
            )

            stage = rng.choices(
                STAGES,
                weights=STAGE_WEIGHTS,
                k=1
            )[0]

            if stage in ("REJECTED", "WITHDRAWN"):
                status = "CLOSED"
            elif stage == "ON_HOLD":
                status = "ON_HOLD"
            else:
                status = "ACTIVE"

            score = round(rng.uniform(35, 100), 2)

            rejection_reason = None

            if stage == "REJECTED":
                rejection_reason = rng.choice([
                    "Insufficient technical skills",
                    "Experience requirements not met",
                    "Screening assessment not cleared",
                    "Interview evaluation unsuccessful",
                ])

            applications.append({
                "application_id": application_id,
                "requisition_business_id": req_id,
                "candidate_business_id": candidate_id,
                "resume_business_id": resume["resume_id"],
                "screening_score": score,
                "current_stage": stage,
                "status": status,
                "rejection_reason": rejection_reason,
                "recruiter_notes": "Synthetic application record",
                "applied_at": applied_at,
            })

            # Append-only stage history
            stage_history.append({
                "application_business_id": application_id,
                "from_stage": None,
                "to_stage": "APPLIED",
                "changed_by": "SYSTEM",
                "reason": "Application submitted",
                "transitioned_at": applied_at,
            })

            if stage != "APPLIED":
                stage_history.append({
                    "application_business_id": application_id,
                    "from_stage": "APPLIED",
                    "to_stage": stage,
                    "changed_by": "SYSTEM",
                    "reason": "Synthetic recruitment stage transition",
                    "transitioned_at": applied_at + timedelta(
                        days=rng.randint(1, 15)
                    ),
                })

        if len(applications) != target_count:
            raise RuntimeError(
                f"Could generate only {len(applications)} "
                f"applications out of {target_count}."
            )

        return {
            "applications": applications,
            "stage_history": stage_history,
        }
        