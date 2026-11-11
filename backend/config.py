import os
from pathlib import Path
# ─────────────────────────────────────────────────────────────
# Project Identity
# ─────────────────────────────────────────────────────────────

PROJECT_NAME: str = "Recruitment Management & Analytics System"
PROJECT_VERSION: str = "0.1.0"
PROJECT_DESCRIPTION: str = (
    "An end-to-end recruitment workflow system covering job requisitions, "
    "candidate management, applications, resume screening, interview scheduling, "
    "interviewer feedback, approvals, and offer management."
)
# ─────────────────────────────────────────────────────────────
# Reproducibility
# ─────────────────────────────────────────────────────────────

RANDOM_SEED: int = 20261022   # Fixed seed for reproducible synthetic data generation

# ─────────────────────────────────────────────────────────────
# Directory Layout
# ─────────────────────────────────────────────────────────────

BASE_DIR: Path = Path(__file__).resolve().parent.parent

DATA_DIR: Path        = BASE_DIR / "data"
RAW_DATA_DIR: Path    = DATA_DIR / "raw"
PROCESSED_DIR: Path   = DATA_DIR / "processed"
EXPORTS_DIR: Path     = DATA_DIR / "exports"
GROUND_TRUTH_DIR: Path = DATA_DIR / "ground_truth"

# ─────────────────────────────────────────────────────────────
# Database
# ─────────────────────────────────────────────────────────────

DATABASE_FILENAME: str = "recruitment.db"

DATABASE_DIR: Path = DATA_DIR / "database"
DATABASE_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_PATH: Path = DATABASE_DIR / DATABASE_FILENAME
DATABASE_URL: str = f"sqlite:///{DATABASE_PATH}"

# ─────────────────────────────────────────────────────────────
# Dataset Scale Configuration
# ─────────────────────────────────────────────────────────────
# These values control how many synthetic records are generated
# for each domain entity.  Adjust to 'small', 'medium', or 'large'
# scale as needed.

DATASET_SCALE: str = "medium"   # Options: "small" | "medium" | "large"

SCALE_CONFIG: dict = {
    "small": {
        "num_departments":       10,
        "num_skills":            50,
        "num_job_requisitions":  10,
        "num_candidates":       100,
        "num_applications":     150,
        "num_interviewers":      50,
        "num_interviews":        30,
        "num_offers":             8,
    },
    "medium": {
        "num_departments":       10,
        "num_skills":            50,
        "num_job_requisitions": 100,
        "num_candidates":      2000,
        "num_applications":    3000,
        "num_interviewers":      50,
        "num_interviews":       600,
        "num_offers":           150,
    },
    "large": {
        "num_departments":       10,
        "num_skills":            50,
        "num_job_requisitions": 500,
        "num_candidates":     10000,
        "num_applications":   15000,
        "num_interviewers":      50,
        "num_interviews":      3000,
        "num_offers":           750,
    },
}

# Convenience shortcut — active scale settings
ACTIVE_SCALE: dict = SCALE_CONFIG[DATASET_SCALE]

# ─────────────────────────────────────────────────────────────
# API Configuration
# ─────────────────────────────────────────────────────────────

API_HOST: str  = os.getenv("API_HOST", "127.0.0.1")
API_PORT: int  = int(os.getenv("API_PORT", "8000"))
API_PREFIX: str = "/api/v1"

# ─────────────────────────────────────────────────────────────
# Streamlit Dashboard Configuration
# ─────────────────────────────────────────────────────────────

DASHBOARD_TITLE: str = "Recruitment Analytics Dashboard"
DASHBOARD_PORT: int  = int(os.getenv("DASHBOARD_PORT", "8501"))
