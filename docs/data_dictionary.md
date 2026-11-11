## Domain-Level Data Dictionary

This section supplements the SQLAlchemy-generated column definitions below. It documents business meaning, relationships, units, lifecycle information and important validation expectations.

The generated column definitions remain the authoritative reference for actual database types, nullability, primary keys, foreign keys, uniqueness and defaults.

### 1. Core Entity Reference

| Entity | Business Purpose | Primary Key | Important Relationships |
|---|---|---|---|
| Department | Organizational department | id | One department can have multiple requisitions. |
| JobRequisition | Job opening and hiring requirements | id | References Department. |
| Candidate | Synthetic candidate profile | id | Has skills, resumes and applications. |
| Application | Candidate application for a requisition | id | References Candidate, JobRequisition and optionally ResumeArtifact. |
| ResumeArtifact | Candidate resume metadata | id | References Candidate. |
| Skill | Skill master data | id | Connects to candidates and requisitions through bridge tables. |
| CandidateSkill | Candidate-skill association | id | References Candidate and Skill. |
| ScreeningRule | Requisition screening criterion | id | References JobRequisition. |
| Interview | Interview scheduling record | id | References Application. |
| Interviewer | Interview panel member | id | Connects to Interview through panel assignments. |
| Feedback | Structured interview assessment | id | References Interview and Interviewer. |
| Offer | Offer information | id | References Application. |

### 2. Field Units and Validation Expectations

| Entity | Important Fields | Units / Expected Values | Validation Expectations |
|---|---|---|---|
| Department | name, is_active | Text, Boolean | Department name should be present and unique. |
| JobRequisition | openings, minimum_salary, maximum_salary, experience_required, status | Count, configured currency, years, requisition status | Openings must be positive; minimum salary must not exceed maximum salary. |
| Candidate | experience_years, graduation_year, education, status | Years, calendar year, education enum, candidate status | Experience must be non-negative; graduation year must be valid. |
| Application | screening_score, current_stage, status | Configured score range, application stage, application status | Candidate and requisition must exist; duplicate candidate-requisition pairs are prevented. |
| ResumeArtifact | version, file_size_kb, file_format, parse_status | Version number, KB, file format, parsing status | Version must be positive; candidate reference must exist. |
| Skill | name, category, is_active | Text, skill category, Boolean | Skill name should be unique. |
| CandidateSkill | proficiency, years_of_experience, is_primary | Proficiency level, years, Boolean | Candidate and skill must exist; experience must be non-negative. |
| ScreeningRule | rule_type, rule_value, weight, is_knockout | Rule type, configured value, weight, Boolean | Weight must follow the configured database constraint. |
| Interview | round_number, scheduled_start, scheduled_end, mode, status | Round number, datetime, interview mode, interview status | End time must be after start time. |
| Interviewer | max_interviews_per_week, is_active | Interview count, Boolean | Maximum weekly interview count must be positive. |
| Feedback | technical_score, communication_score, problem_solving_score, cultural_fit_score, overall_score, recommendation | Configured score scale, recommendation enum | Scores must follow the configured score-range constraints. |
| Offer | offered_salary, signing_bonus, start_date, expiry_date, status | Configured currency, monetary amount, date, offer status | Salary must be positive; signing bonus must be non-negative. |

**Note:** Exact enum members and numeric score ranges should be read from the corresponding SQLAlchemy model definitions. Do not assume that every field has an application-level restriction simply because it appears in this reference.

### 3. Relationship Cardinalities

| Relationship | Cardinality |
|---|---|
| Department → JobRequisition | 1:N |
| Candidate → CandidateSkill | 1:N |
| Skill → CandidateSkill | 1:N |
| Candidate → ResumeArtifact | 1:N |
| Candidate → Application | 1:N |
| JobRequisition → Application | 1:N |
| JobRequisition → RequisitionApproval | 1:N |
| JobRequisition → ScreeningRule | 1:N |
| JobRequisition → RequisitionRequiredSkill | 1:N |
| Application → ApplicationStageHistory | 1:N |
| Application → Interview | 1:N |
| Interview → InterviewPanelAssignment | 1:N |
| Interviewer → InterviewPanelAssignment | 1:N |
| Interview → Feedback | 1:N |
| Interviewer → Feedback | 1:N |
| Application → Offer | 1:N |

The candidate-skill, requisition-required-skill and interview-panel relationships use bridge tables.

### 4. Lifecycle States

The database uses enum-backed fields for several lifecycle attributes.

The principal lifecycle areas are:

- Requisition: status, approval and closing dates.
- Application: current stage and application status.
- Candidate: candidate status.
- Interview: interview round, mode and status.
- Feedback: recommendation.
- Offer: approval, extension, acceptance and rejection statuses and timestamps.

The exact permitted enum values are defined in the SQLAlchemy models.

### 5. Date and Timestamp Fields

| Entity | Date / Timestamp Fields |
|---|---|
| JobRequisition | created_at, approved_at, closed_at, updated_at |
| Candidate | created_at, updated_at |
| Application | applied_at, updated_at |
| ResumeArtifact | uploaded_at |
| Interview | scheduled_start, scheduled_end, actual_start, actual_end, created_at, updated_at |
| InterviewPanelAssignment | assigned_at |
| Feedback | submitted_at |
| Offer | start_date, expiry_date, created_at, approved_at, extended_at, accepted_at, rejected_at |
| ApplicationStageHistory | transitioned_at |
| AuditEvent | occurred_at |

Dates and timestamps should be checked for logical ordering and consistency with the relevant lifecycle.

### 6. Identifier Conventions

The business identifier fields are separate from internal integer primary keys.

The intended business identifier patterns are:

| Entity | Identifier Pattern |
|---|---|
| Job Requisition | REQ-2026-000001 |
| Candidate | CAND-000001 |
| Application | APP-<requisition-id>-<candidate-id> |
| Interview | INT-2026-000001 |
| Feedback | FB-<interview-id>-<interviewer-id> |
| Offer | OFF-2026-000001 |

These are the target nomenclature conventions from the assignment. Verify actual generated values against the generator output before claiming complete compliance.

### 7. Ground Truth and Anomaly Labels

Known anomaly scenarios are stored separately from the normal recruitment records.

The five documented scenarios are:

1. Interview scheduled for an unavailable interviewer.
2. Duplicate candidate application.
3. Missing feedback with stage progression.
4. Offer salary outside the approved band.
5. Closed requisition with active applications.

The ground-truth records identify the issue type and expected classification. They should not be mixed into model input features.

### 8. Data Dictionary Limitations

This document is generated from SQLAlchemy model metadata. It describes database-level structure and constraints.

It does not automatically capture every business rule, generator decision, scheduling policy, lifecycle transition or application-level validation.

For complete business-rule documentation, refer to:

- `docs/architecture.md`
- `docs/database_schema.md`
- `README.md`
- The relevant generator, model and validation source files.