# Database Schema Documentation

## 1. Overview

The Recruitment Management & Analytics System uses SQLite and SQLAlchemy to manage recruitment information.

The database contains 17 relational tables covering departments, skills, candidates, requisitions, applications, interviews, feedback, offers and related records.

**Database:** SQLite  
**ORM:** SQLAlchemy  
**Total tables:** 17

Database location:

`data/database/recruitment.db`

## 2. Database Tables

| No. | Table | Purpose |
|---|---|---|
| 1 | departments | Department information |
| 2 | skills | Skill master data |
| 3 | interviewers | Interviewer information |
| 4 | candidates | Candidate profiles |
| 5 | candidate_skills | Candidate-skill relationships |
| 6 | resume_artifacts | Candidate resume metadata |
| 7 | job_requisitions | Job openings |
| 8 | requisition_approvals | Requisition approval records |
| 9 | screening_rules | Requisition screening criteria |
| 10 | requisition_required_skills | Required skills for requisitions |
| 11 | applications | Candidate applications |
| 12 | application_stage_history | Application lifecycle history |
| 13 | interviews | Interview scheduling records |
| 14 | interview_panel_assignments | Interviewer-panel relationships |
| 15 | feedbacks | Structured interview feedback |
| 16 | offers | Candidate offer records |
| 17 | audit_events | Audit event structure |

## 3. Entity Relationships and Cardinality

| Parent Entity | Child Entity | Relationship | Description |
|---|---|---|---|
| Department | Job Requisition | 1:N | A department can have multiple requisitions. |
| Candidate | Candidate Skill | 1:N | A candidate can have multiple skill records. |
| Skill | Candidate Skill | 1:N | A skill can be associated with multiple candidates. |
| Candidate | Resume Artifact | 1:N | A candidate can have multiple resume versions. |
| Job Requisition | Requisition Approval | 1:N | A requisition can have multiple approval records. |
| Job Requisition | Screening Rule | 1:N | A requisition can have multiple screening rules. |
| Job Requisition | Required Skill | 1:N | A requisition can require multiple skills. |
| Skill | Required Skill | 1:N | A skill can be required by multiple requisitions. |
| Candidate | Application | 1:N | A candidate can apply to multiple requisitions. |
| Job Requisition | Application | 1:N | A requisition can receive multiple applications. |
| Application | Stage History | 1:N | An application can have multiple stage-history records. |
| Application | Interview | 1:N | An application can have multiple interviews. |
| Interview | Panel Assignment | 1:N | An interview can have multiple panel assignments. |
| Interviewer | Panel Assignment | 1:N | An interviewer can be assigned to multiple interviews. |
| Interview | Feedback | 1:N | An interview can have feedback from multiple interviewers. |
| Interviewer | Feedback | 1:N | An interviewer can submit feedback for multiple interviews. |
| Application | Offer | 1:N | An application can have offer records. |

### Many-to-Many Relationships

Two bridge tables implement many-to-many relationships:

**candidate_skills**

Connects candidates and skills.

- Candidate foreign key: `candidate_id`
- Skill foreign key: `skill_id`
- Unique candidate-skill combination.

**requisition_required_skills**

Connects job requisitions and skills.

- Requisition foreign key: `requisition_id`
- Skill foreign key: `skill_id`
- Unique requisition-skill combination.

**interview_panel_assignments**

Connects interviews and interviewers.

- Interview foreign key: `interview_id`
- Interviewer foreign key: `interviewer_id`
- Unique interview-interviewer combination.

## 4. Important Foreign-Key Relationships

| Table | Foreign Key | References |
|---|---|---|
| job_requisitions | department_id | departments.id |
| candidate_skills | candidate_id | candidates.id |
| candidate_skills | skill_id | skills.id |
| resume_artifacts | candidate_id | candidates.id |
| requisition_approvals | requisition_id | job_requisitions.id |
| screening_rules | requisition_id | job_requisitions.id |
| requisition_required_skills | requisition_id | job_requisitions.id |
| requisition_required_skills | skill_id | skills.id |
| applications | requisition_id | job_requisitions.id |
| applications | candidate_id | candidates.id |
| applications | resume_id | resume_artifacts.id |
| application_stage_history | application_id | applications.id |
| interviews | application_id | applications.id |
| interview_panel_assignments | interview_id | interviews.id |
| interview_panel_assignments | interviewer_id | interviewers.id |
| feedbacks | interview_id | interviews.id |
| feedbacks | interviewer_id | interviewers.id |
| offers | application_id | applications.id |

## 5. Lifecycle and History

### Application Lifecycle

Applications maintain a current stage and status.

The `application_stage_history` table records stage changes using:

- `from_stage`
- `to_stage`
- `changed_by`
- `reason`
- `transitioned_at`

This provides a historical record of application progression.

### Requisition Lifecycle

Requisitions contain:

- Status
- Created date
- Approval date
- Closing date
- Updated date

Approval decisions are stored separately in `requisition_approvals`.

### Interview Lifecycle

Interviews contain:

- Scheduled start and end.
- Actual start and end.
- Interview round.
- Mode.
- Status.
- Cancellation reason.

Panel assignments are maintained separately.

### Offer Lifecycle

Offers contain:

- Offered salary.
- Offer status.
- Approval timestamp.
- Extension timestamp.
- Acceptance timestamp.
- Rejection timestamp.

These fields support offer lifecycle reporting.

## 6. Constraints and Integrity

The database uses:

- Primary key constraints.
- Foreign key constraints.
- Unique constraints.
- Check constraints.
- Required-field constraints.

Examples include:

- Unique candidate-requisition application combinations.
- Unique candidate-skill combinations.
- Unique requisition-required-skill combinations.
- Valid interview start and end ordering.
- Valid salary ranges.
- Non-negative experience values.
- Feedback score range checks.

## 7. Audit and Anomaly Handling

The `audit_events` table provides columns for entity type, entity ID, action, actor, old value, new value, metadata and event timestamp.

The current generated dataset contains zero audit event records. Application stage history is populated separately.

Known anomaly scenarios are maintained in separate ground-truth CSV and JSON files. They are not treated as ordinary valid baseline records.

## 8. Database Implementation

SQLAlchemy models:

`backend/src/database/models/`

Database connection:

`backend/src/database/database.py`

Database configuration:

`backend/config.py`

Database initialization:

`backend/src/database/init_db.py`

Database file:

`data/database/recruitment.db`

## 9. Conclusion

The database provides a relational foundation for recruitment data management, lifecycle tracking, reporting and validation.

Its bridge tables support many-to-many relationships, while application stage history provides a record of recruitment progression.