import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# Connect to Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("Digital Support QA Scorecard")

consultants = [
    "Aobakwe Peter",
    "Daychannel Jasson",
    "Diya Ramesar",
    "Golden Raphulu",
    "Karabo Ratau",
    "Moreen Nkosi"
]

# Form
with st.form("qa_form"):
    consultant = st.selectbox("Consultant", consultants)
    team_leader = "Sipho Ramashiya"
    audit_date = datetime.now()
    client_id = st.text_input("Client ID")
    
    st.subheader("Quality Checks")

    questions = {
        "q1": "Was the consultant Friendly & Professional?",
        "q2": "Did the consultant validate the customer correctly?",
        "q3": "Actively listening?",
        "q4": "Displayed empathy?",
        "q5": "Notes captured?",
        "q6": "Hold process followed?",
        "q7": "Correct transfer?",
        "q8": "Navigation assistance correct?",
        "q9": "Pin/Password process correct?",
        "q10": "Correct branch referral?",
        "q11": "Did the agent call back the client?",
        "q12": "Was self-service promoted?"
    }

    answers = {}
    for key, q in questions.items():
        answers[key] = st.selectbox(q, ["Yes", "No", "N/A"], key=key)

    comments = st.text_area("Comments")

    submitted = st.form_submit_button("Submit Scorecard")

# Scoring function
def calculate_score(ans):
    weight = 8.33
    total = 0.0

    # Your special rule: if q2 or q10 = "No", score is 0
    if ans["q2"] == "No" or ans["q10"] == "No":
        return 0

    for v in ans.values():
        if v in ["Yes", "N/A"]:
            total += weight

    return round(total, 2)

# Save to Supabase
if submitted:
    score = calculate_score(answers)

    data = {
        "consultant": consultant,
        "team_leader": team_leader,
        "audit_date": audit_date.isoformat(),
        "client_id": client_id,
        "score": score,
        "comments": comments,
        **answers
    }

    supabase.table("scorecards").insert(data).execute()

    st.success(f"Scorecard saved! Final Score: {score}%")
