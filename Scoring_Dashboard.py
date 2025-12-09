import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# =================== STREAMLIT PAGE CONFIG ===================
st.set_page_config(
    page_title="QA Scorecard System",
    page_icon="📊",
    layout="wide"
)

# =================== SUPABASE CONNECTION ===================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# =================== DATA STRUCTURES ===================
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

TEAM_CONSULTANTS_MAP = {
    "Sipho Ramashiya": [
        "Aobakwe Peter", "Daychannel Jasson", "Diyajal Ramesar",
        "Golden Raphulu", "Karabo Ratau", "Moreen Nkosi"
    ],
    "Anita Maharaj": [
        "Bongani Sekese", "Chriselda Silubane", "Jeanerty Jiyane",
        "Martin Kwinda", "Molatelo Mohlapamaswi", "Nokwethaba Buthelezi",
        "Ntudiseng Komane", "Qaqamba Somdakakazi", "Rudzani Ratshumana",
        "Ryle Basaviah", "Shamla Shilubane"
    ],
    "Palesa Maponya": [
        "Kgosietsile Seleke", "Lerato Lepuru", "Matome Sekhaolelo",
        "Mpho Ramadwa", "Precious Tlaka", "Pumzile Siko",
        "Refilwe Mokgonyana", "Sholeen Franklin", "Sylvia Letsiane",
        "Thulie Khumalo", "Vuyelwa Mayekiso"
    ],
    "Neo Thobejane": [ 
        "Anna Sekhaolelo", "Joseph Rameetse", "Neria Mohlapamaswi", 
        "Ndifhadza Modau", "Nirvana Rampersad", "Nonkqubela Maganga", 
        "Phelepine Mogaila", "Prince Mabuza", "Refiloe Mohlokoone", 
        "Thando Simelane", "Busi Khanyeza" 
    ], 
    "Garth Masekele": [ 
        "Bandile Khumalo", "Basetsana Eva Masombuka", "Bathabile Mathunjwa", 
        "Charmaine Sambo", "Charmaine Samuel", "Gadija Wilson", 
        "Gladys Thembi Matshiga", "Emily Thandzwane", "Mpho Makgoba", 
        "Sibonelo Phakathi", "Terence Dyssel" 
    ],
    "Sue Darrol": [
        "Bafikile Bungane", "Candice Julius", "Constance Mashele", 
        "Dimpho Gaoletswe (Maaroganye)", "Lindiwe Mazwe", 
        "Moleboheng Mafereka", "Portia Mashego", "Tirsa Wentzel", 
        "Veronicque Wilson", "Prince Masengane", "Thabiso Mokgotsi", 
        "Velancia Parker"
    ],
    "Rethabile Nkadimeng": [
        "Bafedile Komane", "Celine Kelly", "Constantia Makgalia", 
        "Ernest Mthembu", "Eulenda Mduli", "Londeka Mdodana", 
        "Mathabo Makgopa", "Memory Mpofu", "Ndamulelo Makhado", 
        "Pheladi Rameetse", "Margaret Matlala" 
    ],
    "Theo Sambinda": [ 
        "Choene Mojela (Jenny)", "Cynthia Masiya", "Gracious Tshabalala", 
        "Jeanette Thobane", "Kwena Mojela (Lilian)", "Martha Sangweni", 
        "Metlholo Koki", "Thembi Hlongwane", "Unathi Mbuli", 
        "Nokuthela Mashiloane", "Phikisiwe Mthembu"
    ], 
    "Pacience Mashigo": [ 
        "Ayanda Booi", "Claudia Malatji", "Dineo Maija", 
        "Kelly Leso", "Keseabetswe Sebatakgomo", 
        "Thando Ngcanga", "Wiseman Zimemo", 
        "Faith Sekano", "Marika Redelinghuys"
    ], 
    "Bradlee Naidoo": [ 
        "Kekeletso Tokeng", "Kgotso Mavhunga", 
        "Lerato Mongolo", "Maud Phosa", "Nwabisa Mjobo", 
        "Vincent Bhengu", "Zwanga Nndwammbi", 
        "Claudia Malatji", "Qondile Zulu"
    ]
}
    
    # ... add other team leader consultants similarly
}

SCORING_CARDS = {
    "Digital Support": {
        "name": "Digital Support QA Scorecard",
        "questions": {
            1: "Was the consultant Friendly & Professional towards the customer?",
            2: "Did the consultant correctly validate the customer? (POPI Act)",
            3: "Was the consultant Actively Listening to the customer?",
            4: "Did the consultant display Empathy?",
            5: "Were notes placed on every interaction?",
            6: "Was the Hold Process followed correctly?",
            7: "Was the call transferred to the appropriate Dept?",
            8: "Did the consultant assist the client to navigate correctly?",
            9: "Was the Pin/Password reset process followed?",
            10: "Was the Branch referral correct?",
            11: "Did the agent call back the client?",
            12: "Was Self-Service Promoted?"
        },
        "critical_questions": [2, 10]
    },
    "ARQ": {
        "name": "ARQ Department QA Scorecard",
        "questions": {
            1: "Were all documents verified to be in the customers name?",
            2: "Was the payslip and bank statement information clear and visible?",
            3: "Was the bank statement validated with OBS/SkyQR/FNB Website?",
            4: "Did the agent write clear notes when suspending the application?",
            5: "Did the agent confirm flags before approving?",
            6: "Was income captured correctly?",
            7: "Was all incomes captured correctly according to the payslip?",
            8: "Were the documents checked for fraudulent indications?",
            9: "Was the application suspended correctly?",
            10: "Was Net2/Net3 salary captured correctly?",
            11: "Were all required signatures obtained?",
            12: "Was the ARQ checklist fully completed?"
        },
        "critical_questions": [3, 6, 10]
    },
    "DVQ (KYC)": {
        "name": "DVQ (KYC) Department QA Scorecard",
        "questions": {
            1: "Were the customers names and surnames captured?",
            2: "Was the application approved/suspended correctly?",
            3: "Was the ID Document run through Sprint Hive?",
            4: "Does the Sprint Hive outcome and suspension reason match?",
            5: "Were there clear notes made when suspending for additional documents?",
            6: "Bank Statements: 3 salary deposits verified?",
            7: "OBS Banks: consultant reference checked Sybrin?",
            8: "Were all documents verified to be in the customers name?",
            9: "Was the employment confirmation letter requested?",
            10: "Did the agent refer the application correctly?",
            11: "Was the payslip and bank statement information clear?",
            12: "Were any red flags properly escalated?"
        },
        "critical_questions": [3, 4, 7]
    },
    "Assessment": { 
        "name": "Assessment Department QA Scorecard", 
        "questions": { 
            1: "Q1: Was the assessment scope clearly defined?", 
            2: "Q2: Were assessment criteria applied correctly?", 
            3: "Q3: Was the assessment thorough and complete?", 
            4: "Q4: Were findings properly documented?", 
            5: "Q5: Were recommendations clear and actionable?", 
            6: "Q6: Was the assessment delivered on time?", 
            7: "Q7: Was client feedback incorporated?", 
            8: "Q8: Were risks properly evaluated?", 
            9: "Q9: Was the assessment report professional?", 
            10: "Q10: Were follow-up assessments scheduled if needed?", 
            11: "Q11: Was the assessment methodology appropriate?", 
            12: "Q12: Were all stakeholders properly informed?" 
        }, 
        "critical_questions": []
    },
    "Confirmations": { 
        "name": "Confirmations Department QA Scorecard", 
        "questions": { 
            1: "Q1: Did the Agent validate clients ID and employee numbers to HR?", 
            2: "Q2: Did the Agent verify client's employment status i.e. perm or temp?", 
            3: "Q3: Did the Agent verify client company name?", 
            4: "Q4: Did the Agent verify client's employment dates?", 
            5: "Q5: Did the Agent verify client's salary payment dates including when they get paid when it falls on weekend and public holiday?", 
            6: "Q6: Did the Agent verify if there is any possible retrenchment within the company?", 
            7: "Q7: Did the Agent obtain HR/manager/payroll personnel name and surname explaining the significance in obtain the particulars?", 
            8: "Q8: Did the agent confirm the company email address?", 
            9: "Q9: Were follow-ups documented?", 
            10: "Q10: Was feedback from confirmations actioned?", 
            11: "Q11: Were all compliance requirements met?", 
            12: "Q12: Was the confirmation process efficient?" 
        }, 
        "critical_questions": []
    },
    "Dialler": { 
        "name": "Dialler Department QA Scorecard", 
        "questions": { 
            1: "Q1: Regulatory statement (African is a financial services provider…) ⚠️", 
            2: "Q2: ID & V (authenticate the customer correctly) ⚠️", 
            3: "Q3: Did the consultant speak clear, audible and polite tone/accent without interruptions?", 
            4: "Q4: Did the consultant inform/assist with different platforms of sending documents?", 
            5: "Q5: Did the consultant confirm receival of documents?", 
            6: "Q6: Did the consultant confirm and communicate clearly what is outstanding? Referred to the notes on Exactus?", 
            7: "Q7: Defining what will be the next steps to the application?", 
            8: "Q8: How the customer can check on the status of their application?", 
            9: "Q9: Was call disposition accurately recorded?", 
           10: "Q10: Were customer objections handled professionally?", 
           11: "Q11: Was the customer experience positive?", 
           12: "Q12: Were all compliance requirements met during calls?" 
        }, 
        "critical_questions": [1, 2]
    }
    # Add other departments similarly...
}

# =================== HELPER FUNCTIONS ===================
def calculate_score(answers, critical_questions):
    """ Calculate total score; total = 0 if any critical = 'No' """
    for q in critical_questions:
        if answers.get(f"q{q}") == "No":
            return 0
    total = 0
    max_possible = 0
    for i in range(1, 13):
        ans = answers.get(f"q{i}", "NA")
        if ans == "NA":
            continue
        max_possible += 1
        if ans == "Yes":
            total += 1
    return round((total / max_possible) * 100, 2) if max_possible else 0

# =================== SESSION STATE ===================
if 'selected_team_leader' not in st.session_state:
    st.session_state.selected_team_leader = None
if 'selected_department' not in st.session_state:
    st.session_state.selected_department = None
if 'available_consultants' not in st.session_state:
    st.session_state.available_consultants = []

# =================== APP LAYOUT ===================
st.title("🎯 QA Scoring Dashboard")

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ New Audit", 
    "📋 View Audits", 
    "📈 Analytics", 
    "⚙️ Settings"
])

# ------------------- TAB 1: NEW AUDIT -------------------
with tab1:
    st.header("New Audit")

    # Step 1: Team Leader selection
    team_leader = st.selectbox(
        "Select Team Leader",
        list(TEAM_DEPARTMENT_MAP.keys()),
        index=0,
        key="team_leader_widget"
    )
    if team_leader:
        st.session_state.selected_team_leader = team_leader
        st.session_state.selected_department = TEAM_DEPARTMENT_MAP.get(team_leader)
        st.session_state.available_consultants = TEAM_CONSULTANTS_MAP.get(team_leader, [])

        st.subheader("Department")
        st.success(st.session_state.selected_department)

        # Step 2: Consultant
        if st.session_state.available_consultants:
            consultant = st.selectbox(
                "Select Consultant",
                sorted(st.session_state.available_consultants),
                key="consultant_select"
            )
        else:
            consultant = None
            st.warning("No consultants found for this team leader.")

        # Step 3: Audit Info
        client_id = st.text_input("Client ID")
        audit_date = st.date_input("Audit Date", value=datetime.now())
        audit_time = st.time_input("Audit Time", value=datetime.now().time())
        audit_datetime = datetime.combine(audit_date, audit_time)

        # Step 4: Scoring Questions
        department = st.session_state.selected_department
        scoring_card = SCORING_CARDS.get(department)
        answers = {}
        if scoring_card:
            st.subheader(f"{scoring_card['name']}")
            for i in range(1, 13):
                answers[f"q{i}"] = st.radio(
                    scoring_card['questions'][i],
                    ["Yes", "No", "NA"],
                    key=f"{department}_q{i}"
                )

        # Step 5: Comments
        comments = st.text_area("Additional Comments")

        # Step 6: Submit
        if st.button("Submit Audit"):
            if not (team_leader and consultant and client_id and scoring_card):
                st.error("Please complete all required fields")
            else:
                score = calculate_score(answers, scoring_card.get('critical_questions', []))
                data = {
                    "team_leader": team_leader,
                    "department": department,
                    "consultant": consultant,
                    "client_id": client_id,
                    "audit_date": audit_datetime.isoformat(),
                    "score": score,
                    "comments": comments,
                    **answers
                }
                try:
                    supabase.table("audits").insert(data).execute()
                    st.success(f"Audit submitted successfully! Score: {score}%")
                except Exception as e:
                    st.error(f"Error submitting audit: {e}")

# ------------------- TAB 2: VIEW AUDITS -------------------
with tab2:
    st.header("View Audits")
    try:
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        if response.data:
            df = pd.DataFrame(response.data)
            st.dataframe(df)
        else:
            st.info("No audits yet.")
    except Exception as e:
        st.error(f"Error fetching audits: {e}")

# ------------------- TAB 3: ANALYTICS -------------------
with tab3:
    st.header("Analytics Dashboard")
    st.info("Analytics content goes here (you already have this implemented)")

# ------------------- TAB 4: SETTINGS -------------------
with tab4:
    st.header("Settings")
    st.info("Settings content goes here (you already have this implemented)")
