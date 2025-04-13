import streamlit as st
import google.generativeai as genai
import re

from utils.database import (
    get_candidates,
    get_jobs,
    get_candidates_for_job,
    get_candidate_by_id,
    get_job_by_id,
    get_candidates_by_status,
)

def show_chat_page():
    st.title("Talent Acquisition Chat")
    
    # Initialize role and chat history
    if "user_role" not in st.session_state:
        st.session_state.user_role = "Manager"  # Default to manager
    
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Role selection in sidebar
    with st.sidebar:
        previous_role = st.session_state.user_role
        st.session_state.user_role = st.radio(
            "Select Role",
            ["Manager", "Student"],
            index=0 if st.session_state.user_role == "Manager" else 1
        )
        
        # If role was changed, clear chat history
        if previous_role != st.session_state.user_role:
            st.session_state.chat_history = []
            
        st.markdown("---")
        
        # Add example questions in sidebar based on selected role
        st.subheader("Example Questions")
        if st.session_state.user_role == "Manager":
            st.markdown("""
            Try asking:
            - Show me all candidates
            - List open jobs
            - Show candidates shortlisted for interview
            - What's the status of candidate 5?
            - Show me engineering jobs
            - Are there any active candidates?
            - Candidates for job 3
            """)
        else:  # Student role
            st.markdown("""
            Try asking:
            - What's my application status?
            - How should I prepare for the interview?
            - When will I hear back about my application?
            - What skills should I highlight?
            - How can I improve my resume?
            - What's the next step in the process?
            """)
        
        if st.button("Clear Chat History"):
            st.session_state.chat_history = []
            st.rerun()

    # Display chat messages
    for message in st.session_state.chat_history:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # User input
    prompt = st.chat_input("Type your message here...")
    
    if prompt:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        
        # Display user message
        with st.chat_message("user"):
            st.write(prompt)
            
        # Process query based on role
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = process_query(prompt, st.session_state.user_role)
                st.write(response)
        
        # Add assistant response
        st.session_state.chat_history.append({"role": "assistant", "content": response})

def process_query(prompt, role):
    """Process queries based on user role"""
    if role == "Manager":
        return process_manager_query(prompt)
    else:
        return process_student_query(prompt)

def process_manager_query(prompt):
    """Handle manager-specific queries"""
    query_lower = prompt.lower()
    candidates = get_candidates()
    jobs = get_jobs()
    
    # Job-specific candidates
    if re.search(r'candidate(?:s)? for job (\d+)', query_lower) or (('candidate' in query_lower or 'candidates' in query_lower) and 'job' in query_lower and any(str(i) in query_lower for i in range(1, 10))):
        # Extract job ID
        match = re.search(r'job (\d+)', query_lower)
        if match:
            job_id = match.group(1)
        else:
            # Try to find any number in the query
            numbers = [int(s) for s in query_lower.split() if s.isdigit()]
            job_id = str(numbers[0]) if numbers else None
            
        if job_id:
            job_candidates = get_candidates_for_job(job_id)
            job = get_job_by_id(job_id)
            if job:
                return format_job_candidates(job_candidates, job)
        return "Please provide a valid job ID"
    
    # Candidate status query
    if re.search(r'status of candidate (\d+)', query_lower):
        match = re.search(r'candidate (\d+)', query_lower)
        if match:
            return get_candidate_details(match.group(1))
        return "Please provide a valid candidate ID"

    # Shortlisted candidates query
    if any(term in query_lower for term in ['shortlist', 'interview', 'shortlisted']):
        # Assuming 'Shortlisted' is the status for interview candidates
        shortlisted_candidates = get_candidates_by_status("Shortlisted")
        return format_shortlisted_candidates(shortlisted_candidates)

    # List engineering jobs
    if 'engineering' in query_lower and ('job' in query_lower or 'role' in query_lower):
        return get_engineering_jobs(jobs)

    # Active candidates
    if 'active candidate' in query_lower:
        return get_active_candidates(candidates)

    # General candidate list
    if 'candidate' in query_lower and ('list' in query_lower or 'show' in query_lower):
        return format_candidates_list(candidates)

    # General job list
    if 'job' in query_lower and ('list' in query_lower or 'show' in query_lower):
        return format_jobs_list(jobs)

    # Default response
    return get_default_manager_response(candidates, jobs)

def process_student_query(prompt):
    """Handle student-specific queries"""
    query_lower = prompt.lower()
    
    # Student application status
    if re.search(r'(status|update).*(application|my application)', query_lower) or 'status' in query_lower:
        return get_application_status()
    
    # Interview preparation
    if any(term in query_lower for term in ['interview preparation', 'prepare for interview', 'interview tips']):
        return get_interview_tips()
    
    # Resume improvement
    if any(term in query_lower for term in ['resume', 'cv', 'improve']):
        return get_resume_tips()
    
    # Skills to highlight
    if any(term in query_lower for term in ['skill', 'highlight', 'showcase']):
        return get_skills_advice()
    
    # Next steps
    if any(term in query_lower for term in ['next step', 'process', 'what happen', 'happen next']):
        return get_next_steps()
    
    # When to hear back
    if any(term in query_lower for term in ['hear back', 'response', 'when will', 'timeline']):
        return get_timeline_info()
    
    # Default student response
    return get_default_student_response()

def get_candidate_details(candidate_id):
    """Get detailed candidate information"""
    candidate = get_candidate_by_id(candidate_id)
    if not candidate:
        return "Candidate not found"
    
    return (
        f"**Candidate Details**\n\n"
        f"Name: {candidate.get('name', 'N/A')}\n"
        f"Current Role: {candidate.get('current_role', 'N/A')}\n"
        f"Status: {candidate.get('status', 'N/A')}\n"
        f"Match Score: {candidate.get('screening_result', {}).get('match_score', 'N/A')}/100\n"
        f"Last Updated: {candidate.get('last_updated', 'N/A')}"
    )

def format_shortlisted_candidates(candidates):
    """Format shortlisted candidates for interview response"""
    if not candidates:
        return "No candidates are currently shortlisted for interviews."
    
    response = f"**{len(candidates)} Candidates Shortlisted for Interview:**\n\n"
    for i, candidate in enumerate(candidates):
        response += (
            f"{i+1}. **{candidate.get('name', 'N/A')}**\n"
            f"   - Current Role: {candidate.get('current_role', 'N/A')}\n"
        )
        if 'screening_result' in candidate and isinstance(candidate.get('screening_result'), dict):
            response += f"   - Match Score: {candidate.get('screening_result', {}).get('match_score', 'N/A')}/100\n"
        else:
            response += f"   - Match Score: {candidate.get('score', 'N/A')}\n"
        response += "\n"
    return response

def format_job_candidates(candidates, job):
    """Format candidates for a specific job"""
    if not candidates:
        return f"No candidates found for the job: {job.get('title', 'Unknown Job')}"
    
    response = f"**{len(candidates)} Candidates for {job.get('title', 'Job')}:**\n\n"
    for i, candidate in enumerate(candidates):
        response += (
            f"{i+1}. **{candidate.get('name', 'N/A')}**\n"
            f"   - Current Role: {candidate.get('current_role', 'N/A')}\n"
            f"   - Status: {candidate.get('status', 'N/A')}\n\n"
        )
    return response

def get_engineering_jobs(jobs):
    """Filter and format engineering jobs"""
    engineering_jobs = [j for j in jobs if 'engineer' in j.get('title', '').lower()]
    if not engineering_jobs:
        return "No engineering positions currently open"
    
    response = "**Open Engineering Positions:**\n\n"
    for job in engineering_jobs:
        response += (
            f"- {job.get('title', 'N/A')} at {job.get('company', 'N/A')}\n"
            f"  Location: {job.get('location', 'N/A')}\n"
            f"  Experience: {job.get('experience', 'N/A')}\n\n"
        )
    return response

def get_active_candidates(candidates):
    """Get list of active candidates"""
    active_candidates = [c for c in candidates if c.get('status') == 'Available']
    return format_candidates_list(active_candidates, "active")

def format_candidates_list(candidates, status_type="all"):
    """Format candidate list response"""
    if not candidates:
        return "No candidates found"
    
    response = f"**{len(candidates)} Candidates:**\n\n"
    for i, candidate in enumerate(candidates[:5]):
        response += (
            f"{i+1}. **{candidate.get('name', 'N/A')}**\n"
            f"   - Role: {candidate.get('current_role', 'N/A')}\n"
            f"   - Status: {candidate.get('status', 'N/A')}\n\n"
        )
    if len(candidates) > 5:
        response += f"...and {len(candidates)-5} more candidates"
    return response

def format_jobs_list(jobs):
    """Format job list response"""
    open_jobs = [j for j in jobs if j.get('status') == 'open']
    if not open_jobs:
        return "No open positions currently"
    
    response = "**Open Positions:**\n\n"
    for job in open_jobs:
        response += (
            f"- {job.get('title', 'N/A')}\n"
            f"  Company: {job.get('company', 'N/A')}\n"
            f"  Location: {job.get('location', 'N/A')}\n\n"
        )
    return response

def get_default_manager_response(candidates, jobs):
    """Default manager response with statistics"""
    open_jobs = len([j for j in jobs if j.get('status') == 'open'])
    return (
        f"**Current Recruitment Status**\n\n"
        f"- 📄 Total Positions: {len(jobs)}\n"
        f"- 🔍 Open Roles: {open_jobs}\n"
        f"- 👥 Candidates in Pipeline: {len(candidates)}\n\n"
        "Ask about specific candidates or jobs for detailed information."
    )

def get_default_student_response():
    """Default student response"""
    return (
        "**How can I help with your application?**\n\n"
        "I can assist with:\n"
        "- Checking your application status\n"
        "- Providing interview preparation tips\n"
        "- Offering resume improvement advice\n"
        "- Explaining the recruitment process\n"
        "- Suggesting skills to highlight\n\n"
        "Try asking me specific questions about your application journey!"
    )

def get_application_status():
    """Provide application status information"""
    return (
        "**Your Application Status**\n\n"
        "Your application is currently under review. Our recruitment team is assessing your qualifications against the job requirements.\n\n"
        "The typical review process takes 1-2 weeks. If your profile matches our requirements, you'll be contacted for an initial screening call.\n\n"
        "You can check back here anytime for updates on your application status."
    )

def get_interview_tips():
    """Provide interview preparation tips"""
    return (
        "**Interview Preparation Tips:**\n\n"
        "1. **Research the Company**: Understand our mission, values, and recent projects\n"
        "2. **Review the Job Description**: Note the key skills and prepare examples\n"
        "3. **Practice Common Questions**: Especially behavior and technical questions\n"
        "4. **Prepare Your Own Questions**: Show your interest in the role and company\n"
        "5. **Technical Preparation**: Review relevant concepts and practice problems\n"
        "6. **Set Up Your Space**: For virtual interviews, ensure proper lighting and audio\n"
        "7. **Follow-Up**: Prepare a thank-you note after the interview\n\n"
        "Is there a specific part of the interview you'd like more advice on?"
    )

def get_resume_tips():
    """Provide resume improvement advice"""
    return (
        "**Resume Improvement Tips:**\n\n"
        "1. **Tailor to the Job**: Customize your resume for each position\n"
        "2. **Highlight Achievements**: Use quantifiable results when possible\n"
        "3. **Use Keywords**: Include industry and job-specific keywords\n"
        "4. **Keep it Concise**: Limit to 1-2 pages with relevant information\n"
        "5. **Professional Formatting**: Use clean, consistent styling\n"
        "6. **Include Skills Section**: List technical and soft skills\n"
        "7. **Proofread**: Eliminate spelling and grammar errors\n\n"
        "Would you like specific feedback on your resume? You can submit it through our portal."
    )

def get_skills_advice():
    """Provide advice on skills to highlight"""
    return (
        "**Skills to Highlight:**\n\n"
        "For technical roles, emphasize:\n"
        "- Relevant programming languages and technologies\n"
        "- Project experience (especially team projects)\n"
        "- Problem-solving approaches\n"
        "- System design understanding\n\n"
        "Don't forget soft skills:\n"
        "- Communication abilities\n"
        "- Teamwork examples\n"
        "- Time management\n"
        "- Adaptability to new challenges\n\n"
        "Pro tip: Provide specific examples of how you've applied these skills in real situations."
    )

def get_next_steps():
    """Explain next steps in the process"""
    return (
        "**Next Steps in the Recruitment Process:**\n\n"
        "1. **Application Review**: We review your resume and application (1-2 weeks)\n"
        "2. **Initial Screening**: Brief phone/video call with recruiter (30 minutes)\n"
        "3. **Technical Assessment**: Skills-based assessment or coding challenge\n"
        "4. **Technical Interview**: In-depth discussion with the technical team\n"
        "5. **Final Interview**: Meeting with hiring manager and team members\n"
        "6. **Offer Stage**: If successful, you'll receive an offer\n\n"
        "Each stage is an opportunity to learn more about us, as we learn more about you!"
    )

def get_timeline_info():
    """Provide information about application timeline"""
    return (
        "**Application Timeline:**\n\n"
        "You can expect to hear back about your application within **1-2 weeks** after submission.\n\n"
        "If selected for an interview, the process typically takes:\n"
        "- Initial screening: 1 week after application review\n"
        "- Technical assessment: 1 week after screening\n"
        "- Final interviews: 1-2 weeks after assessment\n"
        "- Decision/offer: 1 week after final interview\n\n"
        "The entire process usually takes 4-6 weeks from application to offer, though timing may vary depending on the position and number of applicants."
    )

if __name__ == "__main__":
    show_chat_page()