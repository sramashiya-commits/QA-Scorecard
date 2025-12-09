import streamlit as st
import pandas as pd
from supabase import create_client, Client

# -------------------------
# Supabase Connection
# -------------------------
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -------------------------
# Function to fetch report
# -------------------------
def fetch_report(table_name, filter_col=None, filter_val=None):
    query = supabase.table(table_name).select("*")
    if filter_col and filter_val:
        query = query.eq(filter_col, filter_val)
    try:
        res = query.execute()
        if res.data:
            df = pd.DataFrame(res.data)
            return df
        else:
            return pd.DataFrame()  # empty dataframe
    except Exception as e:
        st.error(f"Error fetching report: {e}")
        return pd.DataFrame()

# -------------------------
# Streamlit UI
# -------------------------
st.title("📄 QA Reports")

report_type = st.radio("Select Report Type:", ["Weekly", "Monthly"])

if st.button(f"Generate {report_type} Report"):
    # Adjust column name here if your table uses a different one
    filter_column = "report_type"  # change to the actual column in your table
    filter_value = report_type.lower()  # 'weekly' or 'monthly'

    df_report = fetch_report("audits", filter_col=filter_column, filter_val=filter_value)

    if not df_report.empty:
        # Show dataframe
        st.dataframe(df_report)

        # Convert to Excel
        excel_file = f"{report_type}_report.xlsx"
        df_report.to_excel(excel_file, index=False)

        # Provide download link
        st.download_button(
            label=f"Download {report_type} Report as Excel",
            data=open(excel_file, "rb").read(),
            file_name=excel_file,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.warning(f"No {report_type} report found.")
