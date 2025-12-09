import streamlit as st
import pandas as pd
import io

st.title("📄 Reports")

# Paths to your CSV reports (replace with actual paths or dynamic sources)
WEEKLY_CSV_PATH = "data/weekly_report.csv"
MONTHLY_CSV_PATH = "data/monthly_report.csv"

def generate_excel_download(df, filename):
    """Convert a DataFrame to Excel in memory and return BytesIO object"""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Report")
    output.seek(0)
    return output

# --- Weekly Report ---
st.subheader("Weekly Report")
try:
    weekly_df = pd.read_csv(WEEKLY_CSV_PATH)
except FileNotFoundError:
    st.error("Weekly CSV not found!")
else:
    if st.button("Generate Weekly Report"):
        excel_data = generate_excel_download(weekly_df, "Weekly_Report.xlsx")
        st.download_button(
            label="Download Weekly Report (Excel)",
            data=excel_data,
            file_name="Weekly_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Weekly report generated! ✅")

# --- Monthly Report ---
st.subheader("Monthly Report")
try:
    monthly_df = pd.read_csv(MONTHLY_CSV_PATH)
except FileNotFoundError:
    st.error("Monthly CSV not found!")
else:
    if st.button("Generate Monthly Report"):
        excel_data = generate_excel_download(monthly_df, "Monthly_Report.xlsx")
        st.download_button(
            label="Download Monthly Report (Excel)",
            data=excel_data,
            file_name="Monthly_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("Monthly report generated! ✅")
