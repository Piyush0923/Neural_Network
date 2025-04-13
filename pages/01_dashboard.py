import streamlit as st
import pandas as pd
import time
from utils.database import get_candidates, get_jobs, get_candidates_by_status

def show_dashboard():
    st.title("Talent Acquisition Dashboard")
    
    # Fetch latest data
    candidates = get_candidates()
    jobs = get_jobs()
    
    # Calculate metrics
    total_candidates = len(candidates)
    open_positions = len(jobs)
    screening_candidates = len(get_candidates_by_status("Screening"))
    scheduled_interviews = len(get_candidates_by_status("Interview Scheduled"))
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Candidates", total_candidates)
    
    with col2:
        st.metric("Open Positions", open_positions)
    
    with col3:
        st.metric("In Screening", screening_candidates)
    
    with col4:
        st.metric("Scheduled Interviews", scheduled_interviews)
    
    st.markdown("---")
    
    # Display two charts side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Candidates by Status")
        # Calculate the count of candidates by status
        status_counts = pd.DataFrame(candidates).groupby('status').size().reset_index(name='count')
        
        # Check if the dataframe is empty
        if not status_counts.empty:
            # Create a bar chart
            st.bar_chart(status_counts.set_index('status'))
        else:
            st.write("No status data available")
    
    with col2:
        st.subheader("Top Skills in Candidate Pool")
        # Extract and count skills
        all_skills = []
        for candidate in candidates:
            if 'skills' in candidate and candidate['skills']:
                skills = [skill.strip() for skill in candidate['skills'].split(',')]
                all_skills.extend(skills)
        
        # Count occurrence of each skill
        skill_counts = pd.Series(all_skills).value_counts().reset_index()
        skill_counts.columns = ['skill', 'count']
        
        # Display top 10 skills
        if not skill_counts.empty:
            top_skills = skill_counts.head(10)
            st.bar_chart(top_skills.set_index('skill'))
        else:
            st.write("No skills data available")
    
    st.markdown("---")
    
    # Recent activities (simulated)
    st.subheader("Recent Activities")
    
    activities = [
        {"time": "Today, 10:30 AM", "description": "New candidate matched for Software Engineer position"},
        {"time": "Today, 9:15 AM", "description": "Interview scheduled with John Doe for Data Scientist role"},
        {"time": "Yesterday", "description": "Resume screening completed for 5 Marketing Specialist candidates"},
        {"time": "2 days ago", "description": "Sourcing agent found 12 new potential candidates"}
    ]
    
    for activity in activities:
        st.markdown(f"**{activity['time']}**: {activity['description']}")
    
    st.markdown("---")
    
    # Job fill progress
    st.subheader("Job Fill Progress")
    
    # Calculate the progress for each job
    for job in jobs:
        job_id = job['id']
        matched_candidates = [c for c in candidates if 'matched_jobs' in c and c['matched_jobs'] and str(job_id) in c['matched_jobs'].split(', ')]
        interviewed_candidates = [c for c in matched_candidates if c['status'] == 'Interview Scheduled']
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{job['title']}** ({job['department']})")
            
            # Calculate percentages (capped at 100%)
            sourcing_pct = min(100, len(matched_candidates) * 20)  # Assume 5 candidates = 100%
            screening_pct = min(100, len(matched_candidates) / 5 * 100) if matched_candidates else 0
            interview_pct = min(100, len(interviewed_candidates) / 3 * 100) if interviewed_candidates else 0  # Assume 3 interviews = 100%
            
            # Create a progress bar for each stage, ensure values are between 0 and 1
            st.write("Sourcing:")
            st.progress(min(1.0, max(0.0, sourcing_pct / 100)))
            
            st.write("Screening:")
            st.progress(min(1.0, max(0.0, screening_pct / 100)))
            
            st.write("Interviewing:")
            st.progress(min(1.0, max(0.0, interview_pct / 100)))
        
        with col2:
            st.write(f"Matched: {len(matched_candidates)}")
            st.write(f"Screened: {len([c for c in matched_candidates if c['status'] == 'Screening'])}")
            st.write(f"Interviews: {len(interviewed_candidates)}")
    
    # Refresh button for the dashboard
    if st.button("Refresh Dashboard"):
        with st.spinner("Refreshing data..."):
            time.sleep(1)  # Simulate a refresh
            st.rerun()

# This code runs when the module is imported, which is required for Streamlit pages
if __name__ == "__main__":
    show_dashboard()
