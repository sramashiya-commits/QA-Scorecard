import streamlit as st
from supabase import create_client, Client
import pandas as pd

# Initialize Supabase
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_report(table_name, filter_col=None, filter_val=None):
    try:
        query = supabase.table(table_name).select("*")
        if filter_col and filter_val:
            query = query.eq(filter_col, filter_val)
        res = query.execute()
        
        if res.data is None:
            st.warning(f"No data found in table '{table_name}' with {filter_col} = '{filter_val}'")
            return pd.DataFrame()
        
        df = pd.DataFrame(res.data)
        return df
    except Exception as e:
        st.error(f"Error fetching report: {e}")
        return pd.DataFrame()

# --- In your Reports page ---
st.header("Reports")
if st.button("Generate Weekly Report"):
    df_weekly = fetch_report("audits", filter_col="report_type", filter_val="weekly")
    if not df_weekly.empty:
        # Export as Excel
        st.download_button(
            label="Download Weekly Report",
            data=df_weekly.to_excel(index=False, engine='openpyxl'),
            file_name="weekly_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No weekly report data available.")
