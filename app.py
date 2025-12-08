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
    Special rule: Q2 and Q10 = 0 if "No"
    Other questions: Yes=1, No=0, NA=excluded
    """
    total_score = 0
    max_possible = 0
    
    for i in range(1, 13):
        answer = answers.get(f"q{i}", "No")
        
        # Questions 2 and 10 have special rules (score 0 if "No")
        if i == 2 or i == 10:
            if answer == "Yes":
                total_score += 1
                max_possible += 1
            elif answer == "No":
                # ZERO points for Q2 or Q10 if "No"
                total_score += 0
                max_possible += 1
            # "NA" is excluded from calculation
        else:
            # Normal scoring for other questions
            if answer == "Yes":
                total_score += 1
                max_possible += 1
            elif answer == "No":
                total_score += 0
                max_possible += 1
            # "NA" is excluded
    
    # Calculate percentage
    if max_possible > 0:
        score_percentage = round((total_score / max_possible) * 100, 2)
    else:
        score_percentage = 0
    
    return score_percentage, total_score, max_possible

# Title
st.title("📊 QA Scorecard System")

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
        st.caption("⚠️ **Note:** Questions 2 and 10 score 0 if answered 'No'. Other questions follow normal scoring.")
        
        # Questions with special indicators for Q2 and Q10
        questions = {
            1: "Q1: Was the consultant Friendly & Professional towards the customer…i.e.Greetings, introduce yourself etc?",
            2: "Q2: Did the consultant correctly validate the customer as per the validation process (POPI Act)?, ⚠️",
            3: "Q3: Was the consultant Actively Listening to the customer(Understanding the reason for the call)?",
            4: "Q4: Did the consultant display Empathy?",
            5: "Q5: Were notes placed on every interaction of the query/complaint?",
            6: "Q6: Was the Hold Process followed correctly?",
            7: "Q7: Was the call transferred to the appropriate Dept?",
            8: "Q8: Did the consultant assist the client to navigate correctly?",
            9: "Q9: Was the Pin/Password reset process followed?",
            10: "Q10: Was the Branch referral correct i.e. Was it warranted or could it be resolved online?, ⚠️",
            11: "Q11: Did the agent call back the client?",
            12: "Q12: Was Self-Service Promoted? i.e. Self-authentication cia IVR, Karabo etc?"
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
                
                # Show scoring hint for special questions
                if i == 2 or i == 10:
                    st.caption("⚠️ Scores 0 if 'No'")
            
            col_idx = (col_idx + 1) % 3
        
        # Calculate score
        score_percentage, raw_score, max_score = calculate_score(answers)
        
        st.divider()
        col3, col4, col5 = st.columns(3)
        with col3:
            st.metric("Total Score", f"{score_percentage}%")
        with col4:
            st.metric("Raw Score", f"{raw_score}/{max_score}")
        with col5:
            # Color code based on score
            if score_percentage >= 85:
                st.success("Excellent ✓")
            elif score_percentage >= 70:
                st.warning("Good ⚠️")
            else:
                st.error("Needs Improvement ✗")
        
        # Show scoring impact of Q2 and Q10
        with st.expander("Scoring Rules", expanded=False):
            st.info("""
            **Special Scoring Rules:**
            - **Q2 (Active listening)** and **Q10 (Follow-up actions)**: Score **0** if "No" is selected
            - Other questions: Normal scoring (1 for Yes, 0 for No)
            - "NA" responses are excluded from calculation
            """)
        
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
                    
                    # Show detailed scoring breakdown
                    with st.expander("Detailed Scoring Breakdown", expanded=True):
                        st.write("**Question-by-Question Scoring:**")
                        
                        special_questions = {2, 10}
                        
                        for i in range(1, 13):
                            answer = answers[f"q{i}"]
                            
                            # Calculate points for this question
                            if answer == "Yes":
                                points = 1
                            elif answer == "No":
                                # Special rule for Q2 and Q10
                                if i in special_questions:
                                    points = 0  # ZERO points for "No" on Q2 or Q10
                                else:
                                    points = 0  # Normal 0 for "No" on other questions
                            else:  # "NA"
                                points = "N/A (excluded)"
                            
                            # Display with special indicator
                            if i in special_questions:
                                st.write(f"**Q{i}** ⚠️: {answer} → {points} point{'s' if points == 1 else ''}")
                            else:
                                st.write(f"Q{i}: {answer} → {points} point{'s' if points == 1 else ''}")
                        
                        st.write(f"**Total Score:** {raw_score}/{max_score} = **{score_percentage}%**")
                    
                except Exception as e:
                    st.error(f"❌ Error submitting audit: {e}")

with tab2:
    st.header("Previous Audits")
    
    try:
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Audits", len(df))
            with col2:
                avg_score = df['score'].mean()
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                # Count audits with Q2 or Q10 = "No"
                q2_no_count = len(df[df['q2'] == 'No'])
                q10_no_count = len(df[df['q10'] == 'No'])
                st.metric("Q2/Q10 'No'", f"{q2_no_count}/{q10_no_count}")
            with col4:
                unique_consultants = df['consultant'].nunique()
                st.metric("Consultants", unique_consultants)
            
            # Highlight special questions in the dataframe
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_order=["id", "audit_date", "consultant", "team_leader", 
                             "client_id", "score", "q2", "q10", "comments"],
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "audit_date": "Date",
                    "consultant": "Consultant",
                    "team_leader": "Team Lead",
                    "client_id": "Client ID",
                    "score": st.column_config.NumberColumn("Score", format="%.1f %%"),
                    "q2": st.column_config.TextColumn("Q2 ⚠️", width="small"),
                    "q10": st.column_config.TextColumn("Q10 ⚠️", width="small"),
                    "comments": "Comments"
                }
            )
            
            # Add filter for special questions
            with st.expander("Filter by Special Questions"):
                filter_q2 = st.selectbox("Filter by Q2 (Active Listening):", 
                                         ["All", "Yes", "No", "NA"])
                filter_q10 = st.selectbox("Filter by Q10 (Follow-up Actions):", 
                                          ["All", "Yes", "No", "NA"])
                
                filtered_df = df.copy()
                if filter_q2 != "All":
                    filtered_df = filtered_df[filtered_df['q2'] == filter_q2]
                if filter_q10 != "All":
                    filtered_df = filtered_df[filtered_df['q10'] == filter_q10]
                
                if len(filtered_df) > 0:
                    st.write(f"Showing {len(filtered_df)} audits:")
                    st.dataframe(filtered_df[['consultant', 'audit_date', 'score', 'q2', 'q10']])
                else:
                    st.info("No audits match the selected filters.")
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download as CSV",
                data=csv,
                file_name="audits.csv",
                mime="text/csv"
            )
        else:
            st.info("No audits found. Submit your first audit above!")
            
    except Exception as e:
        st.error(f"Error fetching audits: {e}")
