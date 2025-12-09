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

# ==================== AI ANALYTICS FUNCTIONS ====================

def generate_ai_insights(df, selected_consultant=None, selected_team=None, selected_dept=None):
    """Generate AI-powered insights from audit data"""
    insights = []
    
    if df.empty:
        return ["📊 Not enough data for AI insights yet. Submit more audits!"]
    
    # Overall performance trend
    if len(df) >= 5:
        df_sorted = df.sort_values('audit_date')
        trend = np.polyfit(range(len(df_sorted)), df_sorted['score'], 1)[0]
        if trend > 1:
            insights.append(f"📈 **Positive Trend**: Overall scores improving by {trend:.1f}% per audit")
        elif trend < -1:
            insights.append(f"📉 **Negative Trend**: Overall scores declining by {abs(trend):.1f}% per audit")
    
    # Department comparison
    if len(df['department'].unique()) > 1:
        dept_perf = df.groupby('department')['score'].mean().sort_values(ascending=False)
        best_dept = dept_perf.index[0]
        worst_dept = dept_perf.index[-1]
        insights.append(f"🏆 **Top Department**: {best_dept} ({dept_perf.iloc[0]:.1f}%)")
        insights.append(f"⚡ **Needs Attention**: {worst_dept} ({dept_perf.iloc[-1]:.1f}%)")
    
    # Question performance analysis
    question_cols = [f'q{i}' for i in range(1, 13) if f'q{i}' in df.columns]
    if question_cols:
        q_performance = {}
        for q in question_cols:
            if q in df.columns:
                yes_count = (df[q] == 'Yes').sum()
                total_count = len(df[df[q] != 'NA'])
                if total_count > 0:
                    q_performance[q] = (yes_count / total_count) * 100
        
        if q_performance:
            worst_q = min(q_performance, key=q_performance.get)
            best_q = max(q_performance, key=q_performance.get)
            insights.append(f"❓ **Weakest Question**: {worst_q.upper()} ({q_performance[worst_q]:.1f}% pass rate)")
            insights.append(f"✅ **Strongest Question**: {best_q.upper()} ({q_performance[best_q]:.1f}% pass rate)")
    
    # Consultant-specific insights
    if selected_consultant and selected_consultant in df['consultant'].values:
        consultant_df = df[df['consultant'] == selected_consultant]
        if len(consultant_df) >= 3:
            consultant_avg = consultant_df['score'].mean()
            overall_avg = df['score'].mean()
            if consultant_avg > overall_avg + 5:
                insights.append(f"🌟 **Star Performer**: {selected_consultant} is {consultant_avg-overall_avg:.1f}% above average!")
            elif consultant_avg < overall_avg - 5:
                insights.append(f"📚 **Training Opportunity**: {selected_consultant} is {overall_avg-consultant_avg:.1f}% below average")
    
    # Critical failures analysis
    critical_cols = ['q2', 'q10', 'q3', 'q6', 'q7']  # Common critical questions
    critical_cols = [c for c in critical_cols if c in df.columns]
    if critical_cols:
        critical_failures = df[critical_cols].apply(lambda x: (x == 'No').any(), axis=1).sum()
        failure_rate = (critical_failures / len(df)) * 100
        if failure_rate > 20:
            insights.append(f"⚠️ **High Critical Failures**: {failure_rate:.1f}% of audits have critical failures")
    
    if not insights:
        insights.append("📊 Submit more audits to generate detailed insights")
    
    return insights

def generate_coaching_plan(df, consultant_name):
    """Generate personalized coaching plan based on audit history"""
    if consultant_name not in df['consultant'].values:
        return ["Select a consultant with audit history"]
    
    consultant_df = df[df['consultant'] == consultant_name]
    if len(consultant_df) < 3:
        return ["Need at least 3 audits to generate coaching plan"]
    
    plan = []
    
    # Overall performance
    consultant_avg = consultant_df['score'].mean()
    overall_avg = df['score'].mean()
    
    plan.append(f"## 🎯 Coaching Plan for {consultant_name}")
    plan.append(f"**Current Average**: {consultant_avg:.1f}%")
    plan.append(f"**Team Average**: {overall_avg:.1f}%")
    plan.append(f"**Performance Gap**: {consultant_avg - overall_avg:+.1f}%")
    
    # Identify weak areas
    question_cols = [f'q{i}' for i in range(1, 13) if f'q{i}' in df.columns]
    weak_areas = []
    
    for q in question_cols:
        if q in consultant_df.columns:
            consultant_yes = (consultant_df[q] == 'Yes').sum()
            consultant_total = len(consultant_df[consultant_df[q] != 'NA'])
            if consultant_total > 0:
                consultant_rate = (consultant_yes / consultant_total) * 100
                
                overall_yes = (df[q] == 'Yes').sum()
                overall_total = len(df[df[q] != 'NA'])
                if overall_total > 0:
                    overall_rate = (overall_yes / overall_total) * 100
                    
                    if consultant_rate < 70 and consultant_rate < overall_rate - 10:
                        weak_areas.append({
                            'question': q.upper(),
                            'consultant_rate': consultant_rate,
                            'team_rate': overall_rate,
                            'gap': overall_rate - consultant_rate
                        })
    
    if weak_areas:
        plan.append("\n## 🎯 Areas Needing Improvement:")
        for area in sorted(weak_areas, key=lambda x: x['gap'], reverse=True)[:3]:
            plan.append(f"- **{area['question']}**: {area['consultant_rate']:.1f}% vs team {area['team_rate']:.1f}% (gap: {area['gap']:.1f}%)")
    
    # Trend analysis
    if len(consultant_df) >= 4:
        dates = pd.to_datetime(consultant_df['audit_date'])
        scores = consultant_df['score'].values
        dates_numeric = np.array([date.timestamp() for date in dates])
        
        # Calculate trend
        if len(dates_numeric) > 1:
            model = LinearRegression()
            model.fit(dates_numeric.reshape(-1, 1), scores)
            trend = model.coef_[0] * (24*3600*30)  # Per month trend
            
            if trend > 5:
                plan.append(f"\n📈 **Positive Trend**: Improving by {trend:.1f}% per month")
                plan.append("**Action**: Continue current practices, consider mentoring others")
            elif trend < -5:
                plan.append(f"\n📉 **Negative Trend**: Declining by {abs(trend):.1f}% per month")
                plan.append("**Action**: Schedule one-on-one coaching session")
            else:
                plan.append("\n📊 **Stable Performance**: Consistent scores")
                plan.append("**Action**: Focus on specific skill development")
    
    # Critical failures
    critical_cols = ['q2', 'q10', 'q3', 'q6', 'q7']
    critical_cols = [c for c in critical_cols if c in consultant_df.columns]
    
    critical_fails = []
    for q in critical_cols:
        if q in consultant_df.columns:
            fails = (consultant_df[q] == 'No').sum()
            if fails > 0:
                critical_fails.append(f"{q.upper()}: {fails} failure(s)")
    
    if critical_fails:
        plan.append("\n⚠️ **Critical Issues to Address:**")
        plan.extend([f"- {fail}" for fail in critical_fails])
        plan.append("**Priority**: Address these immediately as they cause 0% scores")
    
    # Recommendations
    plan.append("\n## 🎯 Recommended Actions:")
    
    if consultant_avg < 70:
        plan.append("1. **Immediate Coaching**: Schedule daily check-ins for 2 weeks")
        plan.append("2. **Shadowing**: Pair with top performer for a week")
        plan.append("3. **Focused Training**: Target lowest scoring questions")
    elif consultant_avg < 85:
        plan.append("1. **Weekly Review**: Analyze 2 audits per week with manager")
        plan.append("2. **Skill Workshops**: Attend department training sessions")
        plan.append("3. **Peer Review**: Exchange audits with colleague for feedback")
    else:
        plan.append("1. **Mentor Role**: Start mentoring newer team members")
        plan.append("2. **Process Improvement**: Identify areas for department improvement")
        plan.append("3. **Advanced Training**: Prepare for team leader role")
    
    return plan

def predict_future_scores(df, consultant_name=None, days_ahead=30):
    """Predict future scores using linear regression"""
    if df.empty or len(df) < 5:
        return None, None
    
    if consultant_name:
        df = df[df['consultant'] == consultant_name]
        if len(df) < 3:
            return None, None
    
    # Prepare data
    df_sorted = df.sort_values('audit_date')
    dates = pd.to_datetime(df_sorted['audit_date'])
    scores = df_sorted['score'].values
    
    # Convert dates to numeric (days since first audit)
    dates_numeric = np.array([(date - dates.min()).days for date in dates])
    
    # Train linear regression model
    model = LinearRegression()
    model.fit(dates_numeric.reshape(-1, 1), scores)
    
    # Predict future
    last_date = dates_numeric[-1]
    future_dates = np.array([last_date + days_ahead])
    predicted_score = model.predict(future_dates.reshape(-1, 1))[0]
    
    # Ensure prediction is within bounds
    predicted_score = max(0, min(100, predicted_score))
    
    # Calculate confidence (R-squared)
    r_squared = model.score(dates_numeric.reshape(-1, 1), scores)
    confidence = r_squared * 100
    
    return predicted_score, confidence

# ==================== ANALYTICS DASHBOARD ====================

st.markdown("<h1 style='text-align: center;'>🤖 AI-Powered Analytics Dashboard</h1>", unsafe_allow_html=True)

try:
    # Fetch all audits
    response = supabase.table("audits").select("*").order("audit_date", desc=True).execute()
    
    if not response.data:
        st.info("No audit data available for analytics. Submit some audits first!")
        st.stop()
    
    df = pd.DataFrame(response.data)
    
    # Ensure department column exists
    if 'department' not in df.columns:
        df['department'] = 'Not Assigned'
    
    # Convert audit_date to datetime
    df['audit_date'] = pd.to_datetime(df['audit_date'], format='ISO8601')
    df['date'] = df['audit_date'].dt.date
    df['week'] = df['audit_date'].dt.isocalendar().week
    df['month'] = df['audit_date'].dt.strftime('%Y-%m')
    df['month_name'] = df['audit_date'].dt.strftime('%B %Y')
    
    # ==================== FILTERS SECTION ====================
    st.subheader("🔍 Filter Analytics Data")
    
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)
    
    with filter_col1:
        # Department filter
        all_departments = ['All'] + sorted(df['department'].unique().tolist())
        selected_department = st.selectbox(
            "Select Department",
            all_departments,
            index=0
        )
    
    with filter_col2:
        # Team Leader filter
        if selected_department != 'All':
            team_leaders = ['All'] + sorted(df[df['department'] == selected_department]['team_leader'].unique().tolist())
        else:
            team_leaders = ['All'] + sorted(df['team_leader'].unique().tolist())
        
        selected_team_leader = st.selectbox(
            "Select Team Leader",
            team_leaders,
            index=0
        )
    
    with filter_col3:
        # Consultant filter
        if selected_team_leader != 'All':
            consultants = ['All'] + sorted(df[df['team_leader'] == selected_team_leader]['consultant'].unique().tolist())
        elif selected_department != 'All':
            consultants = ['All'] + sorted(df[df['department'] == selected_department]['consultant'].unique().tolist())
        else:
            consultants = ['All'] + sorted(df['consultant'].unique().tolist())
        
        selected_consultant = st.selectbox(
            "Select Consultant",
            consultants,
            index=0
        )
    
    with filter_col4:
        # Date range filter
        min_date = df['audit_date'].min().date()
        max_date = df['audit_date'].max().date()
        
        date_range = st.date_input(
            "Date Range",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
    
    # Apply filters
    filtered_df = df.copy()
    
    if selected_department != 'All':
        filtered_df = filtered_df[filtered_df['department'] == selected_department]
    
    if selected_team_leader != 'All':
        filtered_df = filtered_df[filtered_df['team_leader'] == selected_team_leader]
    
    if selected_consultant != 'All':
        filtered_df = filtered_df[filtered_df['consultant'] == selected_consultant]
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['audit_date'].dt.date >= start_date) &
            (filtered_df['audit_date'].dt.date <= end_date)
        ]
    
    st.info(f"📊 **Showing {len(filtered_df)} out of {len(df)} audits**")
    
    if len(filtered_df) == 0:
        st.warning("No data matches your filters. Try adjusting filter criteria.")
        st.stop()
    
    # ==================== KEY METRICS ====================
    st.subheader("📊 Performance Metrics")
    
    # Calculate metrics
    total_audits = len(filtered_df)
    avg_score = filtered_df['score'].mean()
    
    # Calculate critical failures
    critical_questions = ['q2', 'q10', 'q3', 'q6', 'q7']
    critical_questions = [q for q in critical_questions if q in filtered_df.columns]
    critical_failures = 0
    if critical_questions:
        critical_failures = filtered_df[critical_questions].apply(lambda x: (x == 'No').any(), axis=1).sum()
    
    pass_rate = ((total_audits - critical_failures) / total_audits * 100) if total_audits > 0 else 0
    
    # Show metrics
    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5 = st.columns(5)
    
    with metric_col1:
        st.metric("Total Audits", total_audits)
    
    with metric_col2:
        st.metric("Average Score", f"{avg_score:.1f}%")
    
    with metric_col3:
        st.metric("Critical Failures", critical_failures, delta_color="inverse")
    
    with metric_col4:
        st.metric("Pass Rate", f"{pass_rate:.1f}%")
    
    with metric_col5:
        # Performance trend
        if len(filtered_df) >= 2:
            df_sorted = filtered_df.sort_values('audit_date')
            first_half = df_sorted.iloc[:len(df_sorted)//2]['score'].mean()
            second_half = df_sorted.iloc[len(df_sorted)//2:]['score'].mean()
            trend = second_half - first_half
            trend_label = f"{trend:+.1f}%"
            st.metric("Trend", trend_label, delta=trend_label)
        else:
            st.metric("Trend", "N/A")
    
    # ==================== AI INSIGHTS ====================
    st.subheader("🤖 AI Insights & Recommendations")
    
    insights = generate_ai_insights(
        filtered_df, 
        selected_consultant if selected_consultant != 'All' else None,
        selected_team_leader if selected_team_leader != 'All' else None,
        selected_department if selected_department != 'All' else None
    )
    
    for insight in insights[:5]:  # Show top 5 insights
        st.info(insight)
    
    # ==================== VISUAL ANALYTICS ====================
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📈 Performance Trend")
        
        if len(filtered_df) >= 2:
            # Daily average scores
            daily_scores = filtered_df.groupby('date')['score'].mean().reset_index()
            daily_scores['7_day_avg'] = daily_scores['score'].rolling(window=7, min_periods=1).mean()
            
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=daily_scores['date'],
                y=daily_scores['score'],
                mode='lines+markers',
                name='Daily Score',
                line=dict(color='royalblue', width=2)
            ))
            fig1.add_trace(go.Scatter(
                x=daily_scores['date'],
                y=daily_scores['7_day_avg'],
                mode='lines',
                name='7-Day Average',
                line=dict(color='firebrick', width=3, dash='dash')
            ))
            
            fig1.update_layout(
                xaxis_title="Date",
                yaxis_title="Average Score (%)",
                height=400,
                hovermode='x unified'
            )
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("Need at least 2 audits to show trend")
    
    with col_chart2:
        st.subheader("📊 Score Distribution")
        
        fig2 = px.histogram(
            filtered_df, 
            x='score', 
            nbins=20,
            title="Distribution of Audit Scores",
            labels={'score': 'Score (%)', 'count': 'Number of Audits'},
            color_discrete_sequence=['lightseagreen']
        )
        
        fig2.update_layout(
            height=400,
            bargap=0.1,
            xaxis_range=[0, 100]
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # ==================== COMPARATIVE ANALYSIS ====================
    st.subheader("📋 Comparative Analysis")
    
    comp_col1, comp_col2 = st.columns(2)
    
    with comp_col1:
        # Department/Team comparison
        if selected_department == 'All' and len(filtered_df['department'].unique()) > 1:
            st.write("**Department Performance**")
            dept_stats = filtered_df.groupby('department').agg({
                'score': 'mean',
                'id': 'count'
            }).round(1).reset_index()
            dept_stats.columns = ['Department', 'Avg Score', 'Audit Count']
            
            fig3 = go.Figure(go.Bar(
                x=dept_stats['Avg Score'],
                y=dept_stats['Department'],
                orientation='h',
                text=dept_stats['Avg Score'].astype(str) + '%',
                textposition='outside',
                marker_color='cornflowerblue'
            ))
            
            fig3.update_layout(
                xaxis_title="Average Score (%)",
                yaxis_title="Department",
                height=300
            )
            st.plotly_chart(fig3, use_container_width=True)
        
        elif selected_team_leader == 'All' and len(filtered_df['team_leader'].unique()) > 1:
            st.write("**Team Leader Performance**")
            team_stats = filtered_df.groupby('team_leader').agg({
                'score': 'mean',
                'id': 'count'
            }).round(1).reset_index()
            team_stats.columns = ['Team Leader', 'Avg Score', 'Audit Count']
            team_stats = team_stats.sort_values('Avg Score', ascending=True).tail(10)
            
            fig3 = go.Figure(go.Bar(
                x=team_stats['Avg Score'],
                y=team_stats['Team Leader'],
                orientation='h',
                text=team_stats['Avg Score'].astype(str) + '%',
                textposition='outside',
                marker_color='lightseagreen'
            ))
            
            fig3.update_layout(
                xaxis_title="Average Score (%)",
                yaxis_title="Team Leader",
                height=300
            )
            st.plotly_chart(fig3, use_container_width=True)
    
    with comp_col2:
        # Consultant leaderboard
        if len(filtered_df['consultant'].unique()) > 1:
            st.write("**Top Performers**")
            consultant_stats = filtered_df.groupby('consultant').agg({
                'score': 'mean',
                'id': 'count'
            }).round(1).reset_index()
            consultant_stats.columns = ['Consultant', 'Avg Score', 'Audit Count']
            
            # Show top and bottom performers
            top_5 = consultant_stats.sort_values('Avg Score', ascending=False).head(5)
            bottom_5 = consultant_stats.sort_values('Avg Score', ascending=True).head(5)
            
            fig4 = go.Figure()
            
            # Add top performers
            fig4.add_trace(go.Bar(
                x=top_5['Avg Score'],
                y=top_5['Consultant'],
                orientation='h',
                name='Top 5',
                marker_color='green',
                text=top_5['Avg Score'].astype(str) + '%',
                textposition='outside'
            ))
            
            # Add bottom performers
            fig4.add_trace(go.Bar(
                x=bottom_5['Avg Score'],
                y=bottom_5['Consultant'],
                orientation='h',
                name='Bottom 5',
                marker_color='red',
                text=bottom_5['Avg Score'].astype(str) + '%',
                textposition='outside'
            ))
            
            fig4.update_layout(
                xaxis_title="Average Score (%)",
                yaxis_title="Consultant",
                height=300,
                barmode='group'
            )
            st.plotly_chart(fig4, use_container_width=True)
    
    # ==================== QUESTION ANALYSIS ====================
    st.subheader("❓ Question Performance Analysis")
    
    # Calculate pass rates for each question
    question_stats = []
    for q in range(1, 13):
        q_col = f'q{q}'
        if q_col in filtered_df.columns:
            total_responses = len(filtered_df[filtered_df[q_col] != 'NA'])
            if total_responses > 0:
                yes_count = len(filtered_df[filtered_df[q_col] == 'Yes'])
                pass_rate_q = (yes_count / total_responses) * 100
                
                # Identify critical questions
                is_critical = False
                if selected_department == 'Digital Support' and q in [2, 10]:
                    is_critical = True
                elif selected_department == 'ARQ' and q in [3, 6, 10]:
                    is_critical = True
                elif selected_department == 'DVQ (KYC)' and q in [3, 4, 7]:
                    is_critical = True
                elif selected_department == 'Dialler' and q in [1, 2]:
                    is_critical = True
                
                question_stats.append({
                    'Question': f'Q{q}',
                    'Pass Rate (%)': round(pass_rate_q, 1),
                    'Critical': '⚠️' if is_critical else ''
                })
    
    if question_stats:
        question_df = pd.DataFrame(question_stats)
        question_df = question_df.sort_values('Pass Rate (%)', ascending=True)
        
        fig5 = go.Figure(go.Bar(
            x=question_df['Pass Rate (%)'],
            y=question_df['Question'],
            orientation='h',
            text=question_df['Pass Rate (%)'].astype(str) + '%',
            textposition='outside',
            marker_color=['#ff6b6b' if '⚠️' in crit else '#4ecdc4' for crit in question_df['Critical']]
        ))
        
        fig5.update_layout(
            xaxis_title="Pass Rate (%)",
            yaxis_title="Question",
            height=400
        )
        st.plotly_chart(fig5, use_container_width=True)
    
    # ==================== PREDICTIVE ANALYTICS ====================
    st.subheader("🔮 Predictive Analytics")
    
    pred_col1, pred_col2, pred_col3 = st.columns(3)
    
    with pred_col1:
        # Consultant selector for predictions
        if selected_consultant == 'All' and len(filtered_df['consultant'].unique()) > 1:
            pred_consultants = ['Select...'] + sorted(filtered_df['consultant'].unique().tolist())
            pred_consultant = st.selectbox(
                "Predict for Consultant",
                pred_consultants,
                index=0
            )
        else:
            pred_consultant = selected_consultant if selected_consultant != 'All' else None
    
    with pred_col2:
        # Time horizon
        prediction_days = st.slider(
            "Prediction Horizon (days)",
            min_value=7,
            max_value=90,
            value=30,
            step=7
        )
    
    with pred_col3:
        st.write("")  # Spacer
        if st.button("🔮 Generate Prediction", use_container_width=True):
            if pred_consultant and pred_consultant != 'Select...':
                predicted_score, confidence = predict_future_scores(
                    filtered_df, 
                    pred_consultant, 
                    prediction_days
                )
                
                if predicted_score is not None:
                    current_avg = filtered_df[filtered_df['consultant'] == pred_consultant]['score'].mean()
                    
                    st.success(f"**Predicted Score in {prediction_days} days:**")
                    st.metric(
                        "Prediction", 
                        f"{predicted_score:.1f}%",
                        delta=f"{predicted_score - current_avg:+.1f}% from current"
                    )
                    st.info(f"Confidence: {confidence:.1f}%")
                    
                    if predicted_score < 70:
                        st.error("⚠️ **Alert**: Predicted below passing threshold")
                        st.write("**Action**: Schedule coaching session immediately")
                    elif predicted_score < 85:
                        st.warning("⚠️ **Warning**: Predicted below excellence threshold")
                        st.write("**Action**: Monitor closely, provide additional support")
                    else:
                        st.success("✅ **Excellent**: Predicted strong performance")
                        st.write("**Action**: Consider for mentor role")
                else:
                    st.warning("Need more data for accurate predictions (minimum 3 audits)")
            else:
                st.warning("Please select a consultant for prediction")
    
    # ==================== COACHING PLANS ====================
    st.subheader("🎯 Automated Coaching Plans")
    
    coach_col1, coach_col2 = st.columns([2, 1])
    
    with coach_col1:
        # Consultant selector for coaching plan
        if selected_consultant == 'All' and len(filtered_df['consultant'].unique()) > 1:
            coach_consultants = ['Select...'] + sorted(filtered_df['consultant'].unique().tolist())
            coach_consultant = st.selectbox(
                "Generate Coaching Plan for",
                coach_consultants,
                index=0
            )
        else:
            coach_consultant = selected_consultant if selected_consultant != 'All' else None
    
    with coach_col2:
        st.write("")  # Spacer
        if st.button("📋 Generate Coaching Plan", use_container_width=True):
            if coach_consultant and coach_consultant != 'Select...':
                coaching_plan = generate_coaching_plan(filtered_df, coach_consultant)
                
                with st.expander(f"📋 Coaching Plan for {coach_consultant}", expanded=True):
                    for line in coaching_plan:
                        if line.startswith("##"):
                            st.subheader(line[3:])
                        elif line.startswith("**"):
                            st.write(line)
                        else:
                            st.write(line)
                
                # Download coaching plan
                plan_text = "\n".join(coaching_plan)
                st.download_button(
                    label="📥 Download Coaching Plan",
                    data=plan_text,
                    file_name=f"coaching_plan_{coach_consultant}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
            else:
                st.warning("Please select a consultant for coaching plan")
    
    # ==================== EXPORT DATA ====================
    st.subheader("💾 Export Data")
    
    exp_col1, exp_col2, exp_col3 = st.columns(3)
    
    with exp_col1:
        # Export filtered data
        csv_data = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv_data,
            file_name=f"qa_analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    
    with exp_col2:
        # Export summary report
        summary_report = f"""
        QA Scorecard Analytics Report
        Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        Period: {date_range[0]} to {date_range[1]}
        Filters: Department={selected_department}, Team Leader={selected_team_leader}, Consultant={selected_consultant}
        
        SUMMARY STATISTICS:
        - Total Audits: {total_audits}
        - Average Score: {avg_score:.1f}%
        - Critical Failures: {critical_failures}
        - Pass Rate: {pass_rate:.1f}%
        
        AI INSIGHTS:
        {chr(10).join(insights[:3])}
        
        RECOMMENDATIONS:
        1. Focus on questions with lowest pass rates
        2. Address critical failures immediately
        3. Provide targeted coaching for underperformers
        """
        
        st.download_button(
            label="📄 Download Summary Report",
            data=summary_report,
            file_name=f"qa_summary_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with exp_col3:
        # Quick actions
        if st.button("🔄 Reset All Filters", use_container_width=True):
            for key in st.session_state.keys():
                if key.startswith('Select'):
                    del st.session_state[key]
            st.rerun()
    
except Exception as e:
    st.error(f"Error loading analytics: {e}")
    st.info("Try refreshing the page or check your database connection.")
