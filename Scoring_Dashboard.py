import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# ------------------- PAGE CONFIG -------------------
st.set_page_config(
    page_title="QA Scorecard System",
    page_icon="📊",
    layout="wide"
)

# ------------------- SUPABASE CONNECTION -------------------
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ------------------- HELPER FUNCTIONS -------------------

def load_team_leaders():
    """
    Load team leaders, their departments, and consultants from the audits table
    """
    try:
        res = supabase.table("audits").select("team_leader, department, consultant").execute()
        if res.data:
            # Extract unique team leaders
            team_leaders = sorted(set([row['team_leader'] for row in res.data if row.get('team_leader')]))
            
            # Map team leaders to departments and consultants
            team_department_map = {}
            team_consultants_map = {}
            for row in res.data:
                tl = row.get('team_leader')
                dept = row.get('department')
                cons = row.get('consultant')
                
                if tl:
                    if tl not in team_department_map and dept:
                        team_department_map[tl] = dept
                    
                    if tl not in team_consultants_map:
                        team_consultants_map[tl] = set()
                    if cons:
                        team_consultants_map[tl].add(cons)
            
            # Convert consultant sets to sorted lists
            for tl in team_consultants_map:
                team_consultants_map[tl] = sorted(list(team_consultants_map[tl]))
            
            return team_leaders, team_department_map, team_consultants_map
        else:
            return [], {}, {}
    except Exception as e:
        st.error(f"Error loading team leaders: {e}")
        return [], {}, {}

def calculate_score(answers, critical_questions):
    """
    Calculate QA score, applying critical question rules
    """
    if not answers:
        return 0, 0, 0
    
    # If any critical question = "No", total score = 0
    for q_num in critical_questions:
        if answers.get(f"q{q_num}") == "No":
            return 0, 0, 0
    
    total_score = 0
    max_possible = 0
    for i in range(1, 13):
        answer = answers.get(f"q{i}", "No")
        if answer == "NA":
            continue
        max_possible += 1
        if answer == "Yes":
            total_score += 1
    score_percentage = round((total_score / max_possible) * 100, 2) if max_possible > 0 else 0
    return score_percentage, total_score, max_possible

# ------------------- LOAD TEAM LEADERS -------------------
team_leaders, TEAM_DEPARTMENT_MAP, TEAM_CONSULTANTS_MAP = load_team_leaders()

# ------------------- SCORING CARDS -------------------
# (You can copy your full SCORING_CARDS dict here; for brevity, I show just Digital Support & ARQ)
SCORING_CARDS = {
    "Digital Support": {
        "name": "Digital Support QA Scorecard",
        "questions": {
            1: "Q1: Friendly & Professional towards the customer?",
            2: "Q2: Correctly validated the customer (POPI Act)? ⚠️",
            3: "Q3: Actively listening?",
            4: "Q4: Displayed Empathy?",
            5: "Q5: Notes on every interaction?",
            6: "Q6: Hold process followed?",
            7: "Q7: Correct call transfer?",
            8: "Q8: Assisted client navigation?",
            9: "Q9: Pin/Password reset process followed?",
            10: "Q10: Branch referral correct? ⚠️",
            11: "Q11: Agent callback done?",
            12: "Q12: Self-Service promoted?"
        },
        "critical_questions": [2, 10]
    },
    "ARQ": {
        "name": "ARQ Department QA Scorecard",
        "questions": {
            1: "Q1: Documents verified in customer’s name?",
            2: "Q2: Payslip & bank info clear?",
            3: "Q3: Bank statement validated? ⚠️",
            4: "Q4: Clear notes when suspending?",
            5: "Q5: Flags confirmed before approving?",
            6: "Q6: Payslip calculation correct? ⚠️",
            7: "Q7: All incomes captured correctly?",
            8: "Q8: Documents checked for fraud?",
            9: "Q9: Application suspended correctly?",
            10: "Q10: Net2/Net3 salary correct? ⚠️",
            11: "Q11: Signatures obtained?",
            12: "Q12: ARQ checklist completed?"
        },
        "critical_questions": [3, 6, 10]
    }
}

# ------------------- SESSION STATE -------------------
if 'selected_team_leader' not in st.session_state:
    st.session_state.selected_team_leader = None
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None
if 'available_consultants' not in st.session_state:
    st.session_state.available_consultants = []

# ------------------- MAIN APP -------------------
st.title("🎯 QA Scorecard Dashboard")

# Tabs
tab1, tab2, tab3 = st.tabs(["➕ New Audit", "📋 View Audits", "📈 Analytics Dashboard"])

# ------------------- TAB 1: NEW AUDIT -------------------
with tab1:
    st.header("Submit New Audit")

    # --- Step 1: Team Leader ---
    st.subheader("Step 1: Select Team Leader")
    selected_team_leader = st.selectbox(
        "Team Leader",
        options=team_leaders,
        index=None,
        key="team_leader_widget",
        on_change=lambda: update_team_leader()
    )

    def update_team_leader():
        st.session_state.selected_team_leader = st.session_state.team_leader_widget
        if st.session_state.selected_team_leader:
            st.session_state.selected_department = TEAM_DEPARTMENT_MAP.get(st.session_state.selected_team_leader)
            st.session_state.available_consultants = TEAM_CONSULTANTS_MAP.get(st.session_state.selected_team_leader, [])
        else:
            st.session_state.selected_department = None
            st.session_state.available_consultants = []

    # --- Step 2: Department ---
    if st.session_state.selected_team_leader and st.session_state.selected_department:
        st.subheader("Step 2: Department (Auto-filled)")
        st.success(st.session_state.selected_department)

    # --- Step 3: Consultant ---
    st.subheader("Step 3: Select Consultant")
    if st.session_state.selected_team_leader and st.session_state.available_consultants:
        consultant = st.selectbox(
            "Consultant",
            options=st.session_state.available_consultants,
            index=None
        )
    else:
        st.info("No consultants available yet for this Team Leader")
        consultant = None

    # --- Step 4: Audit Details ---
    st.subheader("Step 4: Audit Details")
    client_id = st.text_input("Client ID")
    audit_date = st.date_input("Audit Date", datetime.now())
    audit_time = st.time_input("Audit Time", datetime.now().time())
    audit_datetime = datetime.combine(audit_date, audit_time)

    # --- Step 5: QA Questions ---
    if st.session_state.selected_department:
        scoring_card = SCORING_CARDS.get(st.session_state.selected_department, SCORING_CARDS["Digital Support"])
        st.subheader(f"{scoring_card['name']}")
        answers = {}
        cols = st.columns(3)
        for i in range(1, 13):
            col_idx = (i-1)%3
            with cols[col_idx]:
                q_text = scoring_card['questions'][i]
                if i in scoring_card['critical_questions']:
                    q_text += " ⚠️"
                answers[f"q{i}"] = st.radio(q_text, ["Yes","No","NA"], key=f"q{i}_{st.session_state.selected_department}")

        # Calculate score
        score_percentage, raw_score, max_score = calculate_score(answers, scoring_card['critical_questions'])
        st.metric("Total Score", f"{score_percentage}%")

    # --- Step 6: Comments ---
    comments = st.text_area("Additional Comments")

    # --- Submit Button ---
    if st.button("Submit Audit"):
        if not (selected_team_leader and consultant and client_id):
            st.error("Please complete all required fields")
        else:
            data = {
                "team_leader": selected_team_leader,
                "department": st.session_state.selected_department,
                "consultant": consultant,
                "client_id": client_id,
                "audit_date": audit_datetime.isoformat(),
                "score": score_percentage,
                "comments": comments,
                **answers
            }
            try:
                supabase.table("audits").insert(data).execute()
                st.success("✅ Audit submitted successfully!")
            except Exception as e:
                st.error(f"Error submitting audit: {e}")

# ------------------- TAB 2: VIEW AUDITS -------------------
with tab2:
    st.header("View Recent Audits")
    try:
        res = supabase.table("audits").select("*").order("audit_date", desc=True).limit(50).execute()
        if res.data:
            df = pd.DataFrame(res.data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No audits found.")
    except Exception as e:
        st.error(f"Error fetching audits: {e}")

# ------------------- TAB 3: ANALYTICS -------------------
with tab3:
    st.header("Analytics Dashboard")
    st.info("Coming soon…")
