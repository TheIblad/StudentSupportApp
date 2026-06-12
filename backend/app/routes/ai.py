import os, io, json, math
from urllib.parse import unquote
from fastapi import APIRouter, HTTPException, Form
from dotenv import load_dotenv
from openai import OpenAI
from PyPDF2 import PdfReader # Alternatives = PyMuPDF, pdfplumber
from datetime import datetime, time, timedelta

from app.database import supabase

load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key = OPENAI_API_KEY)

router = APIRouter()

@router.get("/quiz_results")
def get_quiz_results(user_id: str):
    response = supabase.table("quiz_results").select("*").eq("user_id", user_id).execute()
    return response.data

@router.get("/ai_journals")
def get_ai_journals(user_id: str):
    response = supabase.table("ai_journals").select("*").eq("user_id", user_id).execute()
    return response.data

# Helper - extract text from the bytes of a PDF
# Could be improved using chunking for large documents but this hasn't been done yet
def extract_text_from_pdf(file_bytes: bytes) -> str:
    pdf_reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in pdf_reader.pages: # For each page, if it exists, add it to the text after a new line
        page_text = page.extract_text()
        if page_text: text += page_text + "\n"
    return text

@router.post("/ai")
async def post_generation_request(request: dict):
    file_name = request["file_name"]
    request_type = request["type"]

    file = supabase.table("documents").select("*").eq("file_name", file_name).execute() # Get the row representing the file

    file_location = file.data[0]["file_location"] # Get the file's location i.e. the full URL out of the row

    #file_path = unquote(file_location.split("/")[-1]) # Get the file path out of the full URL and handle spaces

    file_path = file_location.split("/")[-2] + "/" + unquote(file_location.split("/")[-1]) # TEST - seems to work

    # Download file (in bytes) from Supabase
    try: file_bytes = supabase.storage.from_("documents").download(file_path)
    except Exception: raise HTTPException(status_code = 400, detail = "File Not Downloaded")

    file_text = extract_text_from_pdf(file_bytes) # Extract the file's text using the helper

    # Generate the correct instruction
    if request_type == "summary":
        instruction = """
Summarise in paragraphs the following academic content in clear concise language.

Avoid using LaTeX formatting. Use plain text equations where necessary.
"""
    elif request_type == "flashcards":
        instruction = """
Create study flashcards from the following academic content.

Return ONLY valid JSON in the format:

[
  {
    "question": "Question text",
    "answer": "Answer text"
  },
  {
    "question": "Question text",
    "answer": "Answer text"
  }
]

Avoid using LaTeX formatting. Use plain text equations where necessary.
"""
    elif request_type == "quiz":
        instruction = """
Create a multiple-choice quiz from the following academic content.

Return ONLY valid JSON in the format:

[
  {
    "question": "Question text",
    "options": ["A", "B", "C", "D"],
    "answer": "Correct option"
  },
  {
    "question": "Question text",
    "options": ["A", "B", "C", "D"],
    "answer": "Correct option"
  }
]

The correct option for each question MUST be one of: A, B, C, D

Each of the four options for each question MUST begin with a single upper-case letter (use: A, B, C, D in alphabetical order) followed by . or )

Avoid using LaTeX formatting. Use plain text equations where necessary.
"""

    # Call AI using the correct instruction above
    try:
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "You are an academic assistant that clearly and concisely generates academic content including: summaries, flashcards, quizzes."
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"{instruction}\n\n{file_text[:15000]}"
                        }
                    ],
                },
            ],
            temperature = 0.3,
        )

        output_text = response.output_text

    except Exception as e:
        raise HTTPException(status_code = 400, detail = "OpenAI API Error")
    
    # Upload the generated content to the database
    # First, convert the generated content to the correct format depending on what type of content it is
    if request_type == "summary":
        new_value = output_text # Summaries stay as text
    else:
        new_value = json.loads(output_text) # Flashcards and quizzes get converted into JSON

    # Create the row that will be upserted into the database
    # Only the file_name, since its unique, and the type of content need to be known - everything else is either left null or generated automatically
    new_row = {"file_name": file_name}
    if request_type == "summary":
        new_row["summary"] = new_value
    elif request_type == "flashcards":
        new_row["flashcards"] = new_value
    elif request_type == "quiz":
        new_row["quiz"] = new_value

    # Upsert the row into the database (update if the row already exists and insert if it doesn't yet)
    supabase.table("ai_documents").upsert(new_row, on_conflict = "file_name").execute()

    return {request_type: new_value}

@router.post("/ai/ask_question")
def ask_question(request: dict):
    summary = request["summary"]
    question = request["question"]

    instruction = f"""
Below is a summary of an academic document and a question regarding it.

Summary:
{summary}

Question:
{question}

Produce an answer to the question using both the summary and general knowledge about the topics mentioned in the summary.

Keep your answer concise, clear, and reliable.

Avoid using LaTeX formatting. Use plain text equations where necessary.

If the question makes no sense or is not related to the topics mentioned in the summary then just say so.
"""
    try:
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "You are an academic assistant that clearly, concisely, and reliably answers questions about academic content."
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": instruction
                        }
                    ],
                },
            ],
            temperature = 0.3,
        )
        
        output_text = response.output_text
    
    except Exception as e:
        raise HTTPException(status_code = 400, detail = "OpenAI API Error")

    return {"answer": output_text}

# Similar to above but for performing analysis on journal entries
@router.post("/ai/journal_analysis")
def process_journal_analysis_request(request: dict):
    user_id = request.get("user_id")
    date = request["date"]
    entry = request["entry"]

    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    instruction = """
Perform an analysis on the following journal entry.

Return ONLY valid JSON in the format:

{
  "sentiment_score": a number from 1 to 10,
  "insight": "...",
  "suggestion": "..."
}

The sentiment_score scale is as follows:
1 to 2 = very negative
3 to 4 = negative
5 to 6 = neutral
7 to 9 = positive
9 to 10 = very positive

The insight and suggestion should be short and relevant to the journal entry.
The suggestion should be gentle and not too specific.
"""

    try:
        response = openai_client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "You are an academic wellbeing assistant that performs analysis on journal entries for sentiment detection and support"
                        }
                    ],
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_text",
                            "text": f"{instruction}\n\n{entry}"
                        }
                    ],
                },
            ],
            temperature = 0.3,
        )

        output_text = response.output_text

    except Exception as e:
        raise HTTPException(status_code = 400, detail = "OpenAI API Error")

    analysis = json.loads(output_text)

    # Validation on the type of the AI-generated sentiment score which should be an integer
    sentiment_score = analysis["sentiment_score"]
    if not isinstance(sentiment_score, int):
        sentiment_score = 5 # Fallback, though testing confirmed that this function is reliable

    supabase.table("ai_journals").upsert({
        "user_id": user_id,
        "date": date,
        "sentiment_score": sentiment_score,
        "insight": analysis["insight"],
        "suggestion": analysis["suggestion"]
    }, on_conflict = "user_id,date").execute()

    return analysis

# Get journaling trends for display in frontend
# Similar logic to scheduler above
@router.get("/ai/journaling_trends")
def get_journaling_trends(user_id: str):
    ai_journals = supabase.table("ai_journals").select("*").eq("user_id", user_id).execute().data
    if not ai_journals:
        return {
            "mood_history": [],
            "recent_suggestion": "Start journaling to get insights!",
            "need_support": False
        }

    # For mood graph in frontend: x-axis = date (in chronological order), y-axis = sentiment_score
    ai_journals = sorted(ai_journals, key=lambda journal: journal["date"])
    mood_history = [] # Array of (date, sentiment_score) objects
    for journal in ai_journals:
        mood_history.append({"date": journal["date"], "sentiment_score": journal["sentiment_score"]})

    # For showing the most recent suggestion in frontend
    ai_journals = sorted(ai_journals, key=lambda journal: journal["date"], reverse=True)
    recent_suggestion = ai_journals[0]["suggestion"]

    # Compute wellbeing scores using the last 3 journal entries (same logic as scheduler)
    recent_journals = ai_journals[:3]
    mood_score = sum(journal["sentiment_score"] for journal in recent_journals) / len(recent_journals)
    trend_score = recent_journals[0]["sentiment_score"] - recent_journals[-1]["sentiment_score"]

    need_support = False
    if mood_score <= 6 or trend_score < -2:
        need_support = True

    return {
        "mood_history": mood_history[-3:], # Array of (date, sentiment_score) objects
        "recent_suggestion": recent_suggestion, # String
        "need_support": need_support # Boolean
    }

# Get academic trends for display in frontend
# Similar logic to scheduler above
@router.get("/ai/academic_trends")
def get_academic_trends(user_id: str):
    quiz_results = (
        supabase.table("quiz_results")
        .select("score, total_questions, file_name, created_at, documents(module)")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    first_attempts = {} # Key = file name, value = first attempt result
    for result in quiz_results:
        file_name = result["file_name"]
        if file_name not in first_attempts:
            first_attempts[file_name] = result
        else:
            if result["created_at"] < first_attempts[file_name]["created_at"]:
                first_attempts[file_name] = result

    module_scores = {} # Key = module name, value = array of (first attempt) results for each related quiz
    module_scores_history = {} # Key = module name, value = array of (created_at, percentage_score) objects for each related quiz
    for result in first_attempts.values():
        module_name = result["documents"]["module"]
        percentage_score = result["score"] / result["total_questions"]
        if module_name not in module_scores:
            module_scores[module_name] = []
        module_scores[module_name].append(percentage_score)
        if module_name not in module_scores_history:
            module_scores_history[module_name] = []
        module_scores_history[module_name].append({"created_at": result["created_at"], "percentage_score": round(percentage_score * 100, 2)})

    module_scores_averages = [] # Array of (module, average_percentage_score) objects - one object per module
    for module, scores in module_scores.items():
        average_percentage_score = sum(scores) / len(scores)
        module_scores_averages.append({"module": module, "average_percentage_score": round(average_percentage_score * 100, 2)})

    # Support could be needed if the average score for any module is less than 60%
    need_support = False
    for module in module_scores_averages:
        if module["average_percentage_score"] < 60: need_support = True

    # module_scores_history is for the line charts in frontend
    # module_scores_averages is for the bar chart in frontend
    return {
        "module_scores_history": module_scores_history, # Dictionary: module ---> array of (created_at, percentage_score) objects
        "module_scores_averages": module_scores_averages, # Array of (module, average_percentage_score) objects
        "need_support": need_support # Boolean
    }

# Upload a quiz result
@router.post("/ai/quiz_result")
def upload_quiz_result(result: dict):
    user_id = result.get("user_id")
    if not user_id:
        raise HTTPException(status_code=400, detail="Missing user_id")

    response = supabase.table("quiz_results").insert({
        "user_id": user_id,
        "file_name": result["file_name"],
        "score": result["score"],
        "total_questions": result["total_questions"]
    }).execute()
    
    if response.data is None or response.data == []: raise HTTPException(status_code = 400, detail = "Quiz Result Not Added")

    return response.data[0]

# Scheduler
# Runs when a task is created, updated, or removed
@router.post("/ai/generate_schedule")
def generate_schedule(user_id: str):
    today_date = datetime.today().date()

    # Remove the previous schedule because a new one will be created
    supabase.table("scheduled_entries").delete().eq("user_id", user_id).execute()

    # Load inputs from database
    tasks = supabase.table("tasks").select("*").eq("user_id", user_id).execute().data
    ai_journals = supabase.table("ai_journals").select("*").eq("user_id", user_id).execute().data
    timetable_entries = supabase.table("timetable_entries").select("*").eq("user_id", user_id).execute().data

    # Arrays to hold the sessions that will be created and eventually scheduled
    study_sessions = []
    wellbeing_sessions = []
    task_sessions = []

    # Get academic performance by module
    # Join quiz_results with documents on file_name (FK) to get module names
    quiz_results = (
        supabase.table("quiz_results")
        .select("score, total_questions, file_name, created_at, documents(module)")
        .eq("user_id", user_id)
        .execute()
        .data
    )

    # Use only the result of the first attempt on (the quiz generated from) each document to avoid resit results skewing performance
    first_attempts = {} # Key = file name, value = first attempt result
    for result in quiz_results:
        file_name = result["file_name"]
        if file_name not in first_attempts:
            first_attempts[file_name] = result
        else:
            if result["created_at"] < first_attempts[file_name]["created_at"]:
                first_attempts[file_name] = result

    module_scores = {} # Key = module name, value = array of (score, created_at) tuples for each related quiz
    for result in first_attempts.values():
        module_name = result["documents"]["module"] # Join operations return an object with a nested object representing the other row
        percentage_score = result["score"] / result["total_questions"]
        created_at = result["created_at"]
        if module_name not in module_scores:
            module_scores[module_name] = []
        module_scores[module_name].append((percentage_score, created_at))

    # Identify the weaker modules i.e. those where the weighted average (first attempt) quiz score is less than 70%
    # Weakness level uses exponential decay to weight recent quizzes more heavily (30-day half-life)
    weak_modules = []
    weakness_levels = {}
    for module, score_data in module_scores.items():
        # Calculate time-weighted average using exponential decay
        weighted_sum = 0
        total_weight = 0

        for score, created_at in score_data:
            created_date = datetime.strptime(created_at.split('T')[0], "%Y-%m-%d").date()
            days_ago = (today_date - created_date).days

            # Exponential decay: recent quizzes matter more (30-day half-life)
            weight = math.exp(-days_ago / 30)

            weighted_sum += score * weight
            total_weight += weight

        average_score = weighted_sum / total_weight if total_weight > 0 else 0
        if average_score < 0.7:
            weak_modules.append(module)
            weakness_levels[module] = average_score

    # Create study sessions for the weaker modules
    # The number of study sessions created for a module and the duration of those study sessions are based on its weakness level
    # Duration (in minutes) will be replaced by start_time and end_time when these sessions are eventually scheduled
    # A soft due-date is added now for scheduling later
    for module in weak_modules:
        weakness_level = weakness_levels[module]
        number_of_sessions = 1
        duration = 90
        if weakness_level < 0.6: # Longer session
            number_of_sessions = 1
            duration = 120
        if weakness_level < 0.5: # More sessions
            number_of_sessions = 2
            duration = 120
        for each in range(number_of_sessions):
            study_sessions.append({
                "name": module + ": Study Session",
                "category": "academic",
                "duration": duration,
                "due_date": today_date + timedelta(days=7)
            })

    # Compute wellbeing score from AI journal analyses
    # Recent mood and trend are both considered
    mood_score = 0
    trend_score = 0
    recent_journals = []
    if len(ai_journals) > 0:
        # Get the sentiment scores on up to 10 most recent journal entries (more data, better analysis)
        ai_journals_sorted = sorted(ai_journals, key=lambda journal: journal["date"], reverse=True)
        recent_journals = ai_journals_sorted[:10]

        # Time-weighted mood score using exponential decay (7-day half-life)
        weighted_mood = 0
        total_weight = 0

        for journal in recent_journals:
            journal_date = datetime.strptime(journal["date"], "%Y-%m-%d").date()
            days_ago = (today_date - journal_date).days

            # Exponential decay: more recent entries weighted more heavily (7-day half-life)
            weight = math.exp(-days_ago / 7)

            weighted_mood += journal["sentiment_score"] * weight
            total_weight += weight

        mood_score = weighted_mood / total_weight if total_weight > 0 else 7  # Neutral default

        # Calculate trend using linear regression (slope indicates improving/declining mood)
        if len(recent_journals) >= 3:
            # Convert to (days_ago, sentiment) pairs for regression
            data_points = []
            for journal in recent_journals:
                journal_date = datetime.strptime(journal["date"], "%Y-%m-%d").date()
                days_ago = (today_date - journal_date).days
                data_points.append((-days_ago, journal["sentiment_score"]))  # Negative so recent is higher

            # Simple linear regression: slope = trend
            n = len(data_points)
            x_values = [p[0] for p in data_points]
            y_values = [p[1] for p in data_points]

            x_mean = sum(x_values) / n
            y_mean = sum(y_values) / n

            numerator = sum((x_values[i] - x_mean) * (y_values[i] - y_mean) for i in range(n))
            denominator = sum((x_values[i] - x_mean) ** 2 for i in range(n))

            trend_score = numerator / denominator if denominator != 0 else 0
            # Positive trend = improving mood, Negative = declining
        else:
            trend_score = 0  # Not enough data for trend analysis

        # Create wellbeing sessions if mood is low or trend is negative, similar to the study sessions above
        if mood_score <= 6 or trend_score < -2:
            wellbeing_sessions.append({
                "name": "Do some mindfulness activities",
                "category": "wellbeing",
                "duration": 120,
                "due_date": today_date + timedelta(days=7)
            })

    # Compute a priority score for each task that isn't completed using a formula:
    # priority_score = urgency_weight + user_priority_weight + user_status_weight + academic_weakness_weight
    tasks_to_schedule = [] # Array which will contain task objects but with priority scores - these are ready to be scheduled
    for task in tasks:
        if task["status"] == "Complete":
            continue

        priority_score = 0

        # Urgency weight = 1 / days until deadline
        due_date = datetime.strptime(task["due_date"], "%Y-%m-%d").date()
        days_until_deadline = (due_date - today_date).days
        if days_until_deadline <= 0: urgency_weight = 1 
        else: urgency_weight = round(1 / days_until_deadline, 2)

        # User priority weight
        if task["priority"] == "High": user_priority_weight = 0.5
        elif task["priority"] == "Medium": user_priority_weight = 0.25
        else: user_priority_weight = 0

        # User status weight
        if task["status"] == "Incomplete - Not Started": user_status_weight = 0.5
        else: user_status_weight = 0.25

        # Academic weakness weight
        if ("module" in task) and task["module"] in weak_modules: academic_weakness_weight = 0.25
        else: academic_weakness_weight = 0

        priority_score += urgency_weight + user_priority_weight + user_status_weight + academic_weakness_weight
        task["priority_score"] = priority_score

        tasks_to_schedule.append(task)

    # Find candidate slots to insert sessions into (the slots not occupied by fixed timetable entries)
    candidate_slots = []

    days_to_schedule = 7 # Schedule sessions over the next 7 days including today

    for day_number in range(days_to_schedule):
        current_day = today_date + timedelta(days=day_number)

        # Daily scheduling window is noon to 10pm (the period of time during which sessions are allowed to be scheduled)
        # Deals with partial or non-existent timetable input by assuming free days by default
        current_day_start = time(hour=12, minute=0)
        if current_day == datetime.now().date():
            current_day_start = time(hour=datetime.now().hour + 1, minute=0)
        current_day_end = time(hour=22, minute=0)

        if current_day_start >= current_day_end: continue # If the scheduler runs too late in the day then move on to the next day

        # Get the current day's timetable entries in order
        current_day_entries = []
        for entry in timetable_entries:
            if datetime.strptime(entry["date"], "%Y-%m-%d").date() == current_day:
                current_day_entries.append(entry)
        current_day_entries = sorted(current_day_entries, key=lambda entry: entry["start_time"])

        # Move through the current day's scheduling window and record gaps (candidate slots) between timetable entries
        current_time = current_day_start
        for entry in current_day_entries:
            entry_start = datetime.strptime(entry["start_time"], "%H:%M:%S").time()
            entry_end = datetime.strptime(entry["end_time"], "%H:%M:%S").time()

            # Record the gap before the next timetable entry
            if entry_start > current_time:
                gap_minutes = int((datetime.combine(current_day, entry_start) - datetime.combine(current_day, current_time)).total_seconds()) // 60
                # Ignore gaps less than an hour long
                if gap_minutes > 60:
                    candidate_slots.append({
                        "date": current_day,
                        "start_time": current_time,
                        "end_time": entry_start,
                        "duration": gap_minutes
                    })
            if entry_end > current_time:
                current_time = entry_end

        # Record the gap after the last timetable entry
        if current_time < current_day_end:
            gap_minutes = int((datetime.combine(current_day, current_day_end) - datetime.combine(current_day, current_time)).total_seconds()) // 60
            # Ignore gaps less than an hour long
            if gap_minutes > 60:
                candidate_slots.append({
                    "date": current_day,
                    "start_time": current_time,
                    "end_time": current_day_end,
                    "duration": gap_minutes
                })

    # Create task sessions by splitting up each task with smart duration handling
    # Short tasks are not split; longer tasks use variable session lengths
    for task in tasks_to_schedule:
        duration = int(task["estimated_duration"])

        # Don't split short tasks (≤90 minutes)
        if duration <= 90:
            task_sessions.append({
                "name": task["name"],
                "category": "task",
                "duration": duration,
                "due_date": datetime.strptime(task["due_date"], "%Y-%m-%d").date(),
                "priority_score": task["priority_score"]
            })
        else:
            # Determine session length: longer sessions for tasks in weak modules
            module = task.get("module", "")
            base_session = 90 if module in weak_modules else 60

            # Split with smart remainder handling to avoid tiny last sessions
            remaining = duration
            session_count = 0

            while remaining > 0:
                if remaining <= base_session * 1.3:
                    # Don't create tiny last session - use all remaining time
                    task_sessions.append({
                        "name": task["name"],
                        "category": "task",
                        "duration": remaining,
                        "due_date": datetime.strptime(task["due_date"], "%Y-%m-%d").date(),
                        "priority_score": task["priority_score"]
                    })
                    break
                else:
                    # Create standard session and continue
                    task_sessions.append({
                        "name": task["name"],
                        "category": "task",
                        "duration": base_session,
                        "due_date": datetime.strptime(task["due_date"], "%Y-%m-%d").date(),
                        "priority_score": task["priority_score"]
                    })
                    remaining -= base_session

    task_sessions = sorted(task_sessions, key=lambda session: session["priority_score"], reverse=True)

    # Combine all sessions
    all_sessions = task_sessions + study_sessions + wellbeing_sessions

    # Shorten all sessions if wellbeing is very low
    if mood_score <= 5:
        for session in all_sessions:
            session["duration"] = int(session["duration"] * 0.8)

    # The entries to be inserted as JSON into the scheduled_entries table
    scheduled_entries = []

    # Sustains engagement by not overwhelming users - limits number of sessions per day to 3 and spreads sessions across days, leaving buffer time between sessions
    max_sessions_per_day = 3
    daily_session_count = {}

    # Allocate all sessions into candidate slots (greedily)
    for session in all_sessions:
        for slot in candidate_slots:
            # Do not schedule sessions if their due dates have passed
            slot_date = slot["date"]
            if slot_date > session["due_date"]: continue

            if (slot_date in daily_session_count) and (daily_session_count[slot_date] >= max_sessions_per_day): continue

            slot_buffered_duration = int(slot["duration"] * 0.8)
            if session["duration"] <= slot_buffered_duration:
                start_time = slot["start_time"]
                end_time = (datetime.combine(slot_date, start_time) + timedelta(minutes=session["duration"])).time()
                scheduled_entries.append({
                    "name": session["name"],
                    "category": session["category"],
                    "date": slot_date.strftime("%Y-%m-%d"),
                    "start_time": start_time.strftime("%H:%M:%S"),
                    "end_time": end_time.strftime("%H:%M:%S"),
                    "user_id": user_id
                })

                # Update the slot because a session was scheduled in it
                buffer_time = 60
                if session["category"] == "academic": buffer_time = 120
                slot["start_time"] = (datetime.combine(slot_date, end_time) + timedelta(minutes=buffer_time)).time()
                slot["duration"] -= session["duration"]

                if (slot_date in daily_session_count): daily_session_count[slot_date] += 1
                else: daily_session_count[slot_date] = 1

                break # Break because a session only needs to be scheduled once

    # Add user_id to all scheduled entries
    for entry in scheduled_entries:
        entry["user_id"] = user_id

    if scheduled_entries:
        supabase.table("scheduled_entries").insert(scheduled_entries).execute()

    # Return clean summary for frontend
    return {
        "success": True,
        "scheduled_count": len(scheduled_entries),
        "study_sessions_created": len(study_sessions),
        "wellbeing_sessions_created": len(wellbeing_sessions),
        "days_scheduled": days_to_schedule,
        "mood_score": round(mood_score, 2),
        "trend_score": round(trend_score, 3),
        "weak_modules": weak_modules
    }

# Get a document's AI-generated content (summary, flashcards, quiz) from the database
@router.get("/ai/{file_name}")
def get_document_ai_content(file_name: str):
    response = supabase.table("ai_documents").select("summary, flashcards, quiz").eq("file_name", file_name).execute()
    if response.data is None or response.data == []: return {"summary": None, "flashcards": None, "quiz": None}
    return response.data[0]
