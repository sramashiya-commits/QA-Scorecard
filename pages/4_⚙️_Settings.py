import streamlit as st

st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ Settings")
st.markdown("---")

# Settings options
with st.expander("Application Settings", expanded=True):
    notifications = st.checkbox("Enable email notifications", value=True)
    auto_refresh = st.checkbox("Auto-refresh data", value=False)
    refresh_interval = st.slider("Refresh interval (minutes)", 1, 60, 5)

with st.expander("User Preferences"):
    theme = st.selectbox("Theme", ["Light", "Dark", "Auto"])
    timezone = st.selectbox("Timezone", ["UTC", "EST", "PST", "IST"])

if st.button("Save Settings"):
    st.success("Settings saved successfully!")
