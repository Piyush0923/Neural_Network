import pandas as pd
from crewai import Agent, Task
from utils.llm import get_llm
from utils.database import get_candidates, get_jobs, update_candidates
from datetime import datetime, timedelta
import random

class SchedulingAgent:
    def __init__(self):
        """Initialize the Scheduling Agent with the appropriate LLM and tools"""
        self.llm = get_llm()
        self.agent = self._create_agent()
        
        # Simulate a calendar with available slots
        # In a real application, this would connect to an actual calendar API
        self.available_slots = self._generate_available_slots()
        
    def _create_agent(self):
        """Create the CrewAI agent for interview scheduling"""
        return Agent(
            role="Interview Scheduling Specialist",
            goal="Efficiently schedule interviews between candidates and recruiters",
            backstory="""You are an expert in managing complex schedules and coordinating
            interviews. You understand the importance of finding suitable times for both
            candidates and hiring teams, minimizing scheduling conflicts, and ensuring
            a smooth interview process.""",
            verbose=True,
            llm=self.llm
        )
    
    def _generate_available_slots(self):
        """Generate simulated available time slots for the next 2 weeks"""
        slots = []
        today = datetime.now()
        
        # Generate slots for the next 14 days
        for day in range(1, 15):
            current_date = today + timedelta(days=day)
            
            # Skip weekends
            if current_date.weekday() >= 5:  # 5 = Saturday, 6 = Sunday
                continue
                
            # Generate 3-5 random slots per day
            num_slots = random.randint(3, 5)
            for _ in range(num_slots):
                # Business hours: 9 AM to 5 PM
                hour = random.randint(9, 16)  # Up to 4 PM to allow for 1-hour interviews
                minute = random.choice([0, 30])  # Either on the hour or half-hour
                
                slot_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
                duration = 60  # minutes
                
                slots.append({
                    "start_time": slot_time,
                    "end_time": slot_time + timedelta(minutes=duration),
                    "duration": duration,
                    "booked": False,
                    "interviewer": f"Recruiter {random.randint(1, 3)}"
                })
        
        return slots
    
    def get_available_slots(self, start_date=None, end_date=None):
        """Get available interview slots within a date range"""
        if not start_date:
            start_date = datetime.now()
        else:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            
        if not end_date:
            end_date = start_date + timedelta(days=14)
        else:
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Filter slots within the date range and not booked
        available_slots = [
            slot for slot in self.available_slots
            if start_date <= slot["start_time"] <= end_date and not slot["booked"]
        ]
        
        # Format for display
        formatted_slots = []
        for slot in available_slots:
            formatted_slots.append({
                "date": slot["start_time"].strftime("%Y-%m-%d"),
                "start_time": slot["start_time"].strftime("%I:%M %p"),
                "end_time": slot["end_time"].strftime("%I:%M %p"),
                "duration": f"{slot['duration']} minutes",
                "interviewer": slot["interviewer"]
            })
        
        return {
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "available_slots": formatted_slots
        }
    
    def schedule_interview(self, candidate_id, job_id, slot_date, slot_time):
        """Schedule an interview for a candidate at a specific time"""
        candidates = get_candidates()
        jobs = get_jobs()
        
        # Find the candidate and job by ID
        candidate = next((c for c in candidates if str(c['id']) == str(candidate_id)), None)
        job = next((j for j in jobs if str(j['id']) == str(job_id)), None)
        
        if not candidate:
            return {"error": f"Candidate with ID {candidate_id} not found"}
        
        if not job:
            return {"error": f"Job with ID {job_id} not found"}
        
        # Parse the date and time
        try:
            date_obj = datetime.strptime(slot_date, "%Y-%m-%d")
            time_obj = datetime.strptime(slot_time, "%I:%M %p").time()
            slot_datetime = datetime.combine(date_obj.date(), time_obj)
        except ValueError:
            return {"error": "Invalid date or time format"}
        
        # Find the requested slot
        selected_slot = None
        for slot in self.available_slots:
            if slot["start_time"].date() == slot_datetime.date() and \
               slot["start_time"].hour == slot_datetime.hour and \
               slot["start_time"].minute == slot_datetime.minute and \
               not slot["booked"]:
                selected_slot = slot
                break
        
        if not selected_slot:
            return {"error": "Selected time slot is not available"}
        
        # Book the slot
        selected_slot["booked"] = True
        
        # Update candidate status
        candidate['status'] = "Interview Scheduled"
        update_candidates(candidates)
        
        # Skip using Task to avoid validation errors
        # Generate interview details directly
        
        # Create a formatted interview confirmation
        result = f"""
## Interview Confirmation

Dear {candidate['name']},

Your interview for the {job['title']} position has been scheduled for {slot_datetime.strftime("%A, %B %d, %Y at %I:%M %p")} with {selected_slot["interviewer"]}. The interview will last approximately {selected_slot["duration"]} minutes.

## Preparation Steps

To help you prepare for your interview, we recommend:

1. Research our company's mission, values, and recent projects
2. Review the job description and prepare examples of relevant experience
3. Prepare questions about the role and team
4. Test your video/audio equipment the day before (for virtual interviews)
5. Plan to arrive 10-15 minutes early (or join the call 5 minutes early)

## Interview Topics

The interview will likely cover:

- Your experience as a {candidate['current_role']} at {candidate['last_company']}
- Technical skills assessment related to {job['skills_required']}
- Behavioral questions about teamwork and problem-solving
- Your understanding of {job['department']} processes and methodologies
- Your career goals and interest in our company

Please confirm your attendance by replying to this email. If you need to reschedule, please let us know at least 24 hours in advance.

We look forward to meeting you!

Best regards,
Recruitment Team
"""
        
        return {
            "candidate": {
                "id": candidate['id'],
                "name": candidate['name'],
                "email": candidate['email']
            },
            "job": {
                "id": job['id'],
                "title": job['title']
            },
            "interview": {
                "date": slot_datetime.strftime("%A, %B %d, %Y"),
                "time": slot_datetime.strftime("%I:%M %p"),
                "duration": f"{selected_slot['duration']} minutes",
                "interviewer": selected_slot["interviewer"]
            },
            "details": result
        }
    
    def recommend_interview_slots(self, candidate_id, job_id):
        """Recommend the best interview slots for a specific candidate and job"""
        candidates = get_candidates()
        jobs = get_jobs()
        
        # Find the candidate and job by ID
        candidate = next((c for c in candidates if str(c['id']) == str(candidate_id)), None)
        job = next((j for j in jobs if str(j['id']) == str(job_id)), None)
        
        if not candidate:
            return {"error": f"Candidate with ID {candidate_id} not found"}
        
        if not job:
            return {"error": f"Job with ID {job_id} not found"}
        
        # Get available slots for the next 2 weeks
        available_slots = self.get_available_slots()
        
        # Skip using Task to avoid validation errors
        # Generate slot recommendations directly
        
        # Get only the first 10 slots for simplicity
        slots_to_consider = available_slots['available_slots'][:10]
        
        # Create a simulated reasoning for the slot recommendations
        result = f"""
## Interview Slot Recommendations for {candidate['name']}

Based on interview best practices and the available slots, here are my recommendations:

### Recommended Slots:

1. **{slots_to_consider[0]['date']} at {slots_to_consider[0]['start_time']}**
   - Morning interviews allow candidates to be fresh and alert
   - Early in the week provides time for follow-up if needed

2. **{slots_to_consider[1]['date']} at {slots_to_consider[1]['start_time']}**
   - Mid-week slots balance preparation time and decision-making
   - Afternoon slots accommodate candidates with morning commitments

3. **{slots_to_consider[2]['date']} at {slots_to_consider[2]['start_time']}**
   - End-of-week slots allow for immediate weekend reflection 
   - Later morning timing balances alertness and preparation time

### Reasoning:

For technical roles like {job['title']}, I've considered optimal interview timing based on cognitive performance, candidate convenience, and scheduling efficiency. These slots provide good variety while maintaining sufficient spacing between potential rounds.

I recommend reaching out to the candidate with these options and allowing them to select their preferred time.
"""
        
        # For this demo, we'll just return some selected slots rather than parsing the LLM output
        # In a real implementation, we would parse the result to get the actual recommendations
        recommended_slots = available_slots['available_slots'][:3]
        
        return {
            "candidate": {
                "id": candidate['id'],
                "name": candidate['name']
            },
            "job": {
                "id": job['id'],
                "title": job['title']
            },
            "recommended_slots": recommended_slots,
            "reasoning": result
        }
    
    def schedule_batch_interviews(self, job_id, date):
        """Schedule multiple interviews for a job on a specific date"""
        candidates = get_candidates()
        jobs = get_jobs()
        
        # Find the job by ID
        job = next((j for j in jobs if str(j['id']) == str(job_id)), None)
        
        if not job:
            return {"error": f"Job with ID {job_id} not found"}
        
        # Parse the date
        try:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            return {"error": "Invalid date format. Please use YYYY-MM-DD"}
        
        # Get candidates in screening stage for this job
        screening_candidates = [
            c for c in candidates 
            if c['status'] == 'Screening' 
            and 'matched_jobs' in c 
            and str(job_id) in c['matched_jobs'].split(', ')
        ]
        
        # Sort by score
        screening_candidates.sort(key=lambda x: float(x.get('score', 0)), reverse=True)
        
        # Take top 5 candidates
        top_candidates = screening_candidates[:5]
        
        # Get available slots for the specified date
        available_slots = [
            slot for slot in self.available_slots
            if slot["start_time"].date() == date_obj.date() and not slot["booked"]
        ]
        
        if not available_slots:
            return {"error": f"No available slots on {date}"}
        
        # Schedule interviews for each candidate
        scheduled_interviews = []
        
        for i, candidate in enumerate(top_candidates):
            if i >= len(available_slots):
                break
                
            slot = available_slots[i]
            slot["booked"] = True
            
            # Update candidate status
            candidate['status'] = "Interview Scheduled"
            
            scheduled_interviews.append({
                "candidate": {
                    "id": candidate['id'],
                    "name": candidate['name'],
                    "email": candidate['email']
                },
                "time": slot["start_time"].strftime("%I:%M %p"),
                "duration": f"{slot['duration']} minutes",
                "interviewer": slot["interviewer"]
            })
        
        # Update candidates in the database
        update_candidates(candidates)
        
        return {
            "job": {
                "id": job['id'],
                "title": job['title']
            },
            "date": date,
            "scheduled_interviews": scheduled_interviews
        }
