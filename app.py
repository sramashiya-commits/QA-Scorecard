# app.py
import streamlit as st
import pandas as pd
from datetime import datetime
import os

# -----------------------
# Config / Constants
# -----------------------
st.set_page_config(page_title="Digital Support Audit Scorecard", layout="wide")

CONSULTANTS = [
    "Aobakwe Peter",
    "Daychannel Jasson",
    "Diya Ramesar",
    "Golden Raphulu",
    "Karabo Ratau",
    "Moreen Nkosi"
]

TEAM_LEADER = "Sipho Ramashiya"
CSV_PATH = "qa_scores.csv"  # where records are stored (in the app folder)

# weights as decimals (sum approx 1.0)
WEIGHTS = {
    1: 0.0833,  # Friendly & Professional
    2: 0.0833,  # Validation (POPI)
    3: 0.0833,  # Actively listening
    4: 0.0833,  # Empathy
    5: 0.0833,  # Notes placed
    6: 0.0833,  # Hold process
    7: 0.0833,  # Transfer correct dept
    8: 0.0833,  # Assist navigate
    9: 0.0833,  # Pin/Password reset
    10: 0.0837, # Branch referral (slightly different)
    11: 0.0833, # Agent called back
    12: 0.0833  # Self-service promoted
}

# -----------------------
# Helper functions
# -----------------------
def calc_weights(answers):
    """Return list of awarded weight decimals for each question index (1-based)."""
    awarded = []
    for i, ans in enumerate(answers, start=1):
        w = WEIGHTS.get(i, 0)
        if ans in ["Yes", "N/A"]:
            awarded.append(w)
        else:
            awarded.append(0.0)
    return awarded

def compute_total_score(answers):
    """
    Implements special rules from your Excel:
    - If Validation (Q2) == "No" OR Branch referral (Q10) == "No", total = 0
    - If Validation (Q2) == "N/A", total = 0.125 (12.5%)
    - Otherwise, sum the awarded weights
    """
    q2 = answers[1]   # index 1 -> question 2
    q10 = answers[9]  # index 9 -> question 10

    if q2 == "No" or q10 == "No":
        return 0.0
    if q2 == "N/A":
        return 0.125  # 12.5% as decimal
    # normal sum
    return sum(calc_weights(answers))

def ensure_csv_exists(path):
    if not os.path.exists(path):
        df = pd.DataFrame(columns=[
            "timestamp", "employee", "team_leader", "audit_date", "client_id",
            "score_pct", "score_decimal", "comments"
        ] + [f"q{i}" for i in range(1,13)] )
        df.to_csv(path, index=False)

def append_record(path, record: dict):
    ensure_csv_exists(path)
    df = pd.read_csv(path)
    df = pd.concat([df, pd.DataFrame([record])], ignore_index=True)
    df.to_csv(path, index=False)

# -----------------------
# UI: Title & Layout
# -----------------------
st.title("Digital Support Audit — Online QA Scorecard")
st.markdown("**Admin:** Only you (Sipho) have admin controls. This app shows the final score after submission.")

left, right = st.columns([2,1])

with left:
    # Form
    with st.form("score_form"):
        st.subheader("Scorecard input")

        col1, col2 = st.columns([2,3])
        with col1:
            employee = st.selectbox("Employee (Consultant)", CONSULTANTS)
            team_leader_display = st.text_input("Team Leader", TEAM_LEADER, disabled=True)
            audit_date = st.date_input("Audit Date", datetime.now().date())
            client_id = st.text_input("Client ID", value="")
            comments = st.text_area("Comments", height=100, placeholder="Type optional comments here...")
        with col2:
            st.info("Scoring: choose Yes / No / N/A for each criterion")
            st.write("")  # spacer

        st.markdown("---")
        # Questions: keep order matching your spreadsheet
        q1 = st.selectbox("1) Was the consultant Friendly & Professional towards the customer (greetings, introduce yourself etc)?",
                          ["Yes", "No", "N/A"], key="q1")
        q2 = st.selectbox("2) Did the consultant correctly validate the customer as per the validation process? (POPI Act)",
                          ["Yes", "No", "N/A"], key="q2")
        q3 = st.selectbox("3) Was the consultant Actively Listening to the customer? (Understanding the reason for the call)",
                          ["Yes", "No", "N/A"], key="q3")
        q4 = st.selectbox("4) Did the consultant display Empathy?",
                          ["Yes", "No", "N/A"], key="q4")
        q5 = st.selectbox("5) Were notes placed on every interaction of the query/complaint?",
                          ["Yes", "No", "N/A"], key="q5")
        q6 = st.selectbox("6) Was the Hold Process followed correctly?",
                          ["Yes", "No", "N/A"], key="q6")
        q7 = st.selectbox("7) Was the call transferred to the appropriate Department?",
                          ["Yes", "No", "N/A"], key="q7")
        q8 = st.selectbox("8) Did the consultant assist the client to navigate correctly?",
                          ["Yes", "No", "N/A"], key="q8")
        q9 = st.selectbox("9) Was the Pin/Password reset process followed?",
                          ["Yes", "No", "N/A"], key="q9")
        q10 = st.selectbox("10) Was the Branch referral correct i.e. Was it warranted or could it be resolved online?",
                          ["Yes", "No", "N/A"], key="q10")
        q11 = st.selectbox("11) Did the agent call back the client?",
                          ["Yes", "No", "N/A"], key="q11")
        q12 = st.selectbox("12) Was Self-Service Promoted? i.e. Self-authentication via IVR, Karabo etc",
                          ["Yes", "No", "N/A"], key="q12")

        submit = st.form_submit_button("Calculate & Save")

    # End form

    # After submit: compute and show
    if submit:
        answers = [q1, q2, q3, q4, q5, q6, q7, q8, q9, q10, q11, q12]
        total_decimal = compute_total_score(answers)  # decimal 0..1 (or 0.125 etc)
        score_pct = total_decimal * 100

        # Prepare record and save
        record = {
            "timestamp": datetime.now().isoformat(),
            "employee": employee,
            "team_leader": TEAM_LEADER,
            "audit_date": str(audit_date),
            "client_id": client_id,
            "score_pct": round(score_pct, 2),
            "score_decimal": total_decimal,
            "comments": comments
        }
        # add questions
        for i, a in enumerate(answers, start=1):
            record[f"q{i}"] = a

        append_record(CSV_PATH, record)

        # Show final score on-screen (as requested)
        st.success(f"Saved. Final Score for {employee}: **{score_pct:.2f}%**")
        st.write("Score breakdown (awarded weights):")
        awarded = calc_weights(answers)
        breakdown = pd.DataFrame({
            "question": [f"q{i}" for i in range(1,13)],
            "answer": answers,
            "weight_awarded_decimal": awarded
        })
        breakdown["weight_awarded_pct"] = breakdown["weight_awarded_decimal"] * 100
        st.dataframe(breakdown.style.format({"weight_awarded_pct": "{:.2f}"}), height=300)

with right:
    st.subheader("Quick admin / Data")
    ensure_csv_exists(CSV_PATH)
    df = pd.read_csv(CSV_PATH)
    st.write(f"Total submissions: {len(df)}")
    if len(df) > 0:
        # show latest 5
        st.markdown("Latest submissions")
        st.dataframe(df.sort_values("timestamp", ascending=False).head(10))

    # download full CSV
    csv_bytes = open(CSV_PATH, "rb").read()
    st.download_button("Download full CSV", data=csv_bytes, file_name="qa_scores.csv", mime="text/csv")

st.markdown("---")
st.info("Notes & next steps: If you prefer Google Sheets or Supabase as the backing store, I can show you the minimal changes to swap CSV for cloud storage.")
