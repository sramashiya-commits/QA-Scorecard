import streamlit as st
import pandas as pd
from io import BytesIO
from supabase import create_client, Client

st.title("📄 Reports")

# -------------------- Supabase connection --------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------- Helper: Convert DataFrame to Excel --------------------
def df_to_excel(df: pd.DataFrame) -> bytes:
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
        writer.save()
        data = output.getvalue()
    return data

# -------------------- Fetch Reports from Supabase --------------------
def fetch_report(table_name: str, filter_col=None, filter_val=None):
    query = supabase.table(table_name).select("*")
    if filter_col and filter_val:
        query = query.eq(filter_col, filter_val)
    res = query.execute()
    if res.error:
        st.error(f"Error fetching {table_name}: {res.error.message}")
        return pd.DataFrame()
    return pd.DataFrame(res.data)

# -------------------- Weekly Report --------------------
st.header("Weekly Report")
if st.button("Generate Weekly Report"):
    df_weekly = fetch_report("audits", filter_col="report_type", filter_val="weekly")
    if not df_weekly.empty:
        excel_data = df_to_excel(df_weekly)
        st.success("Weekly report generated!")
        st.download_button(
            label="Download Weekly Report",
            data=excel_data,
            file_name="Weekly_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No weekly data found!")

# -------------------- Monthly Report --------------------
st.header("Monthly Report")
if st.button("Generate Monthly Report"):
    df_monthly = fetch_report("audits", filter_col="report_type", filter_val="monthly")
    if not df_monthly.empty:
        excel_data = df_to_excel(df_monthly)
        st.success("Monthly report generated!")
        st.download_button(
            label="Download Monthly Report",
            data=excel_data,
            file_name="Monthly_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning("No monthly data found!")
