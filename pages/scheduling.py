import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from utils.database import get_candidates, get_jobs, get_candidate_by_id, get_job_by_id, get_candidates_for_job
from agents.scheduling_agent import SchedulingAgent

def show_scheduling_page():
    st.title("Interview Scheduling")
    
    # Create tabs for different scheduling features
    tab1, tab2, tab3 = st.tabs(["Schedule Interview", "Calendar View", "Batch Scheduling"])
    
    with tab1:
        show_individual_scheduling()
    
    with tab2:
        show_calendar_view()
    
    with tab3:
        show_batch_scheduling()

def show_individual_scheduling():
    st.subheader("Schedule Individual Interview")
    
    # Load candidates and jobs
    candidates = get_candidates()
    jobs = get_jobs()
    
    # Check if we have a pre-selected candidate or job from another page
    preselected_candidate = st.session_state.get('selected_candidate', None)
    preselected_job = st.session_state.get('selected_job', None)
    
    # Create two columns for selection
    col1, col2 = st.columns(2)
    
    with col1:
        # Candidate selection
        candidate_options = [f"{c['id']} - {c['name']}" for c in candidates]
        
        # Set the default index if we have a preselected candidate
        default_candidate_index = 0
        if preselected_candidate:
            for i, option in enumerate(candidate_options):
                if option.startswith(f"{preselected_candidate} -"):
                    default_candidate_index = i
                    break
        
        selected_candidate = st.selectbox(
            "Select Candidate",
            options=candidate_options,
            index=default_candidate_index
        )
        candidate_id = selected_candidate.split(" - ")[0]
    
    with col2:
        # Job selection
        job_options = [f"{j['id']} - {j['title']}" for j in jobs]
        
        # Set the default index if we have a preselected job
        default_job_index = 0
        if preselected_job:
            for i, option in enumerate(job_options):
                if option.startswith(f"{preselected_job} -"):
                    default_job_index = i
                    break
        
        selected_job = st.selectbox(
            "Select Job",
            options=job_options,
            index=default_job_index
        )
        job_id = selected_job.split(" - ")[0]
    
    # Clear preselected values after using them
    if 'selected_candidate' in st.session_state:
        del st.session_state.selected_candidate
    if 'selected_job' in st.session_state:
        del st.session_state.selected_job
    
    # Fetch the candidate and job details
    candidate = get_candidate_by_id(candidate_id)
    job = get_job_by_id(job_id)
    
    if candidate and job:
        # Display candidate and job summaries
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {candidate['name']}")
            st.markdown(f"**Current Role:** {candidate['current_role']}")
            st.markdown(f"**Email:** {candidate['email']}")
            st.markdown(f"**Status:** {candidate.get('status', 'Available')}")
        
        with col2:
            st.markdown(f"### {job['title']}")
            st.markdown(f"**Department:** {job['department']}")
            st.markdown(f"**Location:** {job['location']}")
        
        # Get available time slots
        st.subheader("Available Interview Slots")
        
        # Create the scheduling agent
        scheduling_agent = SchedulingAgent()
        
        # Date selection for slots
        today = datetime.now()
        date_options = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 15)]
        selected_date = st.selectbox("Select Date", date_options)
        
        # Get available slots for the selected date
        with st.spinner("Loading available slots..."):
            available_slots = scheduling_agent.get_available_slots(selected_date, selected_date)
        
        if available_slots["available_slots"]:
            # Format the slots for display
            slot_options = [f"{slot['start_time']} - {slot['interviewer']}" for slot in available_slots["available_slots"]]
            selected_slot = st.selectbox("Select Time Slot", slot_options)
            
            # Extract the time from the selected slot
            slot_time = selected_slot.split(" - ")[0]
            
            # Schedule button
            if st.button("Schedule Interview"):
                with st.spinner("Scheduling interview..."):
                    # Use the scheduling agent to schedule the interview
                    result = scheduling_agent.schedule_interview(candidate_id, job_id, selected_date, slot_time)
                    
                    if "error" in result:
                        st.error(result["error"])
                    else:
                        st.success("Interview scheduled successfully!")
                        
                        # Show the interview details
                        show_interview_details(result)
        else:
            st.warning(f"No available slots on {selected_date}. Please select a different date.")

def show_interview_details(result):
    st.subheader("Interview Details")
    
    st.markdown(f"**Candidate:** {result['candidate']['name']}")
    st.markdown(f"**Job:** {result['job']['title']}")
    st.markdown(f"**Date:** {result['interview']['date']}")
    st.markdown(f"**Time:** {result['interview']['time']}")
    st.markdown(f"**Duration:** {result['interview']['duration']}")
    st.markdown(f"**Interviewer:** {result['interview']['interviewer']}")
    
    st.subheader("Interview Information")
    st.markdown(result['details'])
    
    # Option to send confirmation
    if st.button("Send Confirmation Email"):
        with st.spinner("Sending confirmation..."):
            # In a real implementation, this would connect to an email service
            # For now, we'll just simulate a delay
            time.sleep(1)
            st.success(f"Confirmation email sent to {result['candidate']['email']}")

def show_calendar_view():
    st.subheader("Interview Calendar")
    
    # Create a scheduling agent to get scheduled interviews
    scheduling_agent = SchedulingAgent()
    
    # Date range selection for calendar view
    col1, col2 = st.columns(2)
    
    with col1:
        today = datetime.now()
        start_date = st.date_input("Start Date", today)
    
    with col2:
        end_date = st.date_input("End Date", today + timedelta(days=14))
    
    # Format dates for the API
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    
    # Get all slots (both available and booked)
    with st.spinner("Loading calendar..."):
        # Get available slots
        available_slots = scheduling_agent.get_available_slots(start_date_str, end_date_str)
        
        # In a real implementation, we would also get booked slots
        # For this demo, we'll just use the available slots
        
        # Create a dictionary to organize slots by date
        calendar_data = {}
        
        for slot in available_slots["available_slots"]:
            date = slot["date"]
            if date not in calendar_data:
                calendar_data[date] = []
            
            calendar_data[date].append({
                "time": f"{slot['start_time']} - {slot['end_time']}",
                "duration": slot["duration"],
                "interviewer": slot["interviewer"],
                "status": "Available",
                "candidate": None,
                "job": None
            })
        
        # Add some example booked interviews for demonstration
        # In a real implementation, these would come from the database
        example_dates = list(calendar_data.keys())[:3]  # Use the first 3 dates
        
        if example_dates:
            for i, date in enumerate(example_dates):
                # Make the first slot of each date booked
                if calendar_data[date]:
                    calendar_data[date][0]["status"] = "Booked"
                    calendar_data[date][0]["candidate"] = f"Candidate {i+1}"
                    calendar_data[date][0]["job"] = "Software Engineer"
    
    # Display the calendar
    if not calendar_data:
        st.info("No interview slots available in the selected date range.")
    else:
        # Sort the dates
        sorted_dates = sorted(calendar_data.keys())
        
        # Display each date
        for date in sorted_dates:
            with st.expander(f"**{date}** ({len(calendar_data[date])} slots)"):
                # Create a table for this date's slots
                slots_df = pd.DataFrame(calendar_data[date])
                
                # Apply color coding based on status
                def highlight_status(val):
                    if val == "Booked":
                        return "background-color: #ffcccc"  # Light red
                    return ""
                
                # Display the table with highlighting
                st.dataframe(slots_df.style.applymap(highlight_status, subset=["status"]), use_container_width=True)
    
    # Calendar export option
    if st.button("Export Calendar (iCal)"):
        st.info("Calendar export functionality would be implemented here in a real application.")
        # In a real implementation, this would generate an iCal file
        # For now, we'll just display a message
        st.download_button(
            label="Download iCal File",
            data="Sample iCal data",
            file_name="interview_calendar.ics",
            mime="text/calendar"
        )

def show_batch_scheduling():
    st.subheader("Batch Schedule Interviews")
    
    # Load jobs
    jobs = get_jobs()
    
    # Check if we have a pre-selected job from another page
    preselected_job = st.session_state.get('selected_job', None)
    
    # Job selection
    job_options = [f"{j['id']} - {j['title']}" for j in jobs]
    
    # Set the default index if we have a preselected job
    default_job_index = 0
    if preselected_job:
        for i, option in enumerate(job_options):
            if option.startswith(f"{preselected_job} -"):
                default_job_index = i
                break
    
    selected_job = st.selectbox(
        "Select Job for Batch Scheduling",
        options=job_options,
        index=default_job_index,
        key="batch_job_scheduling"
    )
    job_id = selected_job.split(" - ")[0]
    
    # Clear preselected value after using it
    if 'selected_job' in st.session_state:
        del st.session_state.selected_job
    
    # Date selection for batch scheduling
    today = datetime.now()
    date_options = [(today + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 15)]
    selected_date = st.selectbox("Select Date for Batch Interviews", date_options)
    
    # Get candidates in screening stage for this job
    candidates = get_candidates_for_job(job_id)
    screening_candidates = [c for c in candidates if c.get('status') == 'Screening']
    
    if not screening_candidates:
        st.info("No candidates in the screening stage for this job. Please screen candidates first.")
    else:
        st.info(f"Found {len(screening_candidates)} candidates in the screening stage for this job.")
        
        # Sort by score
        screening_candidates.sort(key=lambda x: float(x.get('score', 0)), reverse=True)
        
        # Display the candidates
        st.dataframe(pd.DataFrame([
            {
                'id': c['id'],
                'name': c['name'],
                'current_role': c['current_role'],
                'score': float(c.get('score', 0))
            }
            for c in screening_candidates
        ]), use_container_width=True)
        
        # Batch schedule button
        if st.button("Schedule Interviews for Top Candidates"):
            with st.spinner("Scheduling batch interviews..."):
                # Create a scheduling agent
                scheduling_agent = SchedulingAgent()
                
                # Schedule batch interviews
                result = scheduling_agent.schedule_batch_interviews(job_id, selected_date)
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success(f"Successfully scheduled {len(result['scheduled_interviews'])} interviews!")
                    
                    # Show the batch scheduling results
                    show_batch_scheduling_results(result)

def show_batch_scheduling_results(result):
    st.subheader("Batch Scheduling Results")
    
    st.markdown(f"**Job:** {result['job']['title']}")
    st.markdown(f"**Date:** {result['date']}")
    
    # Display the scheduled interviews
    st.dataframe(pd.DataFrame(result['scheduled_interviews']), use_container_width=True)
    
    # Option to send notifications
    if st.button("Send Notifications to All"):
        with st.spinner("Sending notifications..."):
            # In a real implementation, this would connect to an email service
            # For now, we'll just simulate a delay
            time.sleep(2)
            st.success(f"Notifications sent to all {len(result['scheduled_interviews'])} candidates")
    
    # Option to export schedule
    if st.button("Export Schedule"):
        # Convert to CSV
        df = pd.DataFrame(result['scheduled_interviews'])
        csv = df.to_csv(index=False)
        
        # Download button
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"interview_schedule_{result['date']}.csv",
            mime="text/csv"
        )

# This code runs when the module is imported, which is required for Streamlit pages
if __name__ == "__main__":
    show_scheduling_page()
