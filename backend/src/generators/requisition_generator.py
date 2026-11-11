from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Any

from faker import Faker
from config import RANDOM_SEED, SCALE_CONFIG


_JOB_TITLES = [
    "Python Developer",
    "Java Developer",
    "Data Analyst",
    "Machine Learning Engineer",
    "Frontend Developer",
    "Backend Developer",
    "Full Stack Developer",
    "Software Tester",
    "Data Engineer",
    "AI Engineer",
    "DevOps Engineer",
    "Product Manager",
    "Business Analyst",
    "QA Engineer",
    "Cloud Engineer",
]

_LOCATIONS = [
    "Hyderabad, India",
    "Bengaluru, India",
    "Chennai, India",
    "Pune, India",
    "Mumbai, India",
    "Remote",
]

_EMPLOYMENT_TYPES = [
    "FULL_TIME",
    "INTERNSHIP",
    "CONTRACT",
    "PART_TIME",
]

_APPROVER_NAMES = [
    ("HR Manager", "HR"),
    ("Department Head", "DEPARTMENT_HEAD"),
    ("VP Engineering", "MANAGEMENT"),
]

_MIN_PROFICIENCY_LEVELS = [
    "BEGINNER",
    "INTERMEDIATE",
    "ADVANCED",
]

_STATUS_CHOICES = [
    "APPROVED",
    "CLOSED",
    "DRAFT",
    "ON_HOLD",
    "PENDING",
]

_STATUS_WEIGHTS = [
    0.45,
    0.20,
    0.15,
    0.10,
    0.10,
]


class RequisitionGenerator:

    def generate(
        self,
        departments: list[dict[str, Any]],
        skills: list[dict[str, Any]],
        scale: str,
    ) -> dict[str, list[dict[str, Any]]]:

        if scale not in SCALE_CONFIG:
            raise ValueError(
                f"Unknown scale: {scale}. "
                f"Choose from {list(SCALE_CONFIG)}"
            )

        # Independent random generator for this generator.
        rng = random.Random(RANDOM_SEED)

        fake = Faker()
        fake.seed_instance(RANDOM_SEED)

        num_reqs = SCALE_CONFIG[scale][
            "num_job_requisitions"
        ]

        department_ids = [
            d["department_id"] for d in departments
        ]

        skill_ids = [
            s["skill_id"] for s in skills
        ]

        if not department_ids or not skill_ids:
            raise ValueError(
                "Departments and skills must not be empty."
            )

        start_dt = datetime(2025, 1, 1)
        end_dt = datetime(2026, 6, 1)

        date_range_seconds = int(
            (end_dt - start_dt).total_seconds()
        )

        requisitions = []
        req_approvals = []
        screening_rules = []
        req_required_skills = []

        for n in range(1, num_reqs + 1):

            req_id = f"REQ-2026-{n:06d}"

            department_id = rng.choice(department_ids)

            job_title = _JOB_TITLES[
                (n - 1) % len(_JOB_TITLES)
            ]

            min_salary = rng.randrange(
                300000, 800001, 10000
            )

            max_salary = min_salary + rng.randrange(
                100000, 500001, 10000
            )

            experience_required = round(
                rng.uniform(0, 8), 1
            )

            openings = rng.randint(1, 5)

            status = rng.choices(
                _STATUS_CHOICES,
                weights=_STATUS_WEIGHTS,
                k=1,
            )[0]

            created_at = start_dt + timedelta(
                seconds=rng.randint(
                    0, date_range_seconds
                )
            )

            approved_at = None
            closed_at = None

            if status in ("APPROVED", "CLOSED"):
                approved_at = created_at + timedelta(
                    days=rng.randint(1, 7)
                )

            if status == "CLOSED":
                closed_at = approved_at + timedelta(
                    days=rng.randint(30, 180)
                )

            requisitions.append({
                "requisition_id": req_id,
                "department_business_id": department_id,
                "job_title": job_title,
                "job_description": " ".join(
                    fake.sentences(nb=3)
                ),
                "location": rng.choice(_LOCATIONS),
                "employment_type": rng.choice(
                    _EMPLOYMENT_TYPES
                ),
                "openings": openings,
                "minimum_salary": float(min_salary),
                "maximum_salary": float(max_salary),
                "currency": "INR",
                "experience_required": experience_required,
                "remote_allowed": rng.choice(
                    [True, False]
                ),
                "status": status,
                "created_at": created_at,
                "approved_at": approved_at,
                "closed_at": closed_at,
            })

            # Approval history.
            if status in ("APPROVED", "CLOSED"):

                approver_name, approver_role = rng.choice(
                    _APPROVER_NAMES
                )

                req_approvals.append({
                    "requisition_business_id": req_id,
                    "approver_name": approver_name,
                    "approver_role": approver_role,
                    "decision": "APPROVED",
                    "comments": (
                        "Requisition reviewed and approved."
                    ),
                    "decided_at": approved_at,
                })

            # Screening rules.
            rules = [
                (
                    "MIN_EXPERIENCE",
                    str(experience_required),
                    0.30,
                    True,
                    "Minimum required experience in years",
                ),
                (
                    "MIN_EDUCATION",
                    "BACHELOR",
                    0.20,
                    False,
                    "Minimum education qualification",
                ),
                (
                    "REQUIRED_SKILL",
                    "MATCH_REQUIRED_SKILLS",
                    0.50,
                    False,
                    "Candidate must match required job skills",
                ),
            ]

            for rule_num, rule in enumerate(
                rules, start=1
            ):

                (
                    rule_type,
                    rule_value,
                    weight,
                    knockout,
                    description,
                ) = rule

                screening_rules.append({
                    "rule_id": (
                        f"RULE-{n:06d}-{rule_num:02d}"
                    ),
                    "requisition_business_id": req_id,
                    "rule_type": rule_type,
                    "rule_value": rule_value,
                    "weight": weight,
                    "is_knockout": knockout,
                    "is_active": True,
                    "description": description,
                })

            # Required skills.
            number_of_skills = rng.randint(
                3, min(6, len(skill_ids))
            )

            selected_skills = rng.sample(
                skill_ids,
                number_of_skills,
            )

            for index, skill_id in enumerate(
                selected_skills
            ):

                req_required_skills.append({
                    "requisition_business_id": req_id,
                    "skill_business_id": skill_id,
                    "minimum_proficiency": rng.choice(
                        _MIN_PROFICIENCY_LEVELS
                    ),
                    "is_mandatory": index < 2,
                })

        return {
            "requisitions": requisitions,
            "req_approvals": req_approvals,
            "screening_rules": screening_rules,
            "req_required_skills": req_required_skills,
        }