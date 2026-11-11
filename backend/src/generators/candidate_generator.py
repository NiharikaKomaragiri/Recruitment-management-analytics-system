import random
from pathlib import Path

import pandas as pd
from faker import Faker

SEED = 20261022
COUNT = 2000

rng = random.Random(SEED)

fake = Faker()
fake.seed_instance(SEED)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def generate_candidates(skills_df):
    candidates = []
    candidate_skills = []
    resumes = []

    skill_ids = skills_df["skill_id"].tolist()

    education_levels = [
        "HIGH_SCHOOL",
        "ASSOCIATE",
        "BACHELOR",
        "MASTER",
        "DOCTORATE",
        "OTHER",
    ]

    statuses = [
        "ACTIVE",
        "ACTIVE",
        "ACTIVE",
        "PLACED",
        "WITHDRAWN",
    ]

    titles = [
        "Software Developer",
        "Python Developer",
        "Data Analyst",
        "Java Developer",
        "Frontend Developer",
        "AI Engineer",
        "Backend Developer",
        "Fresher",
    ]

    fields_of_study = [
        "Computer Science",
        "Information Technology",
        "Electronics",
        "Data Science",
        "Business",
    ]

    proficiency_levels = [
        "BEGINNER",
        "INTERMEDIATE",
        "ADVANCED",
        "EXPERT",
    ]

    for i in range(1, COUNT + 1):
        candidate_id = f"CAND-{i:06d}"

        education = rng.choice(education_levels)
        graduation_year = rng.randint(2015, 2026)

        max_experience = max(
            0,
            min(15, graduation_year - 2005)
        )

        experience = round(
            rng.uniform(0, max_experience), 1
        )

        candidates.append({
            "candidate_id": candidate_id,
            "full_name": fake.name(),
            "email": f"candidate{i}@example.test",
            "phone": fake.phone_number()[:30],
            "education": education,
            "field_of_study": rng.choice(fields_of_study),
            "institution": fake.company() + " University",
            "graduation_year": graduation_year,
            "experience_years": experience,
            "current_title": rng.choice(titles),
            "current_company": (
                fake.company() if experience > 0 else None
            ),
            "linkedin_url": None,
            "portfolio_url": None,
            "summary": fake.sentence(),
            "status": rng.choice(statuses),
        })

        # Generate between 3 and 10 skills per candidate.
        selected_skills = rng.sample(
            skill_ids,
            k=rng.randint(3, min(10, len(skill_ids))),
        )

        for index, skill_id in enumerate(selected_skills):
            candidate_skills.append({
                "candidate_id": candidate_id,
                "skill_id": skill_id,
                "proficiency": rng.choice(proficiency_levels),
                "years_of_experience": round(
                    rng.uniform(0, experience), 1
                ),
                "is_primary": index == 0,
            })

        # One synthetic resume metadata record per candidate.
        resumes.append({
            "resume_id": f"RES-{candidate_id}-V01",
            "candidate_id": candidate_id,
            "version": 1,
            "file_name": f"{candidate_id}_resume.pdf",
            "file_path": f"resumes/{candidate_id}_resume.pdf",
            "file_size_kb": round(
                rng.uniform(100, 800), 2
            ),
            "file_format": "PDF",
            "is_latest": True,
            "parse_status": "PARSED",
            "parsed_text": None,
        })

    return (
        pd.DataFrame(candidates),
        pd.DataFrame(candidate_skills),
        pd.DataFrame(resumes),
    )


if __name__ == "__main__":
    skills_df = pd.read_csv(
        RAW_DIR / "skills.csv"
    )

    candidates, candidate_skills, resumes = (
        generate_candidates(skills_df)
    )

    candidates.to_csv(
        RAW_DIR / "candidates.csv", index=False
    )

    candidate_skills.to_csv(
        RAW_DIR / "candidate_skills.csv", index=False
    )

    resumes.to_csv(
        RAW_DIR / "resume_artifacts.csv", index=False
    )

    print("Candidate data generated successfully!")
    print("Candidates:", len(candidates))
    print("Candidate skills:", len(candidate_skills))
    print("Resume records:", len(resumes))