import streamlit as st
import pandas as pd
import PyPDF2
import io
import google.generativeai as genai

from utils.database import get_candidates, get_jobs, get_candidate_by_id, get_job_by_id
from agents.screening_agent import ScreeningAgent
from typing import Tuple

# Set page configuration
st.set_page_config(
    page_title="Resume ATS Calculator",
    page_icon="📄",
    layout="centered"
)

# Configure the Gemini API key
GOOGLE_API_KEY = "AIzaSyAZm-jH4ZqxXH-onmiguW9XS4npWd5tbeo"
if not GOOGLE_API_KEY:
    st.error("Google API Key not found. Please set the GOOGLE_API_KEY environment variable.")
    st.stop()

# Configure the Gemini API
genai.configure(api_key=GOOGLE_API_KEY)

# ---------------------------
# PAGE STRUCTURE
# ---------------------------

def show_resume_screening():
    st.title("Resume Screening")
    
    tab1, tab2 = st.tabs(["Individual Screening", "Resume Analysis"])
    
    with tab1:
        show_individual_screening()
    
    with tab2:
        show_resume_analysis()

# ---------------------------
# INDIVIDUAL SCREENING
# ---------------------------

def show_individual_screening():
    st.subheader("Screen Individual Candidate")
    
    candidates = get_candidates()
    jobs = get_jobs()
    
    preselected_candidate = st.session_state.get('selected_candidate', None)
    preselected_job = st.session_state.get('selected_job', None)
    
    col1, col2 = st.columns(2)
    
    with col1:
        candidate_options = [f"{c['id']} - {c['name']}" for c in candidates]
        default_candidate_index = 0
        if preselected_candidate:
            for i, option in enumerate(candidate_options):
                if option.startswith(f"{preselected_candidate} -"):
                    default_candidate_index = i
                    break
        selected_candidate = st.selectbox("Select Candidate", options=candidate_options, index=default_candidate_index)
        candidate_id = selected_candidate.split(" - ")[0]
    
    with col2:
        job_options = [f"{j['id']} - {j['title']}" for j in jobs]
        default_job_index = 0
        if preselected_job:
            for i, option in enumerate(job_options):
                if option.startswith(f"{preselected_job} -"):
                    default_job_index = i
                    break
        selected_job = st.selectbox("Select Job", options=job_options, index=default_job_index)
        job_id = selected_job.split(" - ")[0]
    
    if preselected_candidate:
        del st.session_state.selected_candidate
    if preselected_job:
        del st.session_state.selected_job
    
    candidate = get_candidate_by_id(candidate_id)
    job = get_job_by_id(job_id)
    
    if candidate and job:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"### {candidate['name']}")
            st.markdown(f"**Current Role:** {candidate['current_role']}")
            st.markdown(f"**Experience:** {candidate['years_experience']} years")
            with st.expander("Candidate Details"):
                st.markdown(f"**Skills:** {candidate['skills']}")
                st.markdown(f"**Education:** {candidate['education']}")
                st.markdown("**Resume Summary:**")
                st.markdown(candidate['resume_summary'])
        
        with col2:
            st.markdown(f"### {job['title']}")
            st.markdown(f"**Department:** {job['department']}")
            with st.expander("Job Requirements"):
                st.markdown(job['requirements'])
                st.markdown(f"**Skills Required:** {job['skills_required']}")
                st.markdown(f"**Experience Required:** {job['experience_required']}")
        
        if st.button("Screen Candidate"):
            with st.spinner("Screening candidate..."):
                screening_agent = ScreeningAgent()
                result = screening_agent.screen_candidate(candidate_id, job_id)
                
                if "error" in result:
                    st.error(result["error"])
                else:
                    st.success("Screening completed!")
                    show_screening_results(result)

def show_screening_results(result):
    st.subheader("Screening Results")
    
    score = result['score']
    st.metric("Match Score", f"{int(score * 100)}%")
    
    score_color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
    st.markdown(f"<div style='background-color: {score_color}; height: 10px; width: {int(score * 100)}%; border-radius: 5px;'></div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Skill Matches")
        for skill in result.get('skill_matches', []):
            st.markdown(f"✅ {skill}")
    
    with col2:
        st.markdown("### Skill Gaps")
        for skill in result.get('skill_gaps', []):
            st.markdown(f"❌ {skill}")
    
    st.markdown("### Assessment")
    st.markdown(result['assessment'])
    
    st.subheader("Next Steps")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Schedule Interview"):
            st.session_state.current_page = "scheduling"
            st.session_state.selected_candidate = result['candidate']['id']
            st.session_state.selected_job = result['job']['id']
            st.rerun()
    
    with col2:
        if st.button("Engage with Candidate"):
            st.session_state.current_page = "chat"
            st.session_state.selected_candidate = result['candidate']['id']
            st.session_state.selected_job = result['job']['id']
            st.rerun()

# ---------------------------
# RESUME ATS CALCULATOR
# ---------------------------

def extract_text_from_pdf(pdf_file) -> str:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.getvalue()))
        return "".join([page.extract_text() for page in pdf_reader.pages])
    except Exception as e:
        st.error(f"Error extracting text from PDF: {e}")
        return ""

def compare_resume_with_job(resume_text: str, job_description: str) -> float:
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"""
        As an ATS (Applicant Tracking System) analyzer, evaluate the compatibility between the resume and job description below.

        JOB DESCRIPTION:
        {job_description}

        RESUME:
        {resume_text}

        Analyze how well the resume matches the job requirements and provide a single numerical score between 0 and 1 (where 0 is no match and 1 is perfect match).
        Only return the numerical score and nothing else.
        """
        response = model.generate_content(prompt)
        score_text = response.text.strip()
        for word in score_text.split():
            try:
                score = float(word)
                if 0 <= score <= 1:
                    return score
            except ValueError:
                continue
        import re
        numbers = re.findall(r"0\.\d+|\d+", score_text)
        if numbers:
            return min(max(float(numbers[0]), 0.0), 1.0)
        st.warning("Could not parse a clear score from API response. Using default score.")
        return 0.5
    except Exception as e:
        st.error(f"Error calling Gemini API: {e}")
        return 0.0

def show_resume_analysis():
    st.header("Resume ATS Calculator")

    uploaded_resume = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    job_description = st.text_area("Paste Job Description")

    if st.button("Get ATS Score"):
        if not uploaded_resume:
            st.warning("Please upload a resume PDF.")
            return
        if not job_description.strip():
            st.warning("Please enter a job description.")
            return
        with st.spinner("Analyzing your resume..."):
            resume_text = extract_text_from_pdf(uploaded_resume)
            if not resume_text:
                st.error("Resume text could not be extracted. Try another file.")
                return
            ats_score = compare_resume_with_job(resume_text, job_description)
            st.subheader("ATS Match Score")
            st.metric("Score", f"{int(ats_score * 100)}%")
            color = "green" if ats_score >= 0.8 else "orange" if ats_score >= 0.5 else "red"
            st.markdown(f"<div style='background-color:{color}; height:10px; width:100%; border-radius:5px;'></div>", unsafe_allow_html=True)

# ---------------------------
# MAIN
# ---------------------------

def main():
    show_resume_screening()

if __name__ == "__main__":
    main()
