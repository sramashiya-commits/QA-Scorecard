import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

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

# Custom scoring function
def calculate_score(answers):
    """
    Calculate score based on answers.
    SPECIAL RULE: Total score = 0 if Q2 OR Q10 = "No"
    Other questions: Yes=1, No=0, NA=excluded
    """
    # Check if Q2 or Q10 is "No" - if yes, total score = 0
    if answers.get("q2") == "No" or answers.get("q10") == "No":
        return 0, 0, 0
    
    total_score = 0
    max_possible = 0
    
    for i in range(1, 13):
        answer = answers.get(f"q{i}", "No")
        
        # Exclude NA from calculation
        if answer == "NA":
            continue
            
        # Count for max possible
        max_possible += 1
        
        # Score 1 for Yes, 0 for No
        if answer == "Yes":
            total_score += 1
        # No need for else since No = 0
    
    # Calculate percentage
    if max_possible > 0:
        score_percentage = round((total_score / max_possible) * 100, 2)
    else:
        score_percentage = 0
    
    return score_percentage, total_score, max_possible

# Title
st.markdown("<h1 style='text-align: center;'>📊 QA Scorecard System</h1>", unsafe_allow_html=True)

# Navigation
tab1, tab2 = st.tabs(["➕ New Audit", "📋 View Audits"])

with tab1:
    st.header("New QA Audit")
    
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            consultant = st.selectbox(
                "Consultant Name *",
                ["Golden", "Moreen", "John", "Sarah", "Mike", "David", "Lisa"]
            )
            team_leader = st.text_input("Team Leader *", value="Sipho")
            
        with col2:
            client_id = st.text_input("Client ID *", placeholder="CLIENT-001")
            audit_date = st.date_input("Audit Date *", value=datetime.now())
        
        st.divider()
        st.subheader("Quality Assessment Questions")
        
        # Updated questions as per your specification
        questions = {
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
        }
        
        answers = {}
        
        # Create 3 columns for the questions
        col_q1, col_q2, col_q3 = st.columns(3)
        columns = [col_q1, col_q2, col_q3]
        col_idx = 0
        
        for i in range(1, 13):
            with columns[col_idx]:
                question_text = questions[i]
                answer = st.radio(
                    question_text,
                    ["Yes", "No", "NA"],
                    horizontal=False,
                    key=f"q{i}"
                )
                answers[f"q{i}"] = answer
                
                # Show critical warning for Q2 and Q10
                if i == 2 or i == 10:
                    st.caption("⚠️ **CRITICAL:** 'No' = Total score = 0%")
            
            col_idx = (col_idx + 1) % 3
        
        # Calculate score
        score_percentage, raw_score, max_score = calculate_score(answers)
        
        st.divider()
        st.warning("⚠️ **CRITICAL SCORING RULE:** If Q2 OR Q10 is 'No', the total score will be 0%")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            if answers.get("q2") == "No" or answers.get("q10") == "No":
                st.error(f"❌ Total Score: {score_percentage}%")
                st.caption("(Q2 or Q10 = 'No')")
            else:
                st.metric("Total Score", f"{score_percentage}%")
        
        with col4:
            if answers.get("q2") == "No" or answers.get("q10") == "No":
                st.metric("Raw Score", "0/0")
                st.caption("Critical failure")
            else:
                st.metric("Raw Score", f"{raw_score}/{max_score}")
        
        with col5:
            # Color code based on score
            if answers.get("q2") == "No" or answers.get("q10") == "No":
                st.error("❌ FAIL - Critical Error")
            elif score_percentage >= 85:
                st.success("Excellent ✓")
            elif score_percentage >= 70:
                st.warning("Good ⚠️")
            else:
                st.error("Needs Improvement ✗")
        
        # Show critical question status
        if answers.get("q2") == "No":
            st.error("**❌ Q2 FAIL:** Customer validation (POPI Act) not followed")
        if answers.get("q10") == "No":
            st.error("**❌ Q10 FAIL:** Incorrect branch referral")
        
        comments = st.text_area("Additional Comments")
        
        submitted = st.form_submit_button("Submit Audit")
        
        if submitted:
            if not all([consultant, team_leader, client_id]):
                st.error("Please fill all required fields (*)")
            else:
                data = {
                    "consultant": consultant,
                    "team_leader": team_leader,
                    "client_id": client_id,
                    "audit_date": audit_date.isoformat(),
                    "score": score_percentage,
                    "comments": comments,
                    **answers
                }
                
                try:
                    response = supabase.table("audits").insert(data).execute()
                    st.success("✅ Audit submitted successfully!")
                    
                    # Show scoring details
                    with st.expander("Scoring Details", expanded=True):
                        if answers.get("q2") == "No" or answers.get("q10") == "No":
                            st.error("**CRITICAL FAILURE DETECTED:**")
                            if answers.get("q2") == "No":
                                st.write("- Q2 (Customer Validation/POPI): 'No' → Total score = 0%")
                            if answers.get("q10") == "No":
                                st.write("- Q10 (Branch Referral): 'No' → Total score = 0%")
                            st.write("**Final Score: 0%**")
                        else:
                            st.write("**Question Breakdown:**")
                            for i in range(1, 13):
                                answer = answers[f"q{i}"]
                                if answer == "NA":
                                    points = "N/A (excluded)"
                                elif answer == "Yes":
                                    points = "1 point"
                                else:  # No
                                    points = "0 points"
                                
                                # Highlight critical questions
                                if i == 2 or i == 10:
                                    st.write(f"**Q{i}** ⚠️: {answer} → {points}")
                                else:
                                    st.write(f"Q{i}: {answer} → {points}")
                            
                            st.write(f"\n**Total Score:** {raw_score}/{max_score} = **{score_percentage}%**")
                    
                except Exception as e:
                    st.error(f"❌ Error submitting audit: {e}")

with tab2:
    st.header("Previous Audits")
    
    try:
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Calculate metrics
            total_audits = len(df)
            avg_score = df['score'].mean()
            q2_no_count = len(df[df['q2'] == 'No'])
            q10_no_count = len(df[df['q10'] == 'No'])
            critical_failures = len(df[(df['q2'] == 'No') | (df['q10'] == 'No')])
            
            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Audits", total_audits)
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                st.metric("Critical Failures", critical_failures)
                st.caption("Q2 or Q10 = 'No'")
            with col4:
                pass_rate = ((total_audits - critical_failures) / total_audits * 100) if total_audits > 0 else 0
                st.metric("Pass Rate", f"{pass_rate:.1f}%")
            
            # Dataframe with critical indicators
            def highlight_critical(row):
                if row['q2'] == 'No' or row['q10'] == 'No':
                    return ['background-color: #ffcccc'] * len(row)
                return [''] * len(row)
            
            st.subheader("All Audits")
            display_df = df[['id', 'audit_date', 'consultant', 'team_leader', 
                           'client_id', 'score', 'q2', 'q10', 'comments']].copy()
            
            # Apply styling
            styled_df = display_df.style.apply(highlight_critical, axis=1)
            
            # Display the dataframe
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "audit_date": "Date",
                    "consultant": "Consultant",
                    "team_leader": "Team Lead",
                    "client_id": "Client ID",
                    "score": st.column_config.NumberColumn(
                        "Score", 
                        format="%.1f %%",
                        help="Score = 0% if Q2 or Q10 = 'No'"
                    ),
                    "q2": st.column_config.TextColumn(
                        "Q2 ⚠️", 
                        width="small",
                        help="Customer validation (POPI Act)"
                    ),
                    "q10": st.column_config.TextColumn(
                        "Q10 ⚠️", 
                        width="small",
                        help="Branch referral correctness"
                    ),
                    "comments": "Comments"
                }
            )
            
            # Filter options
            with st.expander("Filter Audits", expanded=False):
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    filter_consultant = st.selectbox(
                        "Filter by Consultant:",
                        ["All"] + sorted(df['consultant'].unique().tolist())
                    )
                with col_f2:
                    filter_critical = st.selectbox(
                        "Filter by Critical Status:",
                        ["All", "Critical Failures", "Non-Critical"]
                    )
                with col_f3:
                    filter_score = st.slider(
                        "Minimum Score:",
                        min_value=0, max_value=100, value=0
                    )
                
                # Apply filters
                filtered_df = df.copy()
                
                if filter_consultant != "All":
                    filtered_df = filtered_df[filtered_df['consultant'] == filter_consultant]
                
                if filter_critical == "Critical Failures":
                    filtered_df = filtered_df[(filtered_df['q2'] == 'No') | (filtered_df['q10'] == 'No')]
                elif filter_critical == "Non-Critical":
                    filtered_df = filtered_df[(filtered_df['q2'] != 'No') & (filtered_df['q10'] != 'No')]
                
                filtered_df = filtered_df[filtered_df['score'] >= filter_score]
                
                st.write(f"**{len(filtered_df)} audits match your filters**")
                if len(filtered_df) > 0:
                    st.dataframe(filtered_df[['consultant', 'audit_date', 'score', 'q2', 'q10']])
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download All Audits as CSV",
                data=csv,
                file_name="audits.csv",
                mime="text/csv"
            )
            
            # Critical failures analysis
            if critical_failures > 0:
                st.subheader("Critical Failures Analysis")
                critical_df = df[(df['q2'] == 'No') | (df['q10'] == 'No')]
                
                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    st.write("**Breakdown by Consultant:**")
                    consultant_counts = critical_df['consultant'].value_counts()
                    st.dataframe(consultant_counts)
                
                with col_c2:
                    st.write("**Failure Reasons:**")
                    q2_failures = len(critical_df[critical_df['q2'] == 'No'])
                    q10_failures = len(critical_df[critical_df['q10'] == 'No'])
                    both_failures = len(critical_df[(critical_df['q2'] == 'No') & (critical_df['q10'] == 'No')])
                    
                    failure_data = pd.DataFrame({
                        'Failure Type': ['Q2 Only', 'Q10 Only', 'Both Q2 & Q10'],
                        'Count': [
                            q2_failures - both_failures,
                            q10_failures - both_failures,
                            both_failures
                        ]
                    })
                    st.dataframe(failure_data, hide_index=True)
            
        else:
            st.info("No audits found. Submit your first audit above!")
            
    except Exception as e:
        st.error(f"Error fetching audits: {e}")
