import streamlit as st
import pandas as pd
from io import BytesIO

st.title("📄 Reports")

# Function to convert CSV to Excel in-memory
def convert_to_excel(csv_file_path):
    df = pd.read_csv(csv_file_path)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Report')
        writer.save()
        processed_data = output.getvalue()
    return processed_data

st.header("Weekly Report")
if st.button("Generate Weekly Report"):
    try:
        excel_data = convert_to_excel("weekly_report.csv")
        st.success("Weekly report generated!")
        st.download_button(
            label="Download Weekly Report",
            data=excel_data,
            file_name="Weekly_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except FileNotFoundError:
        st.error("Weekly report CSV not found!")

st.header("Monthly Report")
if st.button("Generate Monthly Report"):
    try:
        excel_data = convert_to_excel("monthly_report.csv")
        st.success("Monthly report generated!")
        st.download_button(
            label="Download Monthly Report",
            data=excel_data,
            file_name="Monthly_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except FileNotFoundError:
        st.error("Monthly report CSV not found!")
