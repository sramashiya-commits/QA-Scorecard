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

# Test connection
try:
    # ✅ Use 'audits' not 'scorecards'
    response = supabase.table('audits').select("*").limit(1).execute()
    st.sidebar.success("✅ Connected to Supabase")
except Exception as e:
    st.sidebar.error(f"❌ Connection error: {e}")

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
                ["Aobakwe Peter", "Daychannel Jasson", "Daychannel Jaysson", "Diya Ramesar", "Golden Raphulu", "Karabo Ratau", "Moreen Nkosi"]
            )
            team_leader = st.text_input("Team Leader *", value="Sipho Ramashiya")
            
        with col2:
            client_id = st.text_input("Client ID *", placeholder="CLIENT-001")
            audit_date = st.date_input("Audit Date *", value=datetime.now())
        
        st.divider()
        st.subheader("Quality Assessment Questions")
        
        # Questions (you can customize these)
        questions = [
            "Q1: Professional greeting and introduction?",
            "Q2: Active listening demonstrated?",
            "Q3: Accurate information provided?",
            "Q4: Proper call structure followed?",
            "Q5: Correct documentation?",
            "Q6: Compliance with procedures?",
            "Q7: Customer needs addressed?",
            "Q8: Professional language used?",
            "Q9: Appropriate call closure?",
            "Q10: Follow-up actions specified?",
            "Q11: Quality of solution provided?",
            "Q12: Overall customer experience?"
        ]
        
        answers = {}
        scores = {"Yes": 1, "No": 0, "NA": 0}
        total_score = 0
        
        for i, question in enumerate(questions, 1):
            answer = st.radio(
                question,
                ["Yes", "No", "NA"],
                horizontal=True,
                key=f"q{i}"
            )
            answers[f"q{i}"] = answer
            total_score += scores[answer]
        
        # Calculate percentage score
        score_percentage = round((total_score / 12) * 100, 2)
        
        st.divider()
        col3, col4 = st.columns(2)
        with col3:
            st.metric("Total Score", f"{score_percentage}%")
        with col4:
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
                    # ✅ Insert into 'audits' table
                    response = supabase.table("audits").insert(data).execute()
                    st.success("✅ Audit submitted successfully!")
                    
                    # Show summary
                    st.balloons()
                    st.subheader("Audit Summary")
                    st.json(data)
                    
                except Exception as e:
                    st.error(f"❌ Error submitting audit: {e}")

with tab2:
    st.header("Previous Audits")
    
    try:
        # ✅ Fetch from 'audits' table
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Show metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Audits", len(df))
            with col2:
                avg_score = df['score'].mean()
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                unique_consultants = df['consultant'].nunique()
                st.metric("Consultants", unique_consultants)
            
            # Dataframe
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "consultant": "Consultant",
                    "team_leader": "Team Lead",
                    "client_id": "Client ID",
                    "audit_date": "Date",
                    "score": st.column_config.NumberColumn("Score", format="%.1f %%"),
                    "comments": "Comments"
                }
            )
            
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
