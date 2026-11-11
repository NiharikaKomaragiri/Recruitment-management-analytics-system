# Recruitment Management & Analytics System

An end-to-end recruitment management and analytics platform built using Python, SQLAlchemy, SQLite, FastAPI, Pandas, and Streamlit.

The system generates synthetic recruitment data, manages recruitment workflows, provides REST APIs, documents labelled anomaly scenarios, validates database integrity, and visualizes recruitment analytics through an interactive dashboard.

## 1. Project Overview

The system manages the recruitment lifecycle, from job requisition creation and candidate applications through interviews, feedback, and offer management.

### Key Features

- Synthetic recruitment data generation.
- Relational database design and management.
- Recruitment workflow management.
- REST API development using FastAPI.
- Data validation and integrity checks.
- Labelled anomaly scenario generation.
- CSV, JSON, and SQL data exports.
- Interactive recruitment analytics dashboard.
- Reproducible synthetic dataset generation and export verification.

## 2. Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| SQLite | Relational database |
| SQLAlchemy | ORM and database operations |
| Pandas | Data processing and analysis |
| NumPy | Numerical operations |
| Faker | Synthetic data generation |
| FastAPI | REST API development |
| Pydantic | Request validation |
| Streamlit | Analytics dashboard |
| Plotly | Data visualization |
| Pytest | Automated testing |

## 3. System Architecture

```text
       SYNTHETIC DATA GENERATION
                  |
                  v
           Data Generators
                  |
                  v
           SQLite Database
                  |
       +----------+----------+
       |          |          |
       v          v          v
    FastAPI    Analytics  Validation
       |          |          |
       v          v          v
   REST APIs  Streamlit  Ground Truth
              Dashboard    Reports
       |
       v
   API Consumers

       DATABASE EXPORTS
                  |
                  v
             CSV / JSON / SQL
```

## 4. Recruitment Workflow

1. Generate departments, skills, and interviewers.
2. Generate candidate profiles and resume artifacts.
3. Create job requisitions.
4. Generate requisition approvals and screening rules.
5. Generate candidate applications.
6. Schedule interviews and assign interview panels.
7. Generate structured interview feedback.
8. Generate recruitment offers.
9. Validate database records and generate anomaly scenarios.
10. Export datasets and display recruitment analytics.

## 5. Dataset Summary

The final database contains 17 tables and 29,159 records.

| Entity | Records |
|---|---:|
| Departments | 10 |
| Skills | 50 |
| Interviewers | 50 |
| Candidates | 2,000 |
| Candidate Skills | 13,137 |
| Resume Artifacts | 2,000 |
| Job Requisitions | 100 |
| Requisition Approvals | 74 |
| Screening Rules | 300 |
| Required Requisition Skills | 436 |
| Applications | 3,000 |
| Application Stage History | 5,694 |
| Interviews | 600 |
| Interview Panel Assignments | 1,200 |
| Feedback Records | 358 |
| Offers | 150 |
| Audit Events | 0 |
| **Total** | **29,159** |

## 6. Database Design

The SQLite database contains 17 relational tables covering the recruitment lifecycle.

Primary keys and foreign keys maintain relationships between recruitment entities. Bridge tables manage many-to-many relationships, including candidate skills and interview panel assignments.

Application stage history stores recruitment stage transitions, providing a record of application progression.

The `audit_events` table is included in the schema for future audit-event tracking. It currently contains zero records in the generated dataset.

Detailed table definitions, relationships, constraints, and field descriptions are available in `docs/database_schema.md` and `docs/data_dictionary.md`.

## 7. Anomaly Scenarios

Five labelled synthetic anomaly scenarios are included:

| ID | Anomaly |
|---|---|
| ANOM-001 | Interview scheduled for an unavailable interviewer |
| ANOM-002 | Duplicate candidate application |
| ANOM-003 | Missing interview feedback but recruitment stage advanced |
| ANOM-004 | Offer salary outside the approved band |
| ANOM-005 | Closed requisition with active applications |

Files are stored in:

- `data/ground_truth/anomaly_cases.csv`
- `data/ground_truth/anomaly_cases.json`

These are labelled test scenarios and do not intentionally corrupt the main recruitment database.

## 8. Data Validation

The validation module checks:

- Primary key uniqueness.
- Foreign key integrity.
- Required field completeness.
- Dataset record counts.
- Duplicate candidate-requisition applications.
- Offer salary ranges.
- Interview scheduling consistency.
- Application-requisition relationships.

The final validation and automated test runs completed successfully.

Reports are stored under `data/ground_truth/`.

## 9. Reproducibility Testing

Reproducibility was verified using two independent project copies.

The same synthetic dataset was exported from both environments and compared using SHA256 file hashes.

| Metric | Result |
|---|---:|
| Independent test copies | 2 |
| Tables exported | 17 |
| Records per database | 29,159 |
| Export files compared | 37 |
| Matching files | 37 |
| Different files | 0 |
| SQL dump comparison | PASS |

Timestamp normalization and consistent SQL index ordering were applied before the final comparison.

**Result:** All 37 export files matched byte-for-byte across both test runs.

## 10. FastAPI Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | API home |
| GET | `/health` | Health check |
| GET | `/api/v1/candidates` | Retrieve candidates |
| GET | `/api/v1/candidates/{candidate_id}` | Retrieve a candidate |
| GET | `/api/v1/requisitions` | Retrieve job requisitions |
| POST | `/api/v1/applications` | Submit an application |
| GET | `/api/v1/applications` | Retrieve applications |
| GET | `/api/v1/interviews` | Retrieve interviews |
| GET | `/api/v1/offers` | Retrieve offers |

Interactive API documentation is available through Swagger UI at `/docs`.

## 11. Streamlit Dashboard

The dashboard provides:

- Recruitment KPI cards.
- Application stage distribution.
- Requisition status distribution.
- Department-wise requisition analytics.
- Interview status and round analytics.
- Offer status and average salary analytics.
- Candidate search and exploration.
- Recent application records.

The dashboard reads directly from the SQLite database.

## 12. Project Structure

```text
Recruitment Management & Analytics System/
│
├── backend/
│   ├── main.py
│   ├── config.py
│   └── src/
│       ├── database/
│       │   ├── models/
│       │   ├── database.py
│       │   └── init_db.py
│       ├── generators/
│       │   ├── master_data_generator.py
│       │   ├── candidate_generator.py
│       │   ├── requisition_generator.py
│       │   ├── application_generator.py
│       │   ├── interview_generator.py
│       │   ├── feedback_generator.py
│       │   ├── offer_generator.py
│       │   ├── anomaly_generator.py
│       │   ├── generator_export.py
│       │   └── lin.py
│       ├── analytics/
│       │   └── validate_data.py
│       ├── api/
│       └── services/
│
├── frontend/
│   └── app.py
│
├── data/
│   ├── database/
│   ├── raw/
│   ├── processed/
│   ├── exports/
│   └── ground_truth/
│
├── docs/
├── scripts/
├── tests/
│   └── test_database.py
│
├── .vscode/
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## 13. Installation and Setup

### Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd "Recruitment Management & Analytics System"
```

### Create a Virtual Environment

```bash
python -m venv .venv
```

### Activate the Environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## 14. Running the Application

### Navigate to the Backend

From the project root:

```powershell
cd backend
```

### Generate Synthetic Data

```powershell
python -m src.generators.lin
```

**Warning:** This pipeline drops and recreates the database tables. Run it only when you intend to regenerate the database.

### Generate Anomaly Scenarios

```powershell
python -m src.generators.anomaly_generator
```

### Validate Database Records

```powershell
python -m src.analytics.validate_data
```

### Export Database Records

```powershell
python -m src.generators.generator_export
```

### Start FastAPI

```powershell
python -m uvicorn main:app --reload
```

API: `http://127.0.0.1:8000`

Swagger documentation: `http://127.0.0.1:8000/docs`

### Start Streamlit Dashboard

Open another terminal in the project root and activate the virtual environment.

```powershell
python -m streamlit run frontend/app.py
```

Dashboard: `http://localhost:8501`

### Run Database Tests

From the project root:

```powershell
python -m pytest -v
```

## 15. Output Files

### Data Exports

- CSV database exports.
- JSON database exports.
- SQL database dump.
- Export manifest.
- Export summary.

### Ground Truth

- Labelled anomaly scenarios.
- Data validation report.
- Data validation summary.
- Export checksums.

## 16. Future Enhancements

- Job posting and requisition creation interface.
- Advanced candidate-job matching.
- Automated resume parsing.
- AI-assisted candidate ranking.
- Interview scheduling optimization.
- Authentication and role-based access control.
- Advanced recruitment forecasting.
- Automated recruitment notifications.

## 17. Conclusion

The Recruitment Management & Analytics System demonstrates an end-to-end, data-driven recruitment workflow.

It combines synthetic data generation, relational database management, REST API development, data quality validation, anomaly scenario documentation, reproducibility testing, and interactive analytics in a single application.

### Reproducibility

The synthetic data generation process uses a fixed random seed
to support repeatable dataset generation.

Seed: [INSERT THE ACTUAL SEED USED BY YOUR GENERATOR]

The source manifest and export summary are available in
`data/exports/`.#   r e c r u i t m e n t - m a n a g e m e n t - a n a l y t i c s - s y s t e m  
 