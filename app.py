import streamlit as st
from supabase import create_client
import pandas as pd
import numpy as np
from datetime import datetime

# Page config
st.set_page_config(
    page_title="QA Scorecard System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Supabase connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ==================== MAIN SCORING DASHBOARD ====================
st.title("🎯 QA Scoring Dashboard")
st.markdown("---")

# Create tabs for different scoring views
tab1, tab2, tab3 = st.tabs(["📝 Submit Audit", "📊 View Scores", "👤 Consultant Lookup"])

with tab1:
    st.header("Submit New Audit")
    
    with st.form("audit_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            consultant = st.text_input("Consultant Name", key="consultant")
            team_leader = st.text_input("Team Leader", key="team_leader")
            department = st.selectbox(
                "Department",
                ["Digital Support", "ARQ", "DVQ (KYC)", "Dialler", "Other"],
                key="department"
            )
            audit_date = st.date_input("Audit Date", datetime.now(), key="audit_date")
        
        with col2:
            audit_type = st.selectbox(
                "Audit Type",
                ["Random", "Targeted", "Complaint", "Training"],
                key="audit_type"
            )
            auditor = st.text_input("Auditor Name", key="auditor")
            overall_comments = st.text_area("Overall Comments", key="comments")
        
        st.markdown("### Audit Questions")
        
        # Sample questions - customize based on your needs
        questions = []
        scores = []
        
        for i in range(1, 13):
            col_q1, col_q2 = st.columns([3, 1])
            with col_q1:
                question_text = st.text_input(
                    f"Question {i}",
                    value=f"Q{i} - Did the consultant follow proper procedure?",
                    key=f"q{i}_text"
                )
            with col_q2:
                response = st.selectbox(
                    "Response",
                    ["Yes", "No", "NA"],
                    key=f"q{i}"
                )
                questions.append(question_text)
                scores.append(1 if response == "Yes" else 0)
        
        submitted = st.form_submit_button("Submit Audit")
        
        if submitted:
            # Calculate score
            valid_responses = [s for s in scores if s != "NA"]
            if valid_responses:
                total_score = (sum([1 for s in scores if s == 1]) / len(valid_responses)) * 100
            else:
                total_score = 0
            
            # Prepare data for Supabase
            audit_data = {
                "consultant": consultant,
                "team_leader": team_leader,
                "department": department,
                "audit_date": str(audit_date),
                "audit_type": audit_type,
                "auditor": auditor,
                "comments": overall_comments,
                "score": total_score
            }
            
            # Add question responses
            for i in range(1, 13):
                audit_data[f"q{i}"] = st.session_state.get(f"q{i}", "NA")
            
            # Insert into Supabase
            try:
                response = supabase.table("audits").insert(audit_data).execute()
                st.success(f"✅ Audit submitted successfully! Score: {total_score:.1f}%")
                st.balloons()
            except Exception as e:
                st.error(f"Error submitting audit: {e}")

with tab2:
    st.header("Recent Audit Scores")
    
    try:
        # Fetch recent audits
        response = supabase.table("audits").select("*").order("audit_date", desc=True).limit(50).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Display summary metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Audits", len(df))
            with col2:
                st.metric("Avg Score", f"{df['score'].mean():.1f}%")
            with col3:
                st.metric("Today's Audits", len(df[df['audit_date'] == str(datetime.now().date())]))
            with col4:
                st.metric("Top Dept", df.groupby('department')['score'].mean().idxmax())
            
            # Display data
            st.dataframe(
                df[['consultant', 'department', 'audit_date', 'score', 'auditor']],
                use_container_width=True
            )
        else:
            st.info("No audit data available yet.")
            
    except Exception as e:
        st.error(f"Error loading data: {e}")

with tab3:
    st.header("Consultant Performance Lookup")
    
    # Fetch all consultants
    try:
        response = supabase.table("audits").select("consultant").execute()
        consultants = sorted(set([item['consultant'] for item in response.data if item['consultant']]))
        
        selected_consultant = st.selectbox("Select Consultant", consultants)
        
        if selected_consultant:
            # Get consultant's audits
            response = supabase.table("audits").select("*").eq("consultant", selected_consultant).order("audit_date", desc=True).execute()
            
            if response.data:
                consultant_df = pd.DataFrame(response.data)
                
                st.subheader(f"Performance Summary for {selected_consultant}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Audits", len(consultant_df))
                with col2:
                    st.metric("Average Score", f"{consultant_df['score'].mean():.1f}%")
                with col3:
                    st.metric("Best Score", f"{consultant_df['score'].max():.1f}%")
                
                # Display recent audits
                st.dataframe(
                    consultant_df[['audit_date', 'score', 'department', 'auditor', 'comments']],
                    use_container_width=True
                )
            else:
                st.info(f"No audits found for {selected_consultant}")
                
    except Exception as e:
        st.error(f"Error loading consultant data: {e}")

# Footer
st.markdown("---")
st.caption("QA Scorecard System • Use the sidebar to navigate to Analytics Dashboard")
