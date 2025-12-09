import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime

# -------------------------
# Supabase Connection
# -------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Function to fetch report
# -------------------------
def fetch_report(table_name, report_type=None, start_date=None, end_date=None):
    try:
        # Get first row to inspect columns
        sample = supabase.table(table_name).select("*").limit(1).execute()
        if not sample.data:
            st.warning("No data found in the table.")
            return pd.DataFrame()
        df_sample = pd.DataFrame(sample.data)
        
        # Detect report type column
        report_col_candidates = [col for col in df_sample.columns if "report" in col.lower()]
        report_col = report_col_candidates[0] if report_col_candidates else None
        
        # Detect date column
        date_col_candidates = [col for col in df_sample.columns if "date" in col.lower()]
        date_col = date_col_candidates[0] if date_col_candidates else None

        query = supabase.table(table_name).select("*")
        if report_col and report_type:
            query = query.eq(report_col, report_type.lower())
        if date_col:
            if start_date:
                query = query.gte(date_col, start_date.strftime("%Y-%m-%d"))
            if end_date:
                query = query.lte(date_col, end_date.strftime("%Y-%m-%d"))
        
        res = query.execute()
        if res.data:
            return pd.DataFrame(res.data)
        else:
            st.warning("No records found for your selection.")
            return pd.DataFrame()
    except Exception as e:
        st.error(f"Error fetching report: {e}")
        return pd.DataFrame()

# -------------------------
# Streamlit UI
# -------------------------
st.title("📄 QA Reports")

# Fetch available report types dynamically
try:
    sample_data = supabase.table("audits").select("*").limit(50).execute()
    df_sample = pd.DataFrame(sample_data.data) if sample_data.data else pd.DataFrame()
    report_col_candidates = [col for col in df_sample.columns if "report" in col.lower()]
    report_col = report_col_candidates[0] if report_col_candidates else None
    available_report_types = df_sample[report_col].unique().tolist() if report_col else ["weekly", "monthly"]
except:
    available_report_types = ["Weekly", "Monthly"]

report_type = st.selectbox("Select Report Type:", available_report_types)

start_date = st.date_input("Start Date", datetime.today())
end_date = st.date_input("End Date", datetime.today())

if st.button("Generate Report"):
    df_report = fetch_report("audits", report_type=report_type, start_date=start_date, end_date=end_date)
    
    if not df_report.empty:
        st.dataframe(df_report)

        excel_file = f"{report_type}_report.xlsx"
        df_report.to_excel(excel_file, index=False)
        st.download_button(
            label="Download Report as Excel",
            data=open(excel_file, "rb").read(),
            file_name=excel_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
