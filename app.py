import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Page config
st.set_page_config(
    page_title="Digital Support(QA Scorecard System)",
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
st.markdown("<h1 style='text-align: center;'>📊 Digital Support(QA Scorecard System)</h1>", unsafe_allow_html=True)

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
                ["Aobakwe Peter", "Daychannel Jasson", "Diyajal Ramesar", "Golden Raphulu", "Karabo Ratau", "Moreen Nkosi",],
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
            
            # Convert audit_date to datetime and extract date components
            df['audit_date'] = pd.to_datetime(df['audit_date'])
            df['year_month'] = df['audit_date'].dt.strftime('%Y-%m')  # Format: 2024-01
            df['month_name'] = df['audit_date'].dt.strftime('%B %Y')  # Format: January 2024
            df['week'] = df['audit_date'].dt.isocalendar().week
            df['month'] = df['audit_date'].dt.month
            df['day'] = df['audit_date'].dt.date
            df['year'] = df['audit_date'].dt.year
            
            # ========== FILTERS SECTION ==========
            st.subheader("🔍 Filter Analytics Data")
            
            # Create columns for filters
            col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
            
            with col_filter1:
                # Month filter (multi-select)
                all_months = sorted(df['month_name'].unique(), reverse=True)
                selected_months = st.multiselect(
                    "Select Month(s)",
                    options=all_months,
                    default=all_months[:3] if len(all_months) >= 3 else all_months,
                    help="Select one or more months to filter"
                )
            
            with col_filter2:
                # Consultant filter (multi-select)
                all_consultants = sorted(df['consultant'].unique())
                selected_consultants = st.multiselect(
                    "Select Consultant(s)",
                    options=all_consultants,
                    default=all_consultants,
                    help="Select one or more consultants"
                )
            
            with col_filter3:
                # Date range filter
                min_date = df['audit_date'].min().date()
                max_date = df['audit_date'].max().date()
                
                date_range = st.date_input(
                    "Date Range",
                    value=[min_date, max_date],
                    min_value=min_date,
                    max_value=max_date
                )
            
            with col_filter4:
                # Score range filter
                min_score = st.slider(
                    "Minimum Score",
                    min_value=0,
                    max_value=100,
                    value=0,
                    help="Filter by minimum score percentage"
                )
                
                # Critical failures toggle
                show_critical_only = st.checkbox("Show Critical Failures Only", value=False)
            
            # Apply filters
            filtered_df = df.copy()
            
            # Apply month filter
            if selected_months:
                filtered_df = filtered_df[filtered_df['month_name'].isin(selected_months)]
            
            # Apply consultant filter
            if selected_consultants:
                filtered_df = filtered_df[filtered_df['consultant'].isin(selected_consultants)]
            
            # Apply date range filter
            if len(date_range) == 2:
                start_date, end_date = date_range
                filtered_df = filtered_df[
                    (filtered_df['audit_date'].dt.date >= start_date) &
                    (filtered_df['audit_date'].dt.date <= end_date)
                ]
            
            # Apply score filter
            filtered_df = filtered_df[filtered_df['score'] >= min_score]
            
            # Apply critical failures filter
            if show_critical_only:
                filtered_df = filtered_df[(filtered_df['q2'] == 'No') | (filtered_df['q10'] == 'No')]
            
            # Show filter summary
            st.info(f"📊 **Showing {len(filtered_df)} out of {len(df)} audits**")
            
            if len(filtered_df) == 0:
                st.warning("No data matches your filters. Try adjusting filter criteria.")
                st.stop()
            
            # ========== ANALYTICS DASHBOARD ==========
            st.divider()
            
            # Calculate filtered metrics
            total_audits_filtered = len(filtered_df)
            avg_score_filtered = filtered_df['score'].mean()
            critical_failures_filtered = len(filtered_df[(filtered_df['q2'] == 'No') | (filtered_df['q10'] == 'No')])
            pass_rate_filtered = ((total_audits_filtered - critical_failures_filtered) / total_audits_filtered * 100) if total_audits_filtered > 0 else 0
            
            # Top row - Key Metrics (FILTERED)
            st.subheader("📊 Key Performance Indicators (Filtered)")
            kpi1, kpi2, kpi3, kpi4 = st.columns(4)
            
            with kpi1:
                delta_audits = total_audits_filtered - len(df)
                st.metric("Total Audits", total_audits_filtered, 
                         delta=f"{delta_audits:+d}" if delta_audits != 0 else None)
            
            with kpi2:
                delta_score = avg_score_filtered - df['score'].mean()
                st.metric("Average Score", f"{avg_score_filtered:.1f}%", 
                         delta=f"{delta_score:+.1f}%" if delta_score != 0 else None)
            
            with kpi3:
                delta_pass = pass_rate_filtered - ((len(df) - len(df[(df['q2'] == 'No') | (df['q10'] == 'No')])) / len(df) * 100 if len(df) > 0 else 0)
                st.metric("Pass Rate", f"{pass_rate_filtered:.1f}%",
                         delta=f"{delta_pass:+.1f}%" if delta_pass != 0 else None)
            
            with kpi4:
                delta_critical = critical_failures_filtered - len(df[(df['q2'] == 'No') | (df['q10'] == 'No')])
                st.metric("Critical Failures", critical_failures_filtered, 
                         delta=f"{delta_critical:+d}" if delta_critical != 0 else None,
                         delta_color="inverse")
            
            st.divider()
            
            # Row 1 - Performance Trends (FILTERED)
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Performance Trend (Filtered)")
                
                if len(filtered_df) > 1:
                    # Daily average scores
                    daily_scores = filtered_df.groupby('day')['score'].mean().reset_index()
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
                else:
                    st.info("Need at least 2 audits to show trend")
            
            with col2:
                st.subheader("👥 Consultant Performance (Filtered)")
                
                if len(filtered_df) > 0:
                    consultant_scores = filtered_df.groupby('consultant').agg({
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
                else:
                    st.info("No consultant data available")
            
            st.divider()
            
            # Row 2 - Question Analysis (FILTERED)
            st.subheader("❓ Question Performance Analysis (Filtered)")
            
            if len(filtered_df) > 0:
                # Calculate pass rates for each question
                question_stats = []
                for q in range(1, 13):
                    q_col = f'q{q}'
                    total_responses = len(filtered_df[filtered_df[q_col] != 'NA'])
                    if total_responses > 0:
                        yes_count = len(filtered_df[filtered_df[q_col] == 'Yes'])
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
            else:
                st.info("No question data available for current filters")
            
            st.divider()
            
            # Row 3 - Month-wise Comparison
            st.subheader("📅 Monthly Performance Comparison")
            
            if len(filtered_df) > 0 and len(selected_months) > 1:
                # Group by month
                monthly_stats = filtered_df.groupby('month_name').agg({
                    'score': ['mean', 'count'],
                    'id': 'count'
                }).round(1).reset_index()
                
                # Flatten column names
                monthly_stats.columns = ['Month', 'Avg_Score', 'Audit_Count', 'Total']
                
                # Sort by month chronologically
                monthly_stats['Month_Date'] = pd.to_datetime(monthly_stats['Month'], format='%B %Y')
                monthly_stats = monthly_stats.sort_values('Month_Date')
                
                col5, col6 = st.columns(2)
                
                with col5:
                    # Bar chart for monthly scores
                    fig4 = go.Figure(go.Bar(
                        x=monthly_stats['Month'],
                        y=monthly_stats['Avg_Score'],
                        text=monthly_stats['Avg_Score'].astype(str) + '%',
                        textposition='auto',
                        marker_color='cornflowerblue'
                    ))
                    
                    fig4.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Average Score (%)",
                        height=400
                    )
                    st.plotly_chart(fig4, use_container_width=True)
                
                with col6:
                    # Line chart for trend
                    fig5 = go.Figure(go.Scatter(
                        x=monthly_stats['Month'],
                        y=monthly_stats['Avg_Score'],
                        mode='lines+markers',
                        line=dict(color='royalblue', width=3),
                        marker=dict(size=10)
                    ))
                    
                    fig5.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Average Score (%)",
                        height=400
                    )
                    st.plotly_chart(fig5, use_container_width=True)
            else:
                st.info("Select multiple months to see monthly comparison")
            
            st.divider()
            
            # Row 4 - Export Filtered Data
            st.subheader("💾 Export Filtered Data")
            
            col7, col8, col9 = st.columns(3)
            
            with col7:
                # Show filtered data preview
                st.write(f"**Filtered Data Preview** ({len(filtered_df)} rows)")
                st.dataframe(
                    filtered_df[['audit_date', 'consultant', 'team_leader', 'client_id', 'score']].head(10),
                    use_container_width=True,
                    hide_index=True
                )
            
            with col8:
                # Download filtered data as CSV
                csv_filtered = filtered_df.to_csv(index=False)
                st.download_button(
                    label="📥 Download Filtered Data (CSV)",
                    data=csv_filtered,
                    file_name=f"filtered_audits_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            
            with col9:
                # Reset filters button
                if st.button("🔄 Reset All Filters", use_container_width=True):
                    st.rerun()
            
            # Quick filter presets
            st.subheader("⚡ Quick Filter Presets")
            
            preset_col1, preset_col2, preset_col3, preset_col4 = st.columns(4)
            
            with preset_col1:
                if st.button("📅 Last 30 Days", use_container_width=True):
                    thirty_days_ago = (datetime.now() - timedelta(days=30)).date()
                    filtered_df = df[df['audit_date'].dt.date >= thirty_days_ago]
                    st.rerun()
            
            with preset_col2:
                if st.button("👑 Top Performers", use_container_width=True):
                    filtered_df = df[df['score'] >= 85]
                    st.rerun()
            
            with preset_col3:
                if st.button("⚠️ Critical Issues", use_container_width=True):
                    filtered_df = df[(df['q2'] == 'No') | (df['q10'] == 'No')]
                    st.rerun()
            
            with preset_col4:
                if st.button("📊 All Data", use_container_width=True):
                    filtered_df = df
                    st.rerun()
            
    except Exception as e:
        st.error(f"Error loading analytics: {e}")
