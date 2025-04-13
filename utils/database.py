import os
import pandas as pd
import json

# Paths to CSV files
CANDIDATES_FILE = 'data/candidates.csv'
JOBS_FILE = 'data/jobs.csv'

def setup_database():
    """Ensures the database files exist and are properly formatted"""
    # Check if the data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Load the CSV files if they exist, otherwise create them
    if not os.path.exists(CANDIDATES_FILE) or not os.path.exists(JOBS_FILE):
        print("Creating database files...")
        
        # Create the candidates and jobs dataframes if they don't exist
        # Data is already pre-populated in the CSV files we created
        pass
    else:
        print("Database files already exist.")

def get_candidates():
    """Retrieve all candidates from the database"""
    try:
        df = pd.read_csv(CANDIDATES_FILE)
        # Convert DataFrame to list of dictionaries
        candidates = df.fillna('').to_dict('records')
        return candidates
    except Exception as e:
        print(f"Error loading candidates: {e}")
        return []

def get_jobs():
    """Retrieve all jobs from the database"""
    try:
        df = pd.read_csv(JOBS_FILE)
        # Convert DataFrame to list of dictionaries
        jobs = df.fillna('').to_dict('records')
        return jobs
    except Exception as e:
        print(f"Error loading jobs: {e}")
        return []

def update_candidates(candidates):
    """Update the candidates in the database"""
    try:
        df = pd.DataFrame(candidates)
        df.to_csv(CANDIDATES_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error updating candidates: {e}")
        return False

def update_jobs(jobs):
    """Update the jobs in the database"""
    try:
        df = pd.DataFrame(jobs)
        df.to_csv(JOBS_FILE, index=False)
        return True
    except Exception as e:
        print(f"Error updating jobs: {e}")
        return False

def get_candidate_by_id(candidate_id):
    """Get a specific candidate by ID"""
    candidates = get_candidates()
    candidate = next((c for c in candidates if str(c['id']) == str(candidate_id)), None)
    return candidate

def get_job_by_id(job_id):
    """Get a specific job by ID"""
    jobs = get_jobs()
    job = next((j for j in jobs if str(j['id']) == str(job_id)), None)
    return job

def get_candidates_for_job(job_id):
    """Get all candidates matched to a specific job"""
    candidates = get_candidates()
    matched_candidates = [
        c for c in candidates 
        if 'matched_jobs' in c and c['matched_jobs'] and str(job_id) in c['matched_jobs'].split(', ')
    ]
    return matched_candidates

def get_candidates_by_status(status):
    """Get all candidates with a specific status"""
    candidates = get_candidates()
    filtered_candidates = [c for c in candidates if c.get('status') == status]
    return filtered_candidates

def export_candidates_csv():
    """Export candidates data as CSV"""
    candidates = get_candidates()
    df = pd.DataFrame(candidates)
    return df.to_csv(index=False)

def export_jobs_csv():
    """Export jobs data as CSV"""
    jobs = get_jobs()
    df = pd.DataFrame(jobs)
    return df.to_csv(index=False)

def add_custom_candidate(candidate_data):
    """Add a new candidate to the database"""
    candidates = get_candidates()
    
    # Generate a new ID
    max_id = max([int(c['id']) for c in candidates]) if candidates else 0
    candidate_data['id'] = max_id + 1
    
    # Set default values
    if 'status' not in candidate_data:
        candidate_data['status'] = 'Available'
    if 'score' not in candidate_data:
        candidate_data['score'] = 0.0
    
    # Add to the candidates list
    candidates.append(candidate_data)
    
    # Update the database
    success = update_candidates(candidates)
    return success, candidate_data
