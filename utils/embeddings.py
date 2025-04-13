import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from utils.llm import get_embedding_model

# Initialize the embedding model
model = get_embedding_model()

def get_embedding(text):
    """Convert text to embedding using our embedding model"""
    if not text.strip():
        return None
    try:
        return model.encode(text)
    except Exception as e:
        print(f"[Embedding Error] Failed to encode text: {e}")
        return None

def compare_texts(text1, text2):
    """Compare two text passages and return similarity score"""
    embedding1 = get_embedding(text1)
    embedding2 = get_embedding(text2)

    if embedding1 is None or embedding2 is None:
        return 0.0

    embedding1 = embedding1.reshape(1, -1)
    embedding2 = embedding2.reshape(1, -1)

    similarity = cosine_similarity(embedding1, embedding2)[0][0]
    return similarity

def compare_resume_with_job(candidate, job):
    resume_text = str(candidate.get('resume_summary', ''))
    job_description = str(job.get('requirements', ''))

    vectorizer = TfidfVectorizer().fit_transform([resume_text, job_description])
    similarity = cosine_similarity(vectorizer[0:1], vectorizer[1:2])

    score = similarity[0][0]
    result = {
        'score': score,
        'candidate': candidate,
        'job': job,
        'skill_matches': [],
        'skill_gaps': [],
        'assessment': f"This candidate's resume matches the job by {int(score * 100)}%."
    }
    return result

def create_candidate_embeddings(candidates):
    embeddings = {}

    for candidate in candidates:
        candidate_text = f"""
        {candidate['name']}
        {candidate['current_role']}
        {candidate['skills']}
        {candidate['resume_summary']}
        {candidate['years_experience']} years experience
        Education: {candidate['education']}
        Last company: {candidate['last_company']}
        """

        embedding = get_embedding(candidate_text)
        if embedding is not None:
            embeddings[candidate['id']] = embedding
        else:
            print(f"[Warning] Failed to create embedding for candidate ID {candidate['id']}")

    return embeddings

def create_job_embeddings(jobs):
    embeddings = {}

    for job in jobs:
        job_text = f"""
        {job['title']}
        {job['department']}
        {job['description']}
        Requirements: {job['requirements']}
        Skills required: {job['skills_required']}
        Experience required: {job['experience_required']}
        Education required: {job['education_required']}
        """

        embedding = get_embedding(job_text)
        if embedding is not None:
            embeddings[job['id']] = embedding
        else:
            print(f"[Warning] Failed to create embedding for job ID {job['id']}")

    return embeddings

def find_matching_jobs_for_candidate(candidate, job_embeddings, jobs, threshold=0.6):
    candidate_text = f"""
    {candidate['name']}
    {candidate['current_role']}
    {candidate['skills']}
    {candidate['resume_summary']}
    {candidate['years_experience']} years experience
    Education: {candidate['education']}
    Last company: {candidate['last_company']}
    """

    candidate_embedding = get_embedding(candidate_text)
    if candidate_embedding is None:
        print(f"[Warning] Skipping candidate ID {candidate['id']} due to missing embedding")
        return []

    candidate_embedding = candidate_embedding.reshape(1, -1)

    matches = []

    for job_id, job_embedding in job_embeddings.items():
        if job_embedding is None:
            continue

        job_embedding = job_embedding.reshape(1, -1)
        similarity = cosine_similarity(candidate_embedding, job_embedding)[0][0]

        if similarity >= threshold:
            job = next((j for j in jobs if str(j['id']) == str(job_id)), None)
            if job:
                matches.append({
                    "job_id": job_id,
                    "title": job['title'],
                    "score": round(similarity, 2)
                })

    matches.sort(key=lambda x: x['score'], reverse=True)

    return matches

def find_matching_candidates_for_job(job, candidate_embeddings, candidates, threshold=0.6):
    job_text = f"""
    {job['title']}
    {job['department']}
    {job['description']}
    Requirements: {job['requirements']}
    Skills required: {job['skills_required']}
    Experience required: {job['experience_required']}
    Education required: {job['education_required']}
    """

    job_embedding = get_embedding(job_text)
    if job_embedding is None:
        print(f"[Warning] Skipping job ID {job['id']} due to missing embedding")
        return []

    job_embedding = job_embedding.reshape(1, -1)

    matches = []

    for candidate_id, candidate_embedding in candidate_embeddings.items():
        if candidate_embedding is None:
            continue

        candidate_embedding = candidate_embedding.reshape(1, -1)
        similarity = cosine_similarity(job_embedding, candidate_embedding)[0][0]

        if similarity >= threshold:
            candidate = next((c for c in candidates if str(c['id']) == str(candidate_id)), None)
            if candidate:
                matches.append({
                    "candidate_id": candidate_id,
                    "name": candidate['name'],
                    "current_role": candidate['current_role'],
                    "score": round(similarity, 2)
                })

    matches.sort(key=lambda x: x['score'], reverse=True)

    return matches
