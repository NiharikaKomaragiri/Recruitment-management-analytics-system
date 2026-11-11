import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import streamlit as st
import pandas as pd

from sqlalchemy import text
from src.database.database import engine


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Recruitment Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown("""
<style>
section[data-testid="stSidebar"] {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    overflow-y: auto;
}

section[data-testid="stSidebar"] > div {
    height: 100vh;
    overflow-y: auto;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# DATABASE FUNCTIONS
# =========================================================

@st.cache_data(ttl=30)
def load_data(query):

    with engine.connect() as connection:
        return pd.read_sql_query(text(query), connection)


def get_count(table_name):

    allowed_tables = {
        "candidates",
        "job_requisitions",
        "applications",
        "interviews",
        "offers",
        "departments",
        "feedbacks",
        "interviewers",
    }

    if table_name not in allowed_tables:
        return 0

    try:
        dataframe = load_data(
            f"SELECT COUNT(*) AS total FROM {table_name}"
        )
        return int(dataframe.iloc[0]["total"])
    except Exception:
        return 0


def show_chart(dataframe, x, y, title):

    if dataframe.empty:
        st.info("No data available for this chart.")
        return

    st.subheader(title)
    st.bar_chart(dataframe, x=x, y=y, use_container_width=True)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.title("📊 Recruitment Analytics")

st.sidebar.caption("Recruitment Management System")

page = st.sidebar.radio(
    "Navigation",
    [
        "Overview",
        "Application Analytics",
        "Requisition Analytics",
        "Interview Analytics",
        "Offer Analytics",
        "Candidate Explorer",
    ],
)

st.sidebar.divider()

if st.sidebar.button("🔄 Refresh Dashboard"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption("Data source: Recruitment SQLite Database")


# =========================================================
# LOAD KPI COUNTS
# =========================================================

total_candidates = get_count("candidates")
total_requisitions = get_count("job_requisitions")
total_applications = get_count("applications")
total_interviews = get_count("interviews")
total_offers = get_count("offers")
total_departments = get_count("departments")
total_feedback = get_count("feedbacks")
total_interviewers = get_count("interviewers")


# =========================================================
# OVERVIEW PAGE
# =========================================================

if page == "Overview":

    st.title("📊 Recruitment Analytics Dashboard")

    st.write(
        "Monitor recruitment activities, candidate progress, "
        "interviews, and hiring outcomes."
    )

    st.divider()

    # KPI CARDS
    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Candidates", f"{total_candidates:,}")
    col2.metric("Job Requisitions", f"{total_requisitions:,}")
    col3.metric("Applications", f"{total_applications:,}")
    col4.metric("Interviews", f"{total_interviews:,}")

    col5, col6, col7, col8 = st.columns(4)

    col5.metric("Offers", f"{total_offers:,}")
    col6.metric("Departments", f"{total_departments:,}")
    col7.metric("Feedback Records", f"{total_feedback:,}")
    col8.metric("Interviewers", f"{total_interviewers:,}")

    st.divider()

    # APPLICATION STAGE DISTRIBUTION
    left, right = st.columns(2)

    with left:

        try:
            stage_data = load_data("""
                SELECT current_stage AS stage,
                       COUNT(*) AS total
                FROM applications
                GROUP BY current_stage
                ORDER BY total DESC
            """)

            show_chart(
                stage_data,
                "stage",
                "total",
                "Application Stage Distribution",
            )

        except Exception as error:
            st.warning(f"Unable to load application stages: {error}")

    with right:

        try:
            req_data = load_data("""
                SELECT status, COUNT(*) AS total
                FROM job_requisitions
                GROUP BY status
                ORDER BY total DESC
            """)

            show_chart(
                req_data,
                "status",
                "total",
                "Requisition Status Distribution",
            )

        except Exception as error:
            st.warning(f"Unable to load requisitions: {error}")

    # RECENT APPLICATIONS
    st.subheader("Recent Applications")

    try:
        recent = load_data("""
            SELECT
                a.application_id,
                c.full_name AS candidate,
                r.job_title,
                a.current_stage,
                a.status,
                a.applied_at
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            JOIN job_requisitions r ON a.requisition_id = r.id
            ORDER BY a.applied_at DESC
            LIMIT 10
        """)

        st.dataframe(
            recent,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.warning(f"Unable to load recent applications: {error}")


# =========================================================
# APPLICATION ANALYTICS
# =========================================================

elif page == "Application Analytics":

    st.title("📋 Application Analytics")

    st.write("Analyze application progress across recruitment stages.")

    try:
        stage_data = load_data("""
            SELECT current_stage AS stage,
                   COUNT(*) AS total
            FROM applications
            GROUP BY current_stage
            ORDER BY total DESC
        """)

        show_chart(
            stage_data,
            "stage",
            "total",
            "Applications by Stage",
        )

        status_data = load_data("""
            SELECT status, COUNT(*) AS total
            FROM applications
            GROUP BY status
        """)

        show_chart(
            status_data,
            "status",
            "total",
            "Application Status",
        )

        st.subheader("Application Records")

        applications = load_data("""
            SELECT
                a.application_id,
                c.candidate_id,
                c.full_name,
                r.requisition_id,
                r.job_title,
                a.screening_score,
                a.current_stage,
                a.status,
                a.applied_at
            FROM applications a
            JOIN candidates c ON a.candidate_id = c.id
            JOIN job_requisitions r ON a.requisition_id = r.id
            ORDER BY a.applied_at DESC
        """)

        st.dataframe(
            applications,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(f"Application analytics error: {error}")


# =========================================================
# REQUISITION ANALYTICS
# =========================================================

elif page == "Requisition Analytics":

    st.title("💼 Requisition Analytics")

    try:
        status_data = load_data("""
            SELECT status, COUNT(*) AS total
            FROM job_requisitions
            GROUP BY status
        """)

        show_chart(
            status_data,
            "status",
            "total",
            "Jobs by Requisition Status",
        )

        department_data = load_data("""
            SELECT
                d.name AS department,
                COUNT(r.id) AS total_jobs
            FROM job_requisitions r
            JOIN departments d ON r.department_id = d.id
            GROUP BY d.name
            ORDER BY total_jobs DESC
        """)

        show_chart(
            department_data,
            "department",
            "total_jobs",
            "Requisitions by Department",
        )

        st.subheader("Job Requisition Details")

        requisitions = load_data("""
            SELECT
                r.requisition_id,
                r.job_title,
                d.name AS department,
                r.location,
                r.employment_type,
                r.openings,
                r.minimum_salary,
                r.maximum_salary,
                r.status
            FROM job_requisitions r
            JOIN departments d ON r.department_id = d.id
            ORDER BY r.created_at DESC
        """)

        st.dataframe(
            requisitions,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(f"Requisition analytics error: {error}")


# =========================================================
# INTERVIEW ANALYTICS
# =========================================================

elif page == "Interview Analytics":

    st.title("🗓️ Interview Analytics")

    try:
        status_data = load_data("""
            SELECT status, COUNT(*) AS total
            FROM interviews
            GROUP BY status
        """)

        show_chart(
            status_data,
            "status",
            "total",
            "Interview Status Distribution",
        )

        round_data = load_data("""
            SELECT round_name, COUNT(*) AS total
            FROM interviews
            GROUP BY round_name
            ORDER BY total DESC
        """)

        show_chart(
            round_data,
            "round_name",
            "total",
            "Interviews by Round",
        )

        st.subheader("Interview Schedule")

        interviews = load_data("""
            SELECT
                i.interview_id,
                c.full_name AS candidate,
                r.job_title,
                i.round_name,
                i.scheduled_start,
                i.scheduled_end,
                i.mode,
                i.status
            FROM interviews i
            JOIN applications a ON i.application_id = a.id
            JOIN candidates c ON a.candidate_id = c.id
            JOIN job_requisitions r ON a.requisition_id = r.id
            ORDER BY i.scheduled_start
        """)

        st.dataframe(
            interviews,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(f"Interview analytics error: {error}")


# =========================================================
# OFFER ANALYTICS
# =========================================================

elif page == "Offer Analytics":

    st.title("🎯 Offer Analytics")

    try:
        status_data = load_data("""
            SELECT status, COUNT(*) AS total
            FROM offers
            GROUP BY status
        """)

        show_chart(
            status_data,
            "status",
            "total",
            "Offer Status Distribution",
        )

        salary_data = load_data("""
            SELECT
                r.job_title,
                ROUND(AVG(o.offered_salary), 2) AS average_salary
            FROM offers o
            JOIN applications a ON o.application_id = a.id
            JOIN job_requisitions r ON a.requisition_id = r.id
            GROUP BY r.job_title
            ORDER BY average_salary DESC
            LIMIT 15
        """)

        show_chart(
            salary_data,
            "job_title",
            "average_salary",
            "Average Offered Salary by Job",
        )

        st.subheader("Offer Details")

        offers = load_data("""
            SELECT
                o.offer_id,
                c.full_name AS candidate,
                r.job_title,
                o.offered_salary,
                o.currency,
                o.start_date,
                o.expiry_date,
                o.status
            FROM offers o
            JOIN applications a ON o.application_id = a.id
            JOIN candidates c ON a.candidate_id = c.id
            JOIN job_requisitions r ON a.requisition_id = r.id
            ORDER BY o.created_at DESC
        """)

        st.dataframe(
            offers,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(f"Offer analytics error: {error}")


# =========================================================
# CANDIDATE EXPLORER
# =========================================================

elif page == "Candidate Explorer":

    st.title("👥 Candidate Explorer")

    search = st.text_input(
        "Search candidates by name, email, or candidate ID"
    )

    try:
        candidates = load_data("""
            SELECT
                candidate_id,
                full_name,
                email,
                phone,
                education,
                field_of_study,
                institution,
                graduation_year,
                experience_years,
                current_title,
                current_company,
                status
            FROM candidates
            ORDER BY full_name
        """)

        if search:
            search_lower = search.lower()

            candidates = candidates[
                candidates.apply(
                    lambda row: row.astype(str)
                    .str.lower()
                    .str.contains(search_lower, regex=False)
                    .any(),
                    axis=1,
                )
            ]

        st.metric("Matching Candidates", len(candidates))

        st.dataframe(
            candidates,
            use_container_width=True,
            hide_index=True,
        )

    except Exception as error:
        st.error(f"Candidate explorer error: {error}")


# =========================================================
# FOOTER
# =========================================================

st.divider()

st.caption(
    "Recruitment Management & Analytics System | "
    "Powered by Python, Streamlit, Pandas, SQLAlchemy and SQLite"
)