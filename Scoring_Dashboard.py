import streamlit as st
from datetime import datetime
from supabase import create_client

st.set_page_config(page_title="QA Hub", page_icon="🏠", layout="wide")

# --------------------
# Supabase connection
# --------------------
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_ANON_KEY"]
)

# ------------------------------------
# LOAD TEAM LEADERS FROM SUPABASE
# ------------------------------------
def load_team_leaders():
    res = supabase.table("team_leaders").select("*").execute()
    return res.data if res.data else []

# ------------------------------------
# LOAD CONSULTANTS BASED ON TEAM
# ------------------------------------
def load_consultants(team_leader):
    res = (
        supabase.table("consultants")
        .select("consultant")
        .eq("team_leader", team_leader)
        .execute()
    )
    return [c["consultant"] for c in res.data] if res.data else []

# ------------------------------------
# LOAD QUESTION SET BASED ON DEPARTMENT
# ------------------------------------
def load_questions(department):
    res = (
        supabase.table("question_sets")
        .select("*")
        .eq("department", department)
        .order("question_number", asc=True)
        .execute()
    )
    return res.data if res.data else []

# ---------------------
#  PAGE UI
# ---------------------
st.title("🏠 QA Audit Capture")
st.write("This page dynamically loads Team Leaders, Departments, Consultants and Questions.")

team_data = load_team_leaders()

team_list = sorted([t["team_leader"] for t in team_data])

with st.form("audit_form", clear_on_submit=False):

    st.subheader("1️⃣ Select Team Leader")

    team_leader = st.selectbox("Team Leader", team_list)

    # Fetch department automatically
    department = next(
        (t["department"] for t in team_data if t["team_leader"] == team_leader), ""
    )

    st.info(f"Department auto-selected: **{department}**")

    # Load consultants dynamically
    consultants = load_consultants(team_leader)
    consultant = st.selectbox("Consultant", consultants)

    case_id = st.text_input("Case Number / Client ID")

    # ----------------------------------
    # LOAD QUESTIONS FOR THIS DEPARTMENT
    # ----------------------------------
    st.subheader("2️⃣ Audit Questions")

    question_rows = load_questions(department)

    answers = {}
    critical_numbers = []

    for q in question_rows:
        q_num = q["question_number"]
        q_text = q["question_text"]

        if q["is_critical"]:
            critical_numbers.append(q_num)

        answers[f"q{q_num}"] = st.radio(
            f"{q_num}. {q_text}",
            ["Yes", "No", "NA"],
            horizontal=True
        )

    comments = st.text_area("Additional Comments")

    submitted = st.form_submit_button("Submit Audit")

    # --------------------------
    # PROCESS SUBMISSION
    # --------------------------
    if submitted:
        # Calculate score
        failed_critical = any(
            answers[f"q{num}"] == "No" for num in critical_numbers
        )

        if failed_critical:
            score = 0
        else:
            yes_count = sum(1 for a in answers.values() if a == "Yes")
            valid = sum(1 for a in answers.values() if a != "NA")
            score = round((yes_count / valid) * 100, 2) if valid else 0

        # Prepare payload
        record = {
            "team_leader": team_leader,
            "department": department,
            "consultant": consultant,
            "case_id": case_id,
            "score": score,
            "comments": comments,
            "created_at": datetime.now().isoformat()
        }
        record.update(answers)

        # Save to db
        res = supabase.table("performance_audits").insert(record).execute()

        if res.data:
            st.success(f"Audit submitted! Score = {score}%")
        else:
            st.error("Error saving audit.")
