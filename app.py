import streamlit as st
from supabase import create_client
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="QA Scoring Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== SUPABASE CONNECTION ====================
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# ==================== SIDEBAR HEADER ====================
st.sidebar.title("🎯 QA Scorecard System")
st.sidebar.markdown("---")

# Optional: Add sidebar filters/controls for your dashboard
st.sidebar.subheader("Dashboard Filters")

# Date range filter
date_range = st.sidebar.date_input(
    "Select Date Range",
    value=[datetime.now() - timedelta(days=30), datetime.now()],
    max_value=datetime.now()
)

# Team filter
teams = ["All", "Team A", "Team B", "Team C", "Team D"]
selected_team = st.sidebar.selectbox("Select Team", teams)

# Score threshold
score_threshold = st.sidebar.slider("Minimum Score Threshold", 0, 100, 70)

st.sidebar.markdown("---")
st.sidebar.info("Use the navigation above to switch between pages")

# ==================== MAIN DASHBOARD CONTENT ====================
st.title("🎯 QA Scoring Dashboard")
st.markdown("---")

# Create tabs for different views
tab1, tab2, tab3, tab4 = st.tabs(["📊 Overview", "📈 Trends", "👥 Team Performance", "🔍 Detailed Scores"])

with tab1:
    st.header("Overall Performance")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Average Score", "87.5", "+2.3%")
    
    with col2:
        st.metric("Total Evaluations", "1,247", "+15%")
    
    with col3:
        st.metric("Pass Rate", "92.3%", "+1.2%")
    
    with col4:
        st.metric("Avg. Time/Evaluation", "12.4m", "-0.8m")
    
    # Sample chart
    st.subheader("Score Distribution")
    scores = np.random.normal(85, 10, 1000)
    fig = px.histogram(scores, nbins=20, title="Distribution of QA Scores")
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.header("Performance Trends")
    
    # Time series data
    dates = pd.date_range(start='2024-01-01', end='2024-03-01', freq='W')
    trend_data = pd.DataFrame({
        'Date': dates,
        'Average Score': np.random.randint(75, 95, len(dates)),
        'Volume': np.random.randint(50, 150, len(dates))
    })
    
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    fig.add_trace(
        go.Scatter(x=trend_data['Date'], y=trend_data['Average Score'], name="Average Score"),
        secondary_y=False,
    )
    
    fig.add_trace(
        go.Bar(x=trend_data['Date'], y=trend_data['Volume'], name="Evaluation Volume", opacity=0.5),
        secondary_y=True,
    )
    
    fig.update_layout(title="Performance Trends Over Time")
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Average Score", secondary_y=False)
    fig.update_yaxes(title_text="Evaluation Volume", secondary_y=True)
    
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    st.header("Team Performance Comparison")
    
    team_data = pd.DataFrame({
        'Team': ['Team A', 'Team B', 'Team C', 'Team D', 'Team E'],
        'Average Score': [88.5, 92.1, 85.3, 90.7, 87.9],
        'Evaluations': [245, 312, 198, 276, 216],
        'Improvement': [2.3, 3.1, 1.5, 2.8, 1.9]
    })
    
    # Sort by score
    team_data = team_data.sort_values('Average Score', ascending=True)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=team_data['Team'],
        x=team_data['Average Score'],
        orientation='h',
        marker_color='#FF4B4B',
        text=team_data['Average Score'],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Team Performance (Sorted by Score)",
        xaxis_title="Average Score",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display data table
    st.dataframe(team_data, use_container_width=True)

with tab4:
    st.header("Detailed Evaluation Scores")
    
    # Sample detailed data
    detailed_data = pd.DataFrame({
        'Evaluation ID': [f"EVAL-{i:04d}" for i in range(1, 21)],
        'Agent': [f"Agent {i}" for i in range(1, 21)],
        'Date': pd.date_range(start='2024-03-01', periods=20, freq='D'),
        'Score': np.random.randint(60, 100, 20),
        'Category': np.random.choice(['Call', 'Chat', 'Email', 'Ticket'], 20),
        'Status': np.random.choice(['Pass', 'Fail', 'Needs Review'], 20, p=[0.7, 0.2, 0.1])
    })
    
    # Add color coding for scores
    def score_color(score):
        if score >= 90:
            return '🟢'
        elif score >= 80:
            return '🟡'
        elif score >= 70:
            return '🟠'
        else:
            return '🔴'
    
    detailed_data['Rating'] = detailed_data['Score'].apply(score_color)
    
    # Display with filters
    col1, col2 = st.columns(2)
    with col1:
        min_score = st.slider("Minimum Score", 0, 100, 70)
    with col2:
        categories = st.multiselect(
            "Categories",
            options=detailed_data['Category'].unique(),
            default=detailed_data['Category'].unique()
        )
    
    # Filter data
    filtered_data = detailed_data[
        (detailed_data['Score'] >= min_score) &
        (detailed_data['Category'].isin(categories))
    ]
    
    st.dataframe(
        filtered_data.sort_values('Score', ascending=False),
        use_container_width=True,
        column_config={
            "Rating": st.column_config.TextColumn("Rating", width="small"),
            "Score": st.column_config.ProgressColumn(
                "Score",
                format="%d",
                min_value=0,
                max_value=100,
            )
        }
    )
    
    # Download button
    csv = filtered_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Data",
        data=csv,
        file_name="qa_scores_filtered.csv",
        mime="text/csv",
    )

# ==================== FOOTER ====================
st.markdown("---")
st.caption("QA Scorecard System • Last updated: March 2024")
