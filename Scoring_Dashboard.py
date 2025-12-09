import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# ------------------------ Page Config ------------------------
st.set_page_config(
    page_title="QA Scorecard System",
    page_icon="📊",
    layout="wide"
)

# ------------------------ Supabase Connection ------------------------
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ------------------------ DATA ------------------------
# Team Leaders → Departments
TEAM_DEPARTMENT_MAP = {
    "Sipho Ramashiya": "Digital Support",
    "Anita Maharaj": "ARQ",
    "Palesa Maponya": "ARQ",
    "Neo Thobejane": "ARQ",
    "Garth Masekele": "ARQ",
    "Sue Darrol": "DVQ (KYC)",
    "Rethabile Nkadimeng": "Assessment",
    "Theo Sambinda": "Confirmations",
    "Pacience Mashigo": "Dialler",
    "Bradlee Naidoo": "ARQ"
}

# Team Leaders → Consultants
TEAM_CONSULTANTS_MAP = {
    "Sipho Ramashiya": [
        "Aobakwe Peter","Daychannel Jasson","Diyajal Ramesar","Golden Raphulu",
        "Karabo Ratau","Moreen Nkosi","Venessa Badi"
    ],
    "Anita Maharaj": [
        "Bongani Sekese","Chriselda Silubane","Jeanerty Jiyane","Martin Kwinda",
        "Molatelo Mohlapamaswi","Nokwethaba Buthelezi","Ntudiseng Komane",
        "Qaqamba Somdakakazi","Rudzani Ratshumana","Ryle Basaviah","Shamla Shilubane"
    ],
    # ... include all other Team Leaders exactly as you have ...
}

# Department → QA Questions & Critical Questions
SCORING_CARDS = {
    "Digital Support": {
        "name": "Digital Support QA Scorecard",
        "questions": {
            1: "Q1: Was the consultant Friendly & Professional towards the customer?…i.e. Greetings, introduce yourself etc?",
            2: "Q2: Did the consultant correctly validate the customer as per the validation process? (POPI Act)? ⚠️",
            3: "Q3: Was the consultant Actively Listening to the customer? (Understanding the reason for the call)?",
            4: "Q4: Did the consultant display Empathy?",
            5: "Q5: Were notes placed on every interaction of the query/complaint?",
            6: "Q6: Was the Hold Process followed correctly?",
            7: "Q7: Was the call transferred to the appropriate Dept?",
            8: "Q8: Did the consultant assist the client to navigate correctly?",
            9: "Q9: Was the Pin/Password reset process followed?",
            10: "Q10: Was the Branch referral correct i.e. Was it warranted or could it be resolved online? ⚠️",
            11: "Q11: Did the agent call back the client?",
            12: "Q12: Was Self-Service Promoted? i.e. Self-authentication via IVR, Karabo etc?"
        },
        "critical_questions": [2, 10]
    },
    # ... Add all other departments and their full questions exactly as your original SCORING_CARDS ...
}

# ------------------------ SCORE CALCULATION ------------------------
def calculate_score(answers, critical_questions):
    # If any critical question = "No", total score = 0
    for q_num in critical_questions:
        if answers.get(f"q{q_num}") == "No":
            return 0
    total_score = sum(1 for ans in answers.values() if ans=="Yes")
    max_score = sum(1 for ans in answers.values() if ans in ["Yes","No"])
    if max_score > 0:
        return round(total_score/max_score*100,2)
    return 0

# ------------------------ SESSION STATE ------------------------
if 'selected_team_leader' not in st.session_state:
    st.session_state.selected_team_leader = None
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None
if 'available_consultants' not in st.session_state:
    st.session_state.available_consultants = []

# ------------------------ APP UI ------------------------
st.title("🎯 QA Scorecard Dashboard")

# Step 1: Team Leader
team_leader = st.selectbox("Select Team Leader", sorted(TEAM_DEPARTMENT_MAP.keys()))
if team_leader:
    st.session_state.selected_team_leader = team_leader
    st.session_state.selected_department = TEAM_DEPARTMENT_MAP[team_leader]
    st.session_state.available_consultants = TEAM_CONSULTANTS_MAP.get(team_leader, [])

# Step 2: Department (auto-filled)
if st.session_state.selected_department:
    st.info(f"Department: **{st.session_state.selected_department}**")

# Step 3: Consultant
if st.session_state.available_consultants:
    consultant = st.selectbox("Select Consultant", sorted(st.session_state.available_consultants))
else:
    consultant = None

# Step 4: Audit Date
audit_date = st.date_input("Audit Date", datetime.now())

# Step 5: Questions
answers = {}
department = st.session_state.selected_department
if department in SCORING_CARDS:
    scoring_card = SCORING_CARDS[department]
    st.subheader(scoring_card['name'])
    for i in range(1,13):
        answers[f"q{i}"] = st.radio(scoring_card['questions'][i], ["Yes","No","NA"], key=f"{department}_q{i}")

# Step 6: Additional Comments
comments = st.text_area("Additional Comments")

# Step 7: Submit
if st.button("Submit Audit"):
    if not team_leader or not consultant:
        st.error("Please select Team Leader and Consultant")
    else:
        score = calculate_score(answers, scoring_card.get('critical_questions',[]))
        data = {
            "team_leader": team_leader,
            "department": department,
            "consultant": consultant,
            "audit_date": audit_date.isoformat(),
            "score": score,
            "comments": comments,
            **answers
        }
        try:
            supabase.table("audits").insert(data).execute()
            st.success(f"✅ Audit submitted successfully! Score: {score}%")
            st.experimental_rerun()  # refresh dashboard / analytics
        except Exception as e:
            st.error(f"Error submitting audit: {e}")
