import streamlit as st

st.set_page_config(
    page_title="Data Management",
    page_icon="🗄️",
    layout="wide"
)

st.title("🗄️ Data Management")
st.markdown("---")

st.write("This is the data management page where you can:")
st.write("- Upload new QA data")
st.write("- Edit existing records")
st.write("- Manage datasets")

# File uploader example
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])
if uploaded_file is not None:
    st.success(f"File uploaded: {uploaded_file.name}")
