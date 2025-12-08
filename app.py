import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="QA Scorecard System",
    page_icon="📊",
    layout="wide"
)

# Initialize Supabase connection
@st.cache_resource
def init_connection():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_connection()

# Custom scoring function
def calculate_score(answers):
    """
    Calculate score based on answers.
    SPECIAL RULE: Total score = 0 if Q2 OR Q10 = "No"
    Other questions: Yes=1, No=0, NA=excluded
    """
    # Check if Q2 or Q10 is "No" - if yes, total score = 0
    if answers.get("q2") == "No" or answers.get("q10") == "No":
        return 0, 0, 0
    
    total_score = 0
    max_possible = 0
    
    for i in range(1, 13):
        answer = answers.get(f"q{i}", "No")
        
        # Exclude NA from calculation
        if answer == "NA":
            continue
            
        # Count for max possible
        max_possible += 1
        
        # Score 1 for Yes, 0 for No
        if answer == "Yes":
            total_score += 1
        # No need for else since No = 0
    
    # Calculate percentage
    if max_possible > 0:
        score_percentage = round((total_score / max_possible) * 100, 2)
    else:
        score_percentage = 0
    
    return score_percentage, total_score, max_possible

# Initialize session state for form clearing
if 'form_submitted' not in st.session_state:
    st.session_state.form_submitted = False
if 'clear_form' not in st.session_state:
    st.session_state.clear_form = False

# Centered Main Title
st.markdown("<h1 style='text-align: center;'>📊 QA Scorecard System</h1>", unsafe_allow_html=True)

# Create tabs
tab1, tab2, tab3 = st.tabs(["➕ New Audit", "📋 View Audits", "📈 Analytics Dashboard"])

with tab1:
    st.markdown("<h2 style='text-align: center;'>New QA Audit</h2>", unsafe_allow_html=True)
    
    # If form was just submitted, show success message and "Score Another" button
    if st.session_state.get('form_submitted', False):
        st.success("✅ Audit submitted successfully!")
        
        col_success1, col_success2, col_success3 = st.columns([1, 2, 1])
        with col_success2:
            if st.button("🎯 Score Another Person", type="primary", use_container_width=True):
                # Clear the form by resetting session state
                st.session_state.form_submitted = False
                st.session_state.clear_form = True
                st.rerun()
        
        # Show the submitted audit details
        with st.expander("📋 View Submitted Audit Details", expanded=True):
            if 'last_submitted_data' in st.session_state:
                st.write("**Last Submitted Audit:**")
                st.json(st.session_state.last_submitted_data)
    
    # Create a fresh form instance
    with st.form("audit_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            consultant = st.selectbox(
                "Consultant Name *",
                ["Aobakwe Peter", "Daychannel Jasson", "Diya Ramesar", "Golden Raphulu", "Karabo Ratau", "Moreen Nkosi",],
                index=None,
                placeholder="Select consultant..."
            )
            team_leader = st.text_input("Team Leader *", value="Sipho Ramashiya")
            
        with col2:
            client_id = st.text_input("Client ID *", placeholder="CLIENT-001")
            audit_date = st.date_input("Audit Date *", value=datetime.now())
        
        st.divider()
        st.subheader("Quality Assessment Questions")
        
        # Updated questions as per your specification
        questions = {
            1: "Q1: Was the consultant Friendly & Professional towards the customer?…i.e. Greetings, introduce yourself etc?",
            2: "Q2: Did the consultant correctly validate the customer as per the validation process? (POPI Act)? ⚠️",
            3: "Q3: Was the consultant Actively Listening to the customer? (Understanding the reason for the call)?",
            4: "Q4: Did the consultant display Empathy?",
            5: "Q5: Were notes placed on every interaction of the query/complaint?",
            6: "Q6: Was the Hold Process followed correctly?",
            7: "Q7: Was the call transferred to the appropriate Dept?",
            8: "Q8: Did the consultant assist the client to navigate correctly?",
            9: "Q9: Was the Pin/Password reset process followed?",
            10: "Q10: Was the Branch referral correct i.e. Was it warranted or could it be resolved online? ⚠️",
            11: "Q11: Did the agent call back the client?",
            12: "Q12: Was Self-Service Promoted? i.e. Self-authentication via IVR, Karabo etc?"
        }
        
        answers = {}
        
        # Create 3 columns for the questions
        col_q1, col_q2, col_q3 = st.columns(3)
        columns = [col_q1, col_q2, col_q3]
        col_idx = 0
        
        for i in range(1, 13):
            with columns[col_idx]:
                question_text = questions[i]
                answer = st.radio(
                    question_text,
                    ["Yes", "No", "NA"],
                    horizontal=False,
                    key=f"q{i}_form",
                    index=None  # Start with no selection
                )
                answers[f"q{i}"] = answer
                
                # Show critical warning for Q2 and Q10
                if i == 2 or i == 10:
                    st.caption("⚠️ **CRITICAL:** 'No' = Total score = 0%")
            
            col_idx = (col_idx + 1) % 3
        
        # Calculate score
        score_percentage, raw_score, max_score = calculate_score(answers)
        
        st.divider()
        st.warning("⚠️ **CRITICAL SCORING RULE:** If Q2 OR Q10 is 'No', the total score will be 0%")
        
        col3, col4, col5 = st.columns(3)
        with col3:
            if answers.get("q2") == "No" or answers.get("q10") == "No":
                st.error(f"❌ Total Score: {score_percentage}%")
                st.caption("(Q2 or Q10 = 'No')")
            else:
                st.metric("Total Score", f"{score_percentage}%")
        
        with col4:
            if answers.get("q2") == "No" or answers.get("q10") == "No":
                st.metric("Raw Score", "0/0")
                st.caption("Critical failure")
            else:
                st.metric("Raw Score", f"{raw_score}/{max_score}")
        
        with col5:
            # Color code based on score
            if answers.get("q2") == "No" or answers.get("q10") == "No":
                st.error("❌ FAIL - Critical Error")
            elif score_percentage >= 85:
                st.success("Excellent ✓")
            elif score_percentage >= 70:
                st.warning("Good ⚠️")
            else:
                st.error("Needs Improvement ✗")
        
        # Show critical question status
        if answers.get("q2") == "No":
            st.error("**❌ Q2 FAIL:** Customer validation (POPI Act) not followed")
        if answers.get("q10") == "No":
            st.error("**❌ Q10 FAIL:** Incorrect branch referral")
        
        comments = st.text_area("Additional Comments", placeholder="Enter any additional comments here...")
        
        # Submit button with primary styling
        col_submit1, col_submit2, col_submit3 = st.columns([1, 2, 1])
        with col_submit2:
            submitted = st.form_submit_button("📥 Submit Audit", type="primary", use_container_width=True)
        
        if submitted:
            if not all([consultant, team_leader, client_id]):
                st.error("Please fill all required fields (*)")
            else:
                data = {
                    "consultant": consultant,
                    "team_leader": team_leader,
                    "client_id": client_id,
                    "audit_date": audit_date.isoformat(),
                    "score": score_percentage,
                    "comments": comments,
                    **answers
                }
                
                try:
                    response = supabase.table("audits").insert(data).execute()
                    
                    # Store the submitted data in session state
                    st.session_state.last_submitted_data = data
                    st.session_state.form_submitted = True
                    
                    # Don't show the success message here - it will show after rerun
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error submitting audit: {e}")

with tab2:
    st.markdown("<h2 style='text-align: center;'>View Audits</h2>", unsafe_allow_html=True)
    
    try:
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        
        if response.data:
            df = pd.DataFrame(response.data)
            
            # Calculate metrics
            total_audits = len(df)
            avg_score = df['score'].mean()
            q2_no_count = len(df[df['q2'] == 'No'])
            q10_no_count = len(df[df['q10'] == 'No'])
            critical_failures = len(df[(df['q2'] == 'No') | (df['q10'] == 'No')])
            
            # Show metrics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Audits", total_audits)
            with col2:
                st.metric("Average Score", f"{avg_score:.1f}%")
            with col3:
                st.metric("Critical Failures", critical_failures)
                st.caption("Q2 or Q10 = 'No'")
            with col4:
                pass_rate = ((total_audits - critical_failures) / total_audits * 100) if total_audits > 0 else 0
                st.metric("Pass Rate", f"{pass_rate:.1f}%")
            
            # Dataframe with critical indicators
            def highlight_critical(row):
                if row['q2'] == 'No' or row['q10'] == 'No':
                    return ['background-color: #ffcccc'] * len(row)
                return [''] * len(row)
            
            st.subheader("All Audits")
            display_df = df[['id', 'audit_date', 'consultant', 'team_leader', 
                           'client_id', 'score', 'q2', 'q10', 'comments']].copy()
            
            # Apply styling
            styled_df = display_df.style.apply(highlight_critical, axis=1)
            
            # Display the dataframe
            st.dataframe(
                styled_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "audit_date": "Date",
                    "consultant": "Consultant",
                    "team_leader": "Team Lead",
                    "client_id": "Client ID",
                    "score": st.column_config.NumberColumn(
                        "Score", 
                        format="%.1f %%",
                        help="Score = 0% if Q2 or Q10 = 'No'"
                    ),
                    "q2": st.column_config.TextColumn(
                        "Q2 ⚠️", 
                        width="small",
                        help="Customer validation (POPI Act)"
                    ),
                    "q10": st.column_config.TextColumn(
                        "Q10 ⚠️", 
                        width="small",
                        help="Branch referral correctness"
                    ),
                    "comments": "Comments"
                }
            )
            
            # Download button
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download All Audits as CSV",
                data=csv,
                file_name="audits.csv",
                mime="text/csv"
            )
            
        else:
            st.info("No audits found. Submit your first audit above!")
            
    except Exception as e:
        st.error(f"Error fetching audits: {e}")

with tab3:
    st.markdown("<h2 style='text-align: center;'>📈 Analytics Dashboard</h2>", unsafe_allow_html=True)
    
    try:
        # Fetch data for analytics
        response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
        
        if not response.data:
            st.info("No audit data available for analytics. Submit some audits first!")
        else:
            df = pd.DataFrame(response.data)
            
            # Convert audit_date to datetime
            df['audit_date'] = pd.to_datetime(df['audit_date'])
            df['week'] = df['audit_date'].dt.isocalendar().week
            df['month'] = df['audit_date'].dt.month
            df['day'] = df['audit_date'].dt.date
            
            # Calculate additional metrics
            total_audits = len(df)
            avg_score = df['score'].mean()
            critical_failures = len(df[(df['q2'] == 'No') | (df['q10'] == 'No')])
            pass_rate = ((total_audits - critical_failures) / total_audits * 100) if total_audits > 0 else 0
            
            # Top row - Key Metrics
            st.subheader("📊 Key Performance Indicators")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            with kpi1:
                st.metric("Total Audits", total_audits)
            with kpi2:
                st.metric("Average Score", f"{avg_score:.1f}%", 
                         delta=f"{(avg_score - 70):.1f}%" if avg_score > 70 else None)
            with kpi3:
                st.metric("Pass Rate", f"{pass_rate:.1f}%")
            with kpi4:
                st.metric("Critical Failures", critical_failures, 
                         delta_color="inverse")
            
            st.divider()
            
            # Row 1 - Performance Trends
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Performance Trend Over Time")
                
                # Daily average scores
                daily_scores = df.groupby('day')['score'].mean().reset_index()
                daily_scores['7_day_avg'] = daily_scores['score'].rolling(window=7, min_periods=1).mean()
                
                fig1 = go.Figure()
                fig1.add_trace(go.Scatter(x=daily_scores['day'], y=daily_scores['score'],
                                         mode='lines+markers', name='Daily Score',
                                         line=dict(color='royalblue', width=2)))
                fig1.add_trace(go.Scatter(x=daily_scores['day'], y=daily_scores['7_day_avg'],
                                         mode='lines', name='7-Day Average',
                                         line=dict(color='firebrick', width=3, dash='dash')))
                
                fig1.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Average Score (%)",
                    hovermode='x unified',
                    height=400
                )
                st.plotly_chart(fig1, use_container_width=True)
            
            with col2:
                st.subheader("👥 Consultant Performance")
                
                consultant_scores = df.groupby('consultant').agg({
                    'score': 'mean',
                    'id': 'count'
                }).round(1).reset_index()
                consultant_scores = consultant_scores.rename(columns={'id': 'audit_count', 'score': 'avg_score'})
                
                # Sort by average score
                consultant_scores = consultant_scores.sort_values('avg_score', ascending=True)
                
                fig2 = go.Figure(go.Bar(
                    x=consultant_scores['avg_score'],
                    y=consultant_scores['consultant'],
                    orientation='h',
                    text=consultant_scores['avg_score'].astype(str) + '%',
                    textposition='outside',
                    marker_color='lightseagreen'
                ))
                
                fig2.update_layout(
                    xaxis_title="Average Score (%)",
                    yaxis_title="Consultant",
                    height=400,
                    showlegend=False
                )
                st.plotly_chart(fig2, use_container_width=True)
            
            st.divider()
            
            # Row 2 - Question Analysis
            st.subheader("❓ Question Performance Analysis")
            
            # Calculate pass rates for each question
            question_stats = []
            for q in range(1, 13):
                q_col = f'q{q}'
                total_responses = len(df[df[q_col] != 'NA'])
                if total_responses > 0:
                    yes_count = len(df[df[q_col] == 'Yes'])
                    pass_rate_q = (yes_count / total_responses) * 100
                else:
                    pass_rate_q = 0
                
                question_stats.append({
                    'Question': f'Q{q}',
                    'Pass Rate (%)': round(pass_rate_q, 1),
                    'Critical': '⚠️' if q in [2, 10] else ''
                })
            
            question_df = pd.DataFrame(question_stats)
            
            col3, col4 = st.columns(2)
            
            with col3:
                fig3 = go.Figure(go.Bar(
                    x=question_df['Question'],
                    y=question_df['Pass Rate (%)'],
                    text=question_df['Pass Rate (%)'].astype(str) + '%',
                    textposition='auto',
                    marker_color=['#ff6b6b' if q in ['Q2', 'Q10'] else '#4ecdc4' for q in question_df['Question']]
                ))
                
                fig3.update_layout(
                    xaxis_title="Question",
                    yaxis_title="Pass Rate (%)",
                    height=400,
                    xaxis={'categoryorder': 'total descending'}
                )
                st.plotly_chart(fig3, use_container_width=True)
            
            with col4:
                st.subheader("Question Details")
                st.dataframe(
                    question_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Question": "Question",
                        "Pass Rate (%)": st.column_config.NumberColumn("Pass Rate", format="%.1f %%"),
                        "Critical": st.column_config.TextColumn("Critical", width="small")
                    }
                )
            
            st.divider()
            
            # Row 3 - Critical Failures Analysis
            st.subheader("⚠️ Critical Failures Analysis")
            
            # Calculate failure reasons
            q2_failures = len(df[df['q2'] == 'No'])
            q10_failures = len(df[df['q10'] == 'No'])
            both_failures = len(df[(df['q2'] == 'No') & (df['q10'] == 'No')])
            
            failure_data = pd.DataFrame({
                'Failure Type': ['Q2 Only (Validation)', 'Q10 Only (Referral)', 'Both Q2 & Q10'],
                'Count': [
                    q2_failures - both_failures,
                    q10_failures - both_failures,
                    both_failures
                ]
            })
            
            col5, col6 = st.columns(2)
            
            with col5:
                fig4 = go.Figure(go.Pie(
                    labels=failure_data['Failure Type'],
                    values=failure_data['Count'],
                    hole=0.4,
                    marker_colors=['#ff9999', '#66b3ff', '#99ff99']
                ))
                
                fig4.update_layout(
                    height=400,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
                )
                st.plotly_chart(fig4, use_container_width=True)
            
            with col6:
                # Critical failures by consultant
                critical_df = df[(df['q2'] == 'No') | (df['q10'] == 'No')]
                if not critical_df.empty:
                    critical_by_consultant = critical_df['consultant'].value_counts().reset_index()
                    critical_by_consultant.columns = ['Consultant', 'Critical Failures']
                    
                    fig5 = go.Figure(go.Bar(
                        x=critical_by_consultant['Consultant'],
                        y=critical_by_consultant['Critical Failures'],
                        marker_color='indianred'
                    ))
                    
                    fig5.update_layout(
                        xaxis_title="Consultant",
                        yaxis_title="Critical Failures",
                        height=400
                    )
                    st.plotly_chart(fig5, use_container_width=True)
                else:
                    st.info("No critical failures to display")
            
            st.divider()
            
            # Row 4 - Score Distribution
            st.subheader("📊 Score Distribution")
            
            col7, col8 = st.columns(2)
            
            with col7:
                # Histogram of scores
                fig6 = px.histogram(df, x='score', nbins=20,
                                   title="Distribution of Audit Scores",
                                   labels={'score': 'Score (%)', 'count': 'Number of Audits'},
                                   color_discrete_sequence=['lightseagreen'])
                
                fig6.update_layout(
                    height=400,
                    bargap=0.1,
                    xaxis_range=[0, 100]
                )
                st.plotly_chart(fig6, use_container_width=True)
            
            with col8:
                # Score categories
                def get_score_category(score):
                    if score == 0:
                        return 'Critical Failure'
                    elif score >= 85:
                        return 'Excellent (85-100%)'
                    elif score >= 70:
                        return 'Good (70-84%)'
                    else:
                        return 'Needs Improvement (<70%)'
                
                df['score_category'] = df['score'].apply(get_score_category)
                category_counts = df['score_category'].value_counts().reset_index()
                category_counts.columns = ['Category', 'Count']
                
                fig7 = go.Figure(go.Bar(
                    x=category_counts['Category'],
                    y=category_counts['Count'],
                    text=category_counts['Count'],
                    textposition='auto',
                    marker_color=['#ff6b6b', '#4ecdc4', '#ffe66d', '#95e1d3']
                ))
                
                fig7.update_layout(
                    xaxis_title="Score Category",
                    yaxis_title="Number of Audits",
                    height=400
                )
                st.plotly_chart(fig7, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
