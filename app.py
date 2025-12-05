from supabase import create_client
import streamlit as st

# Connect to Supabase
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Insert a score
data = {
    "agent_name": agent_name,
    "score": final_score,
    "date": datetime.now().isoformat()
}

supabase.table("qa_scores").insert(data).execute()

# Fetch for dashboard
rows = supabase.table("qa_scores").select("*").execute().data
