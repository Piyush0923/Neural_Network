import streamlit as st
import pandas as pd
import time
from utils.database import get_candidates, get_jobs, update_candidates, export_candidates_csv, add_custom_candidate
from agents.sourcing_agent import SourcingAgent
from utils.embeddings import compare_resume_with_job, find_matching_jobs_for_candidate

def show_candidates_page():
    st.title("Candidate Management")
    
    # Create tabs for different sections
    tab1, tab2, tab3 = st.tabs(["Candidate Database", "Add Candidate", "Export Data"])
    
    with tab1:
        show_candidate_database()
    
    with tab2:
        show_add_candidate_form()
    
    with tab3:
        show_export_options()

def show_candidate_database():
    # Fetch candidates
    candidates = get_candidates()
    jobs = get_jobs()
    
    # Filter options
    st.subheader("Filter Candidates")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create a multiselect for filtering by status
        status_options = ["All"] + sorted(list(set(c.get('status', '') for c in candidates)))
        selected_status = st.selectbox("Status", status_options)
    
    with col2:
        # Create a multiselect for filtering by job
        job_options = ["All"] + [f"{j['id']} - {j['title']}" for j in jobs]
        selected_job = st.selectbox("Job", job_options)
    
    with col3:
        # Create a search box
        search_query = st.text_input("Search by name, skills, or role")
    
    # Apply filters
    filtered_candidates = candidates.copy()
    
    # Filter by status
    if selected_status != "All":
        filtered_candidates = [c for c in filtered_candidates if c.get('status', '') == selected_status]
    
    # Filter by job
    if selected_job != "All":
        job_id = selected_job.split(" - ")[0]
        filtered_candidates = [c for c in filtered_candidates if 'matched_jobs' in c and c['matched_jobs'] and str(job_id) in c['matched_jobs'].split(', ')]
    
    # Filter by search query
    if search_query:
        search_query = search_query.lower()
        filtered_candidates = [
            c for c in filtered_candidates 
            if search_query in c.get('name', '').lower() 
            or search_query in c.get('skills', '').lower() 
            or search_query in c.get('current_role', '').lower()
        ]
    
    # Display candidates
    st.subheader(f"Candidates ({len(filtered_candidates)})")
    
    if not filtered_candidates:
        st.info("No candidates match the selected filters")
    else:
        # Convert to DataFrame for easier handling
        df = pd.DataFrame(filtered_candidates)
        
        # Select columns to display in the table
        display_columns = ['id', 'name', 'current_role', 'years_experience', 'skills', 'status', 'score']
        
        # Ensure all columns exist
        for col in display_columns:
            if col not in df.columns:
                df[col] = ""
        
        # Display the table
        st.dataframe(df[display_columns], use_container_width=True)
        
        # Candidate details
        st.subheader("Candidate Details")
        
        # Select a candidate to view details
        selected_candidate_id = st.selectbox(
            "Select a candidate to view details",
            options=[f"{c['id']} - {c['name']}" for c in filtered_candidates]
        )
        
        if selected_candidate_id:
            candidate_id = selected_candidate_id.split(" - ")[0]
            candidate = next((c for c in filtered_candidates if str(c['id']) == candidate_id), None)
            
            if candidate:
                show_candidate_details(candidate, jobs)

def show_candidate_details(candidate, jobs):
    # Create two columns for candidate info
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Display candidate information
        st.markdown(f"### {candidate['name']}")
        st.markdown(f"**Current Role:** {candidate['current_role']}")
        st.markdown(f"**Location:** {candidate['location']}")
        st.markdown(f"**Experience:** {candidate['years_experience']} years")
        st.markdown(f"**Status:** {candidate.get('status', 'Available')}")
        
        # Create expandable sections for more details
        with st.expander("Contact Information"):
            st.markdown(f"**Email:** {candidate['email']}")
            st.markdown(f"**Phone:** {candidate['phone']}")
        
        with st.expander("Skills"):
            skills = candidate['skills'].split(',')
            for skill in skills:
                st.markdown(f"- {skill.strip()}")
        
        with st.expander("Education & Experience"):
            st.markdown(f"**Education:** {candidate['education']}")
            st.markdown(f"**Last Company:** {candidate['last_company']}")
            st.markdown(f"**Resume Summary:**")
            st.markdown(candidate['resume_summary'])
    
    with col2:
        # Display match score
        score = float(candidate.get('score', 0))
        st.metric("Match Score", f"{int(score * 100)}%")
        
        # Calculate score color
        score_color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
        
        # Display score indicator
        st.markdown(f"<div style='background-color: {score_color}; height: 10px; width: {int(score * 100)}%; border-radius: 5px;'></div>", unsafe_allow_html=True)
        
        # Show matched jobs
        st.subheader("Matched Jobs")
        
        if 'matched_jobs' in candidate and candidate['matched_jobs']:
            matched_job_ids = candidate['matched_jobs'].split(', ')
            matched_jobs = [j for j in jobs if str(j['id']) in matched_job_ids]
            
            for job in matched_jobs:
                st.markdown(f"- **{job['title']}** ({job['department']})")
        else:
            st.info("No matched jobs yet")
    
    # Actions for this candidate
    st.subheader("Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Find Matching Jobs", key=f"find_jobs_{candidate['id']}"):
            with st.spinner("Finding matching jobs..."):
                # Create job embeddings
                job_embeddings = {j['id']: None for j in jobs}  # Simplified for demo
                
                # Find matches
                matches = find_matching_jobs_for_candidate(candidate, job_embeddings, jobs)
                
                # Update candidate's matched_jobs
                matched_job_ids = [str(match['job_id']) for match in matches]
                candidate['matched_jobs'] = ', '.join(matched_job_ids)
                
                # Get all candidates and update the specific one
                all_candidates = get_candidates()
                for i, c in enumerate(all_candidates):
                    if str(c['id']) == str(candidate['id']):
                        all_candidates[i] = candidate
                        break
                
                update_candidates(all_candidates)
                
                st.success(f"Found {len(matches)} matching jobs!")
                time.sleep(1)
                st.rerun()
    
    with col2:
        # Change status dropdown
        status_options = ["Available", "Screening", "Interview Scheduled", "Offer", "Hired", "Rejected"]
        new_status = st.selectbox("Change Status", status_options, index=status_options.index(candidate.get('status', 'Available')))
        
        if st.button("Update Status"):
            with st.spinner("Updating status..."):
                # Get all candidates and update the specific one
                all_candidates = get_candidates()
                for i, c in enumerate(all_candidates):
                    if str(c['id']) == str(candidate['id']):
                        all_candidates[i]['status'] = new_status
                        break
                
                update_candidates(all_candidates)
                st.success(f"Status updated to {new_status}")
                time.sleep(1)
                st.rerun()
    
    with col3:
        if st.button("Screen for Jobs", key=f"screen_{candidate['id']}"):
            st.session_state.current_page = "resume_screening"
            st.session_state.selected_candidate = candidate['id']
            st.rerun()

def show_add_candidate_form():
    st.subheader("Add New Candidate")
    
    # Create form for adding a new candidate
    with st.form("add_candidate_form"):
        # Basic information
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email")
            phone = st.text_input("Phone")
            location = st.text_input("Location")
        
        with col2:
            current_role = st.text_input("Current Role")
            years_experience = st.number_input("Years of Experience", min_value=0, max_value=50, value=3)
            last_company = st.text_input("Last Company")
            education = st.text_input("Education")
        
        # Skills and resume
        skills = st.text_input("Skills (comma-separated)")
        resume_summary = st.text_area("Resume Summary", height=150)
        
        # Submit button
        submitted = st.form_submit_button("Add Candidate")
        
        if submitted:
            if not name or not email or not current_role:
                st.error("Please fill in at least the name, email, and current role fields")
            else:
                # Create candidate data
                candidate_data = {
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "location": location,
                    "current_role": current_role,
                    "years_experience": years_experience,
                    "last_company": last_company,
                    "education": education,
                    "skills": skills,
                    "resume_summary": resume_summary,
                    "status": "Available",
                    "matched_jobs": "",
                    "score": 0.0
                }
                
                # Add candidate to database
                success, new_candidate = add_custom_candidate(candidate_data)
                
                if success:
                    st.success(f"Added new candidate: {name}")
                    
                    # Placeholder for using NLP to match with jobs
                    st.info("Analyzing candidate profile...")
                    
                    # In a real implementation, this would call the sourcing agent
                    # For now, we'll simulate a delay
                    time.sleep(1)
                    
                    st.success("Candidate added successfully!")
                else:
                    st.error("Failed to add candidate")

def show_export_options():
    st.subheader("Export Candidate Data")
    
    if st.button("Export to CSV"):
        # Get CSV data
        csv_data = export_candidates_csv()
        
        # Create a download button
        st.download_button(
            label="Download CSV",
            data=csv_data,
            file_name="candidates_export.csv",
            mime="text/csv"
        )
        
        st.success("Export ready for download!")

# This code runs when the module is imported, which is required for Streamlit pages
if __name__ == "__main__":
    show_candidates_page()
