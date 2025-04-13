import streamlit as st
import pandas as pd
from utils.database import setup_database, get_candidates, get_jobs
from agents.sourcing_agent import SourcingAgent
from agents.screening_agent import ScreeningAgent
from agents.engagement_agent import EngagementAgent
from agents.scheduling_agent import SchedulingAgent

# Set page configuration
st.set_page_config(
    page_title="Talent Acquisition System",
    page_icon="👥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'initialized' not in st.session_state:
    # Setup database and load initial data
    setup_database()
    st.session_state.candidates = get_candidates()
    st.session_state.jobs = get_jobs()
    
    # Initialize agents
    st.session_state.sourcing_agent = SourcingAgent()
    st.session_state.screening_agent = ScreeningAgent()
    st.session_state.engagement_agent = EngagementAgent()
    st.session_state.scheduling_agent = SchedulingAgent()
    
    st.session_state.initialized = True

# Main page
st.title("🤖 Intelligent Talent Acquisition System")

st.markdown("""
### Welcome to the AI-powered Talent Acquisition Platform
This system uses multiple AI agents to automate and enhance your recruitment process:

- **👨‍💼 Sourcing Agent**: Discovers candidates from various platforms
- **📝 Screening Agent**: Evaluates resumes against job requirements 
- **💬 Engagement Agent**: Communicates with candidates via intelligent chat
- **📅 Scheduling Agent**: Automates interview scheduling

Use the sidebar to navigate through different features of the application.
""")

# Display key metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Candidates", len(st.session_state.candidates))
    
with col2:
    st.metric("Open Positions", len(st.session_state.jobs))
    
with col3:
    # Calculate candidates in screening stage
    screening_count = sum(1 for candidate in st.session_state.candidates 
                         if candidate.get('status') == 'Screening')
    st.metric("In Screening", screening_count)
    
with col4:
    # Calculate scheduled interviews
    scheduled_count = sum(1 for candidate in st.session_state.candidates 
                         if candidate.get('status') == 'Interview Scheduled')
    st.metric("Scheduled Interviews", scheduled_count)

# Recent Activities (placeholder for a real activity log)
st.subheader("Recent Activities")
activities = [
    {"time": "Today, 10:30 AM", "description": "New candidate matched for Software Engineer position"},
    {"time": "Today, 9:15 AM", "description": "Interview scheduled with John Doe for Data Scientist role"},
    {"time": "Yesterday", "description": "Resume screening completed for 5 Marketing Specialist candidates"},
    {"time": "2 days ago", "description": "Sourcing agent found 12 new potential candidates"}
]

for activity in activities:
    st.markdown(f"**{activity['time']}**: {activity['description']}")

# Footer
st.markdown("---")
st.markdown("© 2023 Intelligent Talent Acquisition System | Powered by CrewAI and Hugging Face")
