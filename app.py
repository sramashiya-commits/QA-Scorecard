import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="QA Scorecard System",
    page_icon="📊",
    layout="wide"
)

# Initialize Supabase connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ==================== EXACT DATA STRUCTURE ====================

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
        "Aobakwe Peter",
        "Daychannel Jasson",
        "Diyajal Ramesar",
        "Golden Raphulu",
        "Karabo Ratau",
        "Moreen Nkosi",
        "Venessa Badi"
    ],
    "Anita Maharaj": [
        "Bongani Sekese",
        "Chriselda Silubane",
        "Jeanerty Jiyane",
        "Martin Kwinda",
        "Molatelo Mohlapamaswi",
        "Nokwethaba Buthelezi",
        "Ntudiseng Komane",
        "Qaqamba Somdakakazi",
        "Rudzani Ratshumana",
        "Ryle Basaviah",
        "Shamla Shilubane"
    ],
    "Palesa Maponya": [
        "Kgosietsile Seleke",
        "Lerato Lepuru",
        "Matome Sekhaolelo",
        "Mpho Ramadwa",
        "Precious Tlaka",
        "Pumzile Siko",
        "Refilwe Mokgonyana",
        "Sholeen Franklin",
        "Sylvia Letsiane",
        "Thulie khumalo",
        "Vuyelwa Mayekiso"
    ],
    "Neo Thobejane": [
        "Anna Sekhaolelo",
        "Joseph Rameetse",
        "Neria Mohlapamaswi",
        "Ndifhadza Modau",
        "Nirvana Rampersad",
        "Nonkqubela Maganga",
        "Phelepine Mogaila",
        "Prince Mabuza",
        "Refiloe Mohlokoone",
        "Thando Simelane",
        "Busi Khanyeza"
    ],
    "Garth Masekele": [
        "Bandile Khumalo",
        "Basetsana Eva Masombuka",
        "Bathabile Mathunjwa",
        "Charmaine Sambo",
        "Charmaine Samuel",
        "Gadija Wilson",
        "Gladys Thembi Matshiga",
        "Emily Thandzwane",
        "Mpho Makgoba",
        "Sibonelo Phakathi",
        "Terence Dyssel"
    ],
    "Sue Darrol": [
        "Bafikile Bungane",
        "Candice Julius",
        "Constance Mashele",
        "Dimpho Gaoletswe (Maaroganye)",
        "Lindiwe Mazwe",
        "Moleboheng Mafereka",
        "Portia Mashego",
        "Tirsa Wentzel",
        "Veronicque Wilson",
        "Prince Masengane",
        "Thabiso Mokgotsi",
        "Velancia Parker"
    ],
    "Rethabile Nkadimeng": [
        "Bafedile Komane",
        "Celine Kelly",
        "Constantia Makgalia",
        "Ernest Mthembu",
        "Eulenda Mduli",
        "Londeka Mdodana",
        "Mathabo Makgopa",
        "Memory Mpofu",
        "Ndamulelo Makhado",
        "Pheladi Rameetse",
        "Margaret Matlala"
    ],
    "Theo Sambinda": [
        "Choene Mojela (Jenny)",
        "Cynthia Masiya",
        "Gracious Tshabalala",
        "Jeanette Thobane",
        "Kwena Mojela (Lilian)",
        "Martha Sangweni",
        "Metlholo Koki",
        "Thembi Hlongwane",
        "Unathi Mbuli",
        "Nokuthela Mashiloane",
        "Phikisiwe Mthembu"
    ],
    "Pacience Mashigo": [
        "Ayanda Booi",
        "Claudia Malatji",
        "Dineo Maija",
        "Kelly Leso",
        "Keseabetswe Sebatakgomo",
        "Thando Ngcanga",
        "Wiseman Zimemo",
        "Faith Sekano",
        "Marika Redelinghuys"
    ],
    "Bradlee Naidoo": [
        "Kekeletso Tokeng",
        "Kgotso Mavhunga",
        "Lerato Mongolo",
        "Maud Phosa",
        "Nwabisa Mjobo",
        "Vincent Bhengu",
        "Zwanga Nndwammbi",
        "Claudia Malatji",
        "Qondile Zulu"
    ]
}

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
    "ARQ": {
        "name": "ARQ Department QA Scorecard",
        "questions": {
            1: "Q1: Was the ARQ documentation completed accurately?",
            2: "Q2: Were all compliance checks performed correctly? ⚠️",
            3: "Q3: Did the consultant verify client eligibility?",
            4: "Q4: Was the risk assessment properly documented?",
            5: "Q5: Were all required signatures obtained?",
            6: "Q6: Was the turnaround time within SLA?",
            7: "Q7: Were follow-up actions clearly defined?",
            8: "Q8: Was the client informed of next steps?",
            9: "Q9: Were all supporting documents attached?",
            10: "Q10: Was the final approval/rejection communicated properly? ⚠️",
            11: "Q11: Was the ARQ checklist fully completed?",
            12: "Q12: Was data entry accurate in the system?"
        },
        "critical_questions": [2, 10]
    },
    "DVQ (KYC)": {
        "name": "DVQ (KYC) Department QA Scorecard",
        "questions": {
            1: "Q1: Was the KYC documentation thoroughly reviewed?",
            2: "Q2: Were all identity verification steps completed? ⚠️",
            3: "Q3: Was the customer risk rating correctly assessed?",
            4: "Q4: Were PEP and sanctions checks performed?",
            5: "Q5: Was the source of funds verified?",
            6: "Q6: Were all required documents collected?",
            7: "Q7: Was the KYC file properly documented?",
            8: "Q8: Were any red flags properly escalated?",
            9: "Q9: Was the KYC review completed within SLA?",
            10: "Q10: Were compliance regulations fully followed? ⚠️",
            11: "Q11: Was the customer properly informed of requirements?",
            12: "Q12: Was the KYC file quality checked?"
        },
        "critical_questions": [2, 10]
    },
    "Assessment": {
        "name": "Assessment Department QA Scorecard",
        "questions": {
            1: "Q1: Was the assessment scope clearly defined?",
            2: "Q2: Were assessment criteria applied correctly? ⚠️",
            3: "Q3: Was the assessment thorough and complete?",
            4: "Q4: Were findings properly documented?",
            5: "Q5: Were recommendations clear and actionable?",
            6: "Q6: Was the assessment delivered on time?",
            7: "Q7: Was client feedback incorporated?",
            8: "Q8: Were risks properly evaluated?",
            9: "Q9: Was the assessment report professional?",
            10: "Q10: Were follow-up assessments scheduled if needed? ⚠️",
            11: "Q11: Was the assessment methodology appropriate?",
            12: "Q12: Were all stakeholders properly informed?"
        },
        "critical_questions": [2, 10]
    },
    "Confirmations": {
        "name": "Confirmations Department QA Scorecard",
        "questions": {
            1: "Q1: Were confirmations sent within agreed timeframe?",
            2: "Q2: Was confirmation data 100% accurate? ⚠️",
            3: "Q3: Were all required parties included?",
            4: "Q4: Was the confirmation method appropriate?",
            5: "Q5: Were follow-ups documented?",
            6: "Q6: Were discrepancies properly escalated?",
            7: "Q7: Was confirmation tracking updated in system?",
            8: "Q8: Were client preferences followed?",
            9: "Q9: Were confirmations properly archived?",
            10: "Q10: Was feedback from confirmations actioned? ⚠️",
            11: "Q11: Were all compliance requirements met?",
            12: "Q12: Was the confirmation process efficient?"
        },
        "critical_questions": [2, 10]
    },
    "Dialler": {
        "name": "Dialler Department QA Scorecard",
        "questions": {
            1: "Q1: Was the call script followed correctly?",
            2: "Q2: Were calling lists managed properly? ⚠️",
            3: "Q3: Was call disposition accurately recorded?",
            4: "Q4: Were customer objections handled professionally?",
            5: "Q5: Was the call volume target achieved?",
            6: "Q6: Were callback commitments honored?",
            7: "Q7: Was the dialler system used efficiently?",
            8: "Q8: Were customer data protection rules followed?",
            9: "Q9: Was the call quality maintained throughout?",
            10: "Q10: Were leads properly qualified and escalated? ⚠️",
            11: "Q11: Was the customer experience positive?",
            12: "Q12: Were all compliance requirements met during calls?"
        },
        "critical_questions": [2, 10]
    }
}

def calculate_score(answers, critical_questions):
    if not answers:
        return 0, 0, 0
    
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
    
    if max_possible > 0:
        score_percentage = round((total_score / max_possible) * 100, 2)
    else:
        score_percentage = 0
    
    return score_percentage, total_score, max_possible

# Initialize session state
if 'selected_team_leader' not in st.session_state:
    st.session_state.selected_team_leader = None
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False

# Centered Main Title
st.markdown("<h1 style='text-align: center;'>🏢 Multi-Department QA Scorecard System</h1>", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["➕ New Audit", "📋 View Audits", "📈 Analytics Dashboard"])

with tab1:
    st.markdown("<h2 style='text-align: center;'>New QA Audit</h2>", unsafe_allow_html=True)
    
    if st.session_state.get('form_submitted', False):
        st.success("✅ Audit submitted successfully!")
        
        col_success1, col_success2, col_success3 = st.columns([1, 2, 1])
        with col_success2:
            if st.button("🎯 Score Another Person", type="primary", use_container_width=True):
                st.session_state.form_submitted = False
                st.session_state.selected_team_leader = None
                st.rerun()
    
    with st.form("audit_form", clear_on_submit=True):
        st.subheader("👥 Team Information")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Team Leader dropdown
            team_leaders = list(TEAM_DEPARTMENT_MAP.keys())
            team_leader = st.selectbox(
                "Team Leader *",
                team_leaders,
                index=None,
                placeholder="Select team leader...",
                key="team_leader_select"
            )
            
            # Update session state when team leader changes
            if team_leader:
                st.session_state.selected_team_leader = team_leader
            elif team_leader is None:
                st.session_state.selected_team_leader = None
        
        with col2:
            # Department (auto-filled based on team leader)
            if st.session_state.selected_team_leader:
                department = TEAM_DEPARTMENT_MAP[st.session_state.selected_team_leader]
                # Use st.text to display department (not text_input)
                st.text("Department *")
                st.info(f"**{department}**")
            else:
                st.text("Department *")
                st.warning("Select team leader first")
                department = None
        
        with col3:
            # Consultant dropdown (dynamic based on team leader)
            if st.session_state.selected_team_leader:
                consultants = TEAM_CONSULTANTS_MAP[st.session_state.selected_team_leader]
                consultant = st.selectbox(
                    "Consultant *",
                    sorted(consultants),
                    index=None,
                    placeholder="Select consultant...",
                    key=f"consultant_select_{st.session_state.selected_team_leader}"
                )
            else:
                st.selectbox(
                    "Consultant *",
                    ["Select team leader first"],
                    disabled=True,
                    key="consultant_disabled"
                )
                consultant = None
        
        st.divider()
        
        # Client Information
        st.subheader("📄 Client Information")
        col4, col5 = st.columns(2)
        
        with col4:
            client_id = st.text_input("Client ID *", placeholder="CLIENT-001", key="client_id")
        with col5:
            audit_date = st.date_input("Audit Date *", value=datetime.now(), key="audit_date")
        
        st.divider()
        
        # Show scoring card based on department
        if st.session_state.selected_team_leader and department:
            scoring_card = SCORING_CARDS.get(department, SCORING_CARDS["Digital Support"])
            
            st.subheader(f"📋 {scoring_card['name']}")
            st.info(f"**Team:** {st.session_state.selected_team_leader} | **Department:** {department}")
            
            answers = {}
            
            # Create 3 columns for the questions
            col_q1, col_q2, col_q3 = st.columns(3)
            columns = [col_q1, col_q2, col_q3]
            col_idx = 0
            
            for i in range(1, 13):
                with columns[col_idx]:
                    question_text = scoring_card['questions'][i]
                    is_critical = i in scoring_card['critical_questions']
                    
                    if is_critical:
                        question_text += " ⚠️"
                    
                    answer = st.radio(
                        question_text,
                        ["Yes", "No", "NA"],
                        horizontal=False,
                        key=f"q{i}_{department}_{st.session_state.selected_team_leader}",
                        index=None
                    )
                    answers[f"q{i}"] = answer
                    
                    if is_critical:
                        st.caption("⚠️ **CRITICAL:** 'No' = Total score = 0%")
                
                col_idx = (col_idx + 1) % 3
            
            # Calculate score immediately
            score_percentage, raw_score, max_score = calculate_score(answers, scoring_card['critical_questions'])
            
            st.divider()
            st.warning("⚠️ **CRITICAL SCORING RULE:** If any critical question is 'No', the total score will be 0%")
            
            col6, col7, col8 = st.columns(3)
            with col6:
                critical_failed = any(answers.get(f"q{q}") == "No" for q in scoring_card['critical_questions'])
                if critical_failed:
                    st.error(f"❌ Total Score: {score_percentage}%")
                    st.caption("(Critical question = 'No')")
                else:
                    st.metric("Total Score", f"{score_percentage}%")
            
            with col7:
                if critical_failed:
                    st.metric("Raw Score", "0/0")
                    st.caption("Critical failure")
                else:
                    st.metric("Raw Score", f"{raw_score}/{max_score}")
            
            with col8:
                if critical_failed:
                    st.error("❌ FAIL - Critical Error")
                elif score_percentage >= 85:
                    st.success("Excellent ✓")
                elif score_percentage >= 70:
                    st.warning("Good ⚠️")
                else:
                    st.error("Needs Improvement ✗")
            
            # Show critical question status
            for q_num in scoring_card['critical_questions']:
                if answers.get(f"q{q_num}") == "No":
                    st.error(f"**❌ Q{q_num} FAIL:** Critical requirement not met")
        else:
            st.info("👈 **Please select a Team Leader above to see the scoring card**")
            answers = {}
            score_percentage = 0
            critical_failed = False
        
        st.divider()
        st.subheader("💬 Additional Information")
        comments = st.text_area("Additional Comments", placeholder="Enter any additional comments here...", key="comments")
        
        # Submit button
        col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
        with col_submit2:
            submitted = st.form_submit_button("📥 Submit Audit", type="primary", use_container_width=True)
        
        if submitted:
            if not team_leader:
                st.error("Please select a Team Leader")
            elif not consultant:
                st.error("Please select a Consultant")
            elif not client_id:
                st.error("Please enter a Client ID")
            elif not all(answers.values()):
                st.error("Please answer all questions")
            else:
                department = TEAM_DEPARTMENT_MAP[team_leader]
                
                data = {
                    "consultant": consultant,
                    "team_leader": team_leader,
                    "department": department,
                    "client_id": client_id,
                    "audit_date": audit_date.isoformat(),
                    "score": score_percentage,
                    "comments": comments,
                    **answers
                }
                
                try:
                    response = supabase.table("audits").insert(data).execute()
                    st.session_state.last_submitted_data = data
                    st.session_state.form_submitted = True
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error submitting audit: {e}")

with tab2:
    st.markdown("<h2 style='text-align: center;'>View Audits</h2>", unsafe_allow_html=True)
    
    try:
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            if 'department' not in df.columns:
                df['department'] = 'Not Assigned'
            
            # Calculate metrics
            total_audits = len(df)
            avg_score = df['score'].mean()
            critical_failures = 0
            if all(col in df.columns for col in ['q2', 'q10']):
                critical_failures = len(df[(df['q2'] == 'No') | (df['q10'] == 'No')])
            
            # Show metrics
            cols = st.columns(5)
            cols[0].metric("Total Audits", total_audits)
            cols[1].metric("Average Score", f"{avg_score:.1f}%")
            cols[2].metric("Critical Failures", critical_failures)
            pass_rate = ((total_audits - critical_failures) / total_audits * 100) if total_audits > 0 else 0
            cols[3].metric("Pass Rate", f"{pass_rate:.1f}%")
            cols[4].metric("Departments", df['department'].nunique())
            
            # Dataframe
            display_columns = ['id', 'audit_date', 'department', 'team_leader', 'consultant', 'client_id', 'score']
            for col in ['q2', 'q10', 'comments']:
                if col in df.columns:
                    display_columns.append(col)
            
            st.dataframe(
                df[display_columns],
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "audit_date": "Date",
                    "department": "Department",
                    "team_leader": "Team Lead",
                    "consultant": "Consultant",
                    "client_id": "Client ID",
                    "score": st.column_config.NumberColumn("Score", format="%.1f %%"),
                }
            )
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download All Audits as CSV",
                data=csv,
                file_name="audits.csv",
                mime="text/csv"
            )
            
        else:
            st.info("No audits found. Submit your first audit above!")
            
    except Exception as e:
        st.error(f"Error fetching audits: {e}")

with tab3:
    st.markdown("<h2 style='text-align: center;'>📈 Analytics Dashboard</h2>", unsafe_allow_html=True)
    
    try:
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        
        if not response.data:
            st.info("No audit data available for analytics. Submit some audits first!")
        else:
            df = pd.DataFrame(response.data)
            
            if 'department' not in df.columns:
                df['department'] = 'Not Assigned'
            
            # Convert dates
            df['audit_date'] = pd.to_datetime(df['audit_date'])
            df['month_name'] = df['audit_date'].dt.strftime('%B %Y')
            df['day'] = df['audit_date'].dt.date
            
            # Filters
            st.subheader("🔍 Filter Analytics Data")
            
            col_filter1, col_filter2, col_filter3 = st.columns(3)
            
            with col_filter1:
                all_departments = sorted(df['department'].unique())
                selected_departments = st.multiselect(
                    "Select Department(s)",
                    options=all_departments,
                    default=all_departments
                )
            
            with col_filter2:
                all_team_leaders = sorted(df['team_leader'].unique())
                selected_team_leaders = st.multiselect(
                    "Select Team Leader(s)",
                    options=all_team_leaders,
                    default=all_team_leaders
                )
            
            with col_filter3:
                all_months = sorted(df['month_name'].unique(), reverse=True)
                selected_months = st.multiselect(
                    "Select Month(s)",
                    options=all_months,
                    default=all_months[:3] if len(all_months) >= 3 else all_months
                )
            
            # Apply filters
            filtered_df = df.copy()
            
            if selected_departments:
                filtered_df = filtered_df[filtered_df['department'].isin(selected_departments)]
            if selected_team_leaders:
                filtered_df = filtered_df[filtered_df['team_leader'].isin(selected_team_leaders)]
            if selected_months:
                filtered_df = filtered_df[filtered_df['month_name'].isin(selected_months)]
            
            st.info(f"📊 **Showing {len(filtered_df)} out of {len(df)} audits**")
            
            if len(filtered_df) == 0:
                st.warning("No data matches your filters.")
                st.stop()
            
            # Metrics
            total_audits_filtered = len(filtered_df)
            avg_score_filtered = filtered_df['score'].mean()
            critical_failures_filtered = 0
            if all(col in filtered_df.columns for col in ['q2', 'q10']):
                critical_failures_filtered = len(filtered_df[(filtered_df['q2'] == 'No') | (filtered_df['q10'] == 'No')])
            pass_rate_filtered = ((total_audits_filtered - critical_failures_filtered) / total_audits_filtered * 100) if total_audits_filtered > 0 else 0
            
            # Display metrics
            st.subheader("📊 Key Performance Indicators")
            kpi_cols = st.columns(4)
            kpi_cols[0].metric("Total Audits", total_audits_filtered)
            kpi_cols[1].metric("Average Score", f"{avg_score_filtered:.1f}%")
            kpi_cols[2].metric("Pass Rate", f"{pass_rate_filtered:.1f}%")
            kpi_cols[3].metric("Critical Failures", critical_failures_filtered, delta_color="inverse")
            
            # Department Performance
            st.subheader("🏢 Department Performance")
            if len(filtered_df) > 0:
                dept_scores = filtered_df.groupby('department').agg({
                    'score': 'mean',
                    'id': 'count'
                }).round(1).reset_index()
                dept_scores.columns = ['Department', 'Avg Score', 'Audit Count']
                
                col_dept1, col_dept2 = st.columns(2)
                
                with col_dept1:
                    fig1 = go.Figure(go.Bar(
                        x=dept_scores['Avg Score'],
                        y=dept_scores['Department'],
                        orientation='h',
                        text=dept_scores['Avg Score'].astype(str) + '%',
                        textposition='outside',
                        marker_color='cornflowerblue'
                    ))
                    fig1.update_layout(height=400, xaxis_title="Average Score (%)", yaxis_title="Department")
                    st.plotly_chart(fig1, use_container_width=True)
                
                with col_dept2:
                    st.dataframe(
                        dept_scores,
                        use_container_width=True,
                        hide_index=True
                    )
            
            # Export
            st.divider()
            csv_filtered = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Filtered Data",
                data=csv_filtered,
                file_name=f"filtered_audits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
            
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
