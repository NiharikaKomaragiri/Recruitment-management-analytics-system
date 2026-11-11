import random
from pathlib import Path

import pandas as pd
from faker import Faker

SEED = 20261022

rng = random.Random(SEED)
fake = Faker()
fake.seed_instance(SEED)

RAW_DIR = Path("data/raw")
RAW_DIR.mkdir(parents=True, exist_ok=True)


def generate_departments():
    names = [
        "Engineering",
        "Human Resources",
        "Finance",
        "Marketing",
        "Data Science",
        "Information Technology",
        "Sales",
        "Operations",
        "Product Development",
        "Customer Support",
    ]

    return pd.DataFrame([
        {
            "department_id": f"DEPT-{i:04d}",
            "name": name,
            "description": f"{name} department",
            "cost_centre": f"CC-{i:04d}",
            "location": "Hyderabad",
            "head_of_department": fake.name(),
            "is_active": True,
        }
        for i, name in enumerate(names, start=1)
    ])


def generate_skills():
    names = [
        "Python", "Java", "JavaScript", "C", "C++",
        "SQL", "MySQL", "PostgreSQL", "MongoDB",
        "HTML", "CSS", "React", "Node.js",
        "FastAPI", "Flask", "Django",
        "Machine Learning", "Deep Learning",
        "TensorFlow", "PyTorch", "NLP",
        "Pandas", "NumPy", "Data Analysis",
        "Power BI", "Tableau", "Excel",
        "Git", "GitHub", "Docker",
        "AWS", "Azure", "REST API",
        "Data Structures", "Algorithms",
        "Spring Boot", "Angular",
        "Streamlit", "Linux", "Testing",
        "Selenium", "Agile", "Communication",
        "Problem Solving", "System Design",
        "Data Engineering", "Statistics",
        "Generative AI", "LangChain",
        "Vector Databases",
    ]

    records = []

    for i, name in enumerate(names, start=1):
        if name in ["Communication", "Problem Solving"]:
            category = "SOFT"
        elif name in ["English", "Telugu", "Hindi"]:
            category = "LANGUAGE"
        elif name in ["Docker", "Git", "GitHub", "AWS", "Azure"]:
            category = "TOOL"
        else:
            category = "TECHNICAL"

        records.append({
            "skill_id": f"SKILL-{i:05d}",
            "name": name,
            "category": category,
            "description": f"{name} skill",
            "is_active": True,
        })

    return pd.DataFrame(records)


def generate_interviewers(count=50):
    records = []

    designations = [
        "Technical Lead",
        "HR Manager",
        "Senior Developer",
        "Engineering Manager",
        "Team Lead",
    ]

    for i in range(1, count + 1):
        records.append({
            "interviewer_id": f"INTVR-{i:06d}",
            "full_name": fake.name(),
            "email": f"interviewer{i}@example.test",
            "department_id": f"DEPT-{rng.randint(1, 10):04d}",
            "designation": rng.choice(designations),
        })

    return pd.DataFrame(records)


if __name__ == "__main__":
    departments = generate_departments()
    skills = generate_skills()
    interviewers = generate_interviewers()

    departments.to_csv(
        RAW_DIR / "departments.csv", index=False
    )
    skills.to_csv(
        RAW_DIR / "skills.csv", index=False
    )
    interviewers.to_csv(
        RAW_DIR / "interviewers.csv", index=False
    )

    print("Master data generated successfully!")
    print("Departments:", len(departments))
    print("Skills:", len(skills))
    print("Interviewers:", len(interviewers))