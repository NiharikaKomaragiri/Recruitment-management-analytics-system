# Recruitment Management & Analytics System

An end-to-end recruitment management and analytics platform built using **Python, SQLAlchemy, SQLite, FastAPI, Pandas, and Streamlit**.

The system generates synthetic recruitment data, manages recruitment workflows, provides REST APIs, validates database integrity, documents labelled anomaly scenarios, and visualizes recruitment analytics through an interactive dashboard.

## Key Features

- Synthetic recruitment data generation.
- Relational database design using SQLite and SQLAlchemy.
- Candidate and requisition management.
- Application and interview workflow management.
- Structured interview feedback and offer management.
- REST APIs using FastAPI.
- Data validation and integrity checks.
- Five labelled anomaly scenarios.
- CSV, JSON, and SQL exports.
- Interactive Streamlit analytics dashboard.
- Reproducibility testing using SHA256 checksums.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Core development |
| SQLite | Relational database |
| SQLAlchemy | ORM and database operations |
| Pandas | Data processing |
| NumPy | Numerical operations |
| Faker | Synthetic data generation |
| FastAPI | REST API development |
| Pydantic | Request validation |
| Streamlit | Analytics dashboard |
| Plotly | Data visualization |
| Pytest | Automated testing |

## System Architecture

```text
Synthetic Data Generation
          |
          v
     Data Generators
          |
          v
    SQLite Database
          |
    +-----+------+
    |            |
    v            v
  FastAPI     Analytics
    |            |
    v            v
 REST APIs   Validation
                 |
                 v
          Ground Truth Reports

Database
   |
   v
CSV / JSON / SQL Exports

SQLite Database
   |
   v
Streamlit Dashboard
```

## Dataset Summary

The generated database contains **17 tables and 29,159 records**.

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

## Recruitment Workflow

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

## Database Design

The database contains 17 relational tables covering the recruitment lifecycle.

- Primary keys and foreign keys maintain relationships.
- Bridge tables represent many-to-many relationships.
- Application stage history records recruitment progression.
- The `audit_events` table is included for future audit tracking and currently contains zero records.

Detailed documentation:

- `docs/database_schema.md`
- `docs/data_dictionary.md`
- `docs/architecture.md`

## Anomaly Scenarios

Five labelled synthetic anomaly scenarios are included.

| ID | Anomaly |
|---|---|
| ANOM-001 | Interview scheduled for an unavailable interviewer |
| ANOM-002 | Duplicate candidate application |
| ANOM-003 | Missing interview feedback but recruitment stage advanced |
| ANOM-004 | Offer salary outside the approved band |
| ANOM-005 | Closed requisition with active applications |

Files:

- `data/ground_truth/anomaly_cases.csv`
- `data/ground_truth/anomaly_cases.json`

These are labelled test scenarios and do not intentionally corrupt the main recruitment database.

## Data Validation

The validation module checks:

- Primary key uniqueness.
- Foreign key integrity.
- Required field completeness.
- Dataset record counts.
- Duplicate candidate-requisition applications.
- Offer salary ranges.
- Interview scheduling consistency.
- Application-requisition relationships.

Validation reports are stored under `data/ground_truth/`.

## Reproducibility Testing

Reproducibility was tested using two independent project copies.

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

## FastAPI Endpoints

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

Swagger documentation is available at `/docs`.

## Streamlit Dashboard

The dashboard provides:

- Recruitment KPI cards.
- Application stage distribution.
- Requisition status distribution.
- Department-wise requisition analytics.
- Interview status and round analytics.
- Offer status and average salary analytics.
- Candidate search and exploration.
- Recent application records.

## Project Structure

```text
Recruitment Management & Analytics System/
├── backend/
│   ├── main.py
│   ├── config.py
│   └── src/
│       ├── database/
│       ├── generators/
│       ├── analytics/
│       ├── api/
│       └── services/
├── frontend/
│   └── app.py
├── data/
│   ├── database/
│   ├── raw/
│   ├── processed/
│   ├── exports/
│   └── ground_truth/
├── docs/
├── scripts/
├── tests/
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/NiharikaKomaragiri/recruitment-management-analytics-system.git
cd "Recruitment Management & Analytics System"
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

Run these commands from the project root unless otherwise specified.

### 1. Generate synthetic data

```powershell
cd backend
python -m src.generators.lin
```

**Warning:** This pipeline drops and recreates database tables. Run it only when you intend to regenerate the database.

### 2. Generate anomaly scenarios

```powershell
python -m src.generators.anomaly_generator
```

### 3. Validate database records

```powershell
python -m src.analytics.validate_data
```

### 4. Export database records

```powershell
python -m src.generators.generator_export
```

### 5. Start FastAPI

```powershell
python -m uvicorn main:app --reload
```

- API: http://127.0.0.1:8000
- Swagger UI: http://127.0.0.1:8000/docs

### 6. Start Streamlit Dashboard

Open another terminal in the project root, activate the virtual environment, and run:

```powershell
python -m streamlit run frontend/app.py
```

Dashboard: http://localhost:8501

### 7. Run automated tests

From the project root:

```powershell
python -m pytest -v
```

## Output Files

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

## Future Enhancements

- Job posting and requisition creation interface.
- Advanced candidate-job matching.
- Automated resume parsing.
- AI-assisted candidate ranking.
- Interview scheduling optimization.
- Authentication and role-based access control.
- Advanced recruitment forecasting.
- Automated recruitment notifications.

## Conclusion

The Recruitment Management & Analytics System demonstrates an end-to-end, data-driven recruitment workflow. It combines synthetic data generation, relational database management, REST API development, data quality validation, anomaly documentation, reproducibility testing, and interactive analytics in a single application.

## Reproducibility Configuration

- **Random seed:** `20261022`
- **Seed identifier:** `seed-20261022`

The fixed seed supports repeatable synthetic data generation.