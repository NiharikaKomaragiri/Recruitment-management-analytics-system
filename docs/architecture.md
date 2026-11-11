# System Architecture – Recruitment Management & Analytics System

## 1. Introduction

The Recruitment Management & Analytics System is a synthetic-data-driven recruitment management and analytics application developed using Python, SQLite, SQLAlchemy, FastAPI, Pandas and Streamlit.

The application represents the recruitment lifecycle, including job requisitions, candidate applications, screening, interview scheduling, structured feedback and offer management.

It provides relational data storage, REST API access, data validation, labelled anomaly scenarios, database exports and interactive recruitment analytics.

The system follows a modular architecture that separates data generation, database management, backend APIs, analytics, validation, frontend visualization and data exports.

## 2. High-Level Architecture

The system consists of six major components:

1. Synthetic Data Generation Layer
2. Database Layer
3. Backend API Layer
4. Analytics and Validation Layer
5. Frontend Dashboard Layer
6. Data Export Layer

### Architecture Diagram

```text
             SYNTHETIC DATA GENERATION
                         |
                         v
                Data Generator Modules
                         |
                         v
                  SQLITE DATABASE
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
       FASTAPI        ANALYTICS      VALIDATION
       BACKEND        PROCESSING      MODULE
          |              |              |
          v              v              v
      REST APIs      KPI METRICS    VALIDATION
          |              |           REPORTS
          v              v
     API CONSUMERS   STREAMLIT
                     DASHBOARD

                  DATA EXPORT
                         |
                         v
                   CSV / JSON / SQL
```

## 3. Component Description

### 3.1 Synthetic Data Generation Layer

The generation layer creates synthetic recruitment records using Python and Faker.

Generation follows a dependency-aware sequence so that child records reference valid parent records.

Main modules include:

- master_data_generator.py
- candidate_generator.py
- requisition_generator.py
- application_generator.py
- interview_generator.py
- feedback_generator.py
- offer_generator.py
- anomaly_generator.py
- lin.py

The main generation pipeline coordinates database initialization, master data generation and dependent recruitment record generation.

### 3.2 Database Layer

The database uses SQLite for persistent storage and SQLAlchemy as the Object Relational Mapper.

It contains 17 tables covering:

- Departments and skills.
- Candidates and candidate skills.
- Resume artifacts.
- Interviewers.
- Job requisitions and approvals.
- Screening rules and required skills.
- Applications and application stage history.
- Interviews and panel assignments.
- Structured feedback.
- Offers.
- Audit event records.

Primary keys, foreign keys, unique constraints and check constraints support database integrity.

### 3.3 Backend API Layer

FastAPI provides REST endpoints for retrieving recruitment information and submitting applications.

Main file:

backend/main.py

Implemented API operations include:

- Candidate retrieval.
- Individual candidate retrieval.
- Job requisition retrieval.
- Application submission.
- Application retrieval.
- Interview retrieval.
- Offer retrieval.
- API health checks.

Pydantic is used for request validation.

Swagger UI provides interactive API documentation.

### 3.4 Analytics and Validation Layer

This layer supports recruitment reporting and data quality checks.

The validation module checks:

- Primary key uniqueness.
- Foreign key integrity.
- Required field completeness.
- Duplicate candidate-requisition applications.
- Offer salary ranges.
- Interview scheduling consistency.
- Application-requisition relationships.
- Dataset record counts.

Validation results are generated as reports.

### 3.5 Frontend Dashboard Layer

The frontend uses Streamlit.

Main file:

frontend/app.py

The dashboard reads recruitment information from SQLite and presents:

- Recruitment KPI cards.
- Application stage distribution.
- Requisition status analytics.
- Department-wise requisition analytics.
- Interview analytics.
- Offer analytics.
- Candidate exploration.
- Recent application records.

### 3.6 Data Export Layer

The export module generates database representations in:

- CSV
- JSON
- SQL

Additional outputs include export manifests, summaries and checksum information.

Exports are maintained under data/exports/.

## 4. Recruitment Data Flow

1. Generate departments, skills and interviewers.
2. Generate synthetic candidates and resume artifacts.
3. Generate job requisitions.
4. Generate requisition approvals, screening rules and required skills.
5. Generate applications using valid candidate and requisition references.
6. Generate application stage history.
7. Generate interviews and panel assignments.
8. Generate structured interview feedback.
9. Generate offer records.
10. Generate labelled anomaly scenarios.
11. Validate database records.
12. Export data and display recruitment analytics.

## 5. Technology Architecture

| Layer | Technology | Responsibility |
|---|---|---|
| Programming | Python | Application logic |
| Data Generation | Faker | Synthetic records |
| Database | SQLite | Persistent storage |
| ORM | SQLAlchemy | Database operations |
| API | FastAPI | REST endpoints |
| API Validation | Pydantic | Request validation |
| Analytics | Pandas, NumPy | Data processing |
| Dashboard | Streamlit | Interactive reporting |
| Visualization | Plotly | Charts and graphs |
| Testing | Pytest | Automated testing |

## 6. Data Integrity and Traceability

The database uses primary keys, foreign keys, unique constraints and check constraints to support data consistency.

Application stage history records stage transitions.

The audit_events table provides a structure for storing audit information. The current generated dataset contains no audit event records.

Known anomaly scenarios are maintained separately from the main database using labelled ground-truth files.

## 7. Reproducibility

Reproducibility was tested using two independent copies of the project.

Both copies generated 17 tables containing 29,159 records.

The exported files were compared using SHA256 checksums.

Results:

| Metric | Result |
|---|---:|
| Independent test copies | 2 |
| Tables | 17 |
| Records per database | 29,159 |
| Files compared | 37 |
| Matching files | 37 |
| Different files | 0 |

Timestamp normalization and consistent SQL index ordering were applied before the final comparison.

## 8. Deployment and Execution Architecture

The backend and frontend run as separate local application processes.

### FastAPI

Address: http://127.0.0.1:8000

Swagger documentation: http://127.0.0.1:8000/docs

### Streamlit

Address: http://localhost:8501

The dashboard reads data from the SQLite database.

## 9. Project Directory Organization

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
│       ├── analytics/
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
├── .gitignore
├── pytest.ini
├── requirements.txt
└── README.md
```

## 10. Conclusion

The modular architecture separates synthetic data generation, relational storage, API access, analytics, validation and visualization.

The system demonstrates an integrated recruitment management workflow while providing a foundation for future enhancements such as AI-assisted candidate matching, resume parsing, role-based authentication and automated interview scheduling.