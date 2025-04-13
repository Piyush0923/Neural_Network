import streamlit as st
import pandas as pd
import time
from utils.database import get_candidates, get_jobs, get_candidates_for_job, export_jobs_csv
from agents.sourcing_agent import SourcingAgent

def show_jobs_page():
    st.title("Job Positions")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Open Positions", "Match Candidates", "Export Data"])
    
    with tab1:
        show_job_listings()
    
    with tab2:
        show_candidate_matching()
    
    with tab3:
        show_export_options()

def show_job_listings():
    # Fetch jobs
    jobs = get_jobs()
    
    # Filter options
    st.subheader("Filter Jobs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Create a dropdown for filtering by department
        dept_options = ["All"] + sorted(list(set(j['department'] for j in jobs)))
        selected_dept = st.selectbox("Department", dept_options)
    
    with col2:
        # Create a search box
        search_query = st.text_input("Search by title or skills")
    
    # Apply filters
    filtered_jobs = jobs.copy()
    
    # Filter by department
    if selected_dept != "All":
        filtered_jobs = [j for j in filtered_jobs if j['department'] == selected_dept]
    
    # Filter by search query
    if search_query:
        search_query = search_query.lower()
        filtered_jobs = [
            j for j in filtered_jobs 
            if search_query in j['title'].lower() 
            or search_query in j.get('skills_required', '').lower()
        ]
    
    # Display jobs
    st.subheader(f"Job Positions ({len(filtered_jobs)})")
    
    if not filtered_jobs:
        st.info("No jobs match the selected filters")
    else:
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(filtered_jobs)
        
        # Select columns to display in the table
        display_columns = ['id', 'title', 'department', 'location', 'type', 'status']
        
        # Display the table
        st.dataframe(df[display_columns], use_container_width=True)
        
        # Job details
        st.subheader("Job Details")
        
        # Select a job to view details
        selected_job_id = st.selectbox(
            "Select a job to view details",
            options=[f"{j['id']} - {j['title']}" for j in filtered_jobs]
        )
        
        if selected_job_id:
            job_id = selected_job_id.split(" - ")[0]
            job = next((j for j in filtered_jobs if str(j['id']) == job_id), None)
            
            if job:
                show_job_details(job)

def show_job_details(job):
    # Create two columns for job info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display job information
        st.markdown(f"### {job['title']}")
        st.markdown(f"**Department:** {job['department']}")
        st.markdown(f"**Location:** {job['location']}")
        st.markdown(f"**Type:** {job['type']}")
        st.markdown(f"**Status:** {job['status']}")
        
        # Create expandable sections for more details
        with st.expander("Job Description"):
            st.markdown(job['description'])
        
        with st.expander("Requirements"):
            st.markdown(job['requirements'])
        
        with st.expander("Responsibilities"):
            st.markdown(job['responsibilities'])
    
    with col2:
        # Display requirements summary
        st.subheader("Required Skills")
        skills = job['skills_required'].split(',')
        for skill in skills:
            st.markdown(f"- {skill.strip()}")
        
        st.subheader("Experience")
        st.markdown(job['experience_required'])
        
        st.subheader("Education")
        st.markdown(job['education_required'])
        
        st.subheader("Salary Range")
        st.markdown(job['salary_range'])
    
    # Matched candidates section
    st.subheader("Matched Candidates")
    
    # Get candidates matched to this job
    candidates = get_candidates_for_job(job['id'])
    
    if not candidates:
        st.info("No candidates matched to this job yet")
        
        if st.button("Find Matching Candidates", key=f"find_candidates_{job['id']}"):
            with st.spinner("Finding matching candidates..."):
                # Create a sourcing agent instance
                sourcing_agent = SourcingAgent()
                
                # Find matching candidates
                result = sourcing_agent.search_candidates(job['id'])
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"Found {len(result['matched_candidates'])} matching candidates!")
                    time.sleep(1)
                    st.rerun()
    else:
        # Sort candidates by score
        candidates.sort(key=lambda x: float(x.get('score', 0)), reverse=True)
        
        # Create a dataframe for display
        df = pd.DataFrame([
            {
                'id': c['id'],
                'name': c['name'],
                'current_role': c['current_role'],
                'years_experience': c['years_experience'],
                'status': c.get('status', 'Available'),
                'score': float(c.get('score', 0))
            }
            for c in candidates
        ])
        
        # Display the candidate table
        st.dataframe(df, use_container_width=True)
        
        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Screen Candidates", key=f"screen_{job['id']}"):
                st.session_state.current_page = "resume_screening"
                st.session_state.selected_job = job['id']
                st.rerun()
        
        with col2:
            if st.button("Find More Candidates", key=f"find_more_{job['id']}"):
                with st.spinner("Finding more candidates..."):
                    # Create a sourcing agent instance
                    sourcing_agent = SourcingAgent()
                    
                    # Find matching candidates
                    result = sourcing_agent.search_candidates(job['id'])
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success(f"Found {len(result['matched_candidates'])} matching candidates!")
                        time.sleep(1)
                        st.rerun()

def show_candidate_matching():
    st.subheader("Match Candidates to Jobs")
    
    # Fetch jobs
    jobs = get_jobs()
    
    # Select a job for matching
    selected_job_id = st.selectbox(
        "Select a job to find matching candidates",
        options=[""] + [f"{j['id']} - {j['title']}" for j in jobs]
    )
    
    if selected_job_id:
        job_id = selected_job_id.split(" - ")[0]
        job = next((j for j in jobs if str(j['id']) == job_id), None)
        
        if job:
            st.markdown(f"### Finding matches for: {job['title']}")
            
            # Get candidates matched to this job
            already_matched = get_candidates_for_job(job['id'])
            
            if already_matched:
                st.info(f"This job already has {len(already_matched)} matched candidates. You can find more candidates.")
            
            # Use the sourcing agent for matching
            if st.button("Find Matching Candidates"):
                with st.spinner("The sourcing agent is analyzing candidate profiles..."):
                    # Create a sourcing agent instance
                    sourcing_agent = SourcingAgent()
                    
                    # Find matching candidates
                    result = sourcing_agent.search_candidates(job['id'])
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        # Display results
                        st.success(f"Found {len(result['matched_candidates'])} matching candidates!")
                        
                        # Create a dataframe for display
                        df = pd.DataFrame(result['matched_candidates'])
                        
                        # Display the matched candidates
                        st.dataframe(df, use_container_width=True)
                        
                        # Option to screen these candidates
                        if st.button("Screen These Candidates"):
                            st.session_state.current_page = "resume_screening"
                            st.session_state.selected_job = job['id']
                            st.rerun()

def show_export_options():
    st.subheader("Export Job Data")
    
    if st.button("Export to CSV"):
        # Get CSV data
        csv_data = export_jobs_csv()
        
        # Create a download button
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="jobs_export.csv",
            mime="text/csv"
        )
        
        st.success("Export ready for download!")

# This code runs when the module is imported, which is required for Streamlit pages
if __name__ == "__main__":
    show_jobs_page()
