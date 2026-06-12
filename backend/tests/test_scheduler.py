from datetime import datetime, time, timedelta
import math


# TO RUN ALL TESTS:             python -m pytest tests/test_scheduler.py -p no:warnings
# TO RUN A SPECIFIC TEST:       python -m pytest tests/test_scheduler.py::test_name_of_test -p no:warnings




# Duplicate of Scheduler V2 from ai.py
# Database operations removed
def generate_schedule(tasks, ai_journals, timetable_entries, quiz_results):
    today_date = datetime.today().date()

    # Arrays to hold the sessions that will be created and eventually scheduled
    study_sessions = []
    wellbeing_sessions = []
    task_sessions = []

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
                    "end_time": end_time.strftime("%H:%M:%S")
                })

                # Update the slot because a session was scheduled in it
                buffer_time = 60
                if session["category"] == "academic": buffer_time = 120
                slot["start_time"] = (datetime.combine(slot_date, end_time) + timedelta(minutes=buffer_time)).time()
                slot["duration"] -= session["duration"]

                if (slot_date in daily_session_count): daily_session_count[slot_date] += 1
                else: daily_session_count[slot_date] = 1

                break # Break because a session only needs to be scheduled once

    # Output for testing (intermediate results)
    return {
        "candidate_slots": candidate_slots,
        "scheduled_entries": scheduled_entries,
        "tasks_to_schedule": tasks_to_schedule,
        "task_sessions": task_sessions,
        "first_attempts": first_attempts,
        "module_scores" : module_scores,
        "weak_modules": weak_modules,
        "weakness_levels": weakness_levels,
        "study_sessions": study_sessions,
        "recent_journals": recent_journals,
        "mood_score": mood_score,
        "trend_score": trend_score,
        "wellbeing_sessions": wellbeing_sessions
    }




# UNIT TESTING
# Implemented as black-box testing on the scheduler
# Both intermediate results and the actual scheduler output are evaluated for correctness

# Arguments:
# tasks                 (name, description, due_date, priority, status, module, estimated_duration)
# ai_journals           (date, sentiment_score, insight, suggestion)
# timetable_entries     (date, start_time, end_time, title, module, type, location)
# quiz_results          (file_name, score, total_questions, documents: module)


### NO INPUTS ###

# One Simple Test
def test_no_inputs():
    result = generate_schedule([], [], [], [])

    # No entries should be scheduled
    assert len(result["scheduled_entries"]) == 0


### TASK PRIORITY ORDERING ###

# One Comprehensive Test
def test_task_priority_ordering():
    today = datetime.today().date()
    soon_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")
    later_date = (today + timedelta(days=15)).strftime("%Y-%m-%d")

    tasks = [
        {"name": "Task A", "due_date": soon_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task B", "due_date": soon_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task C", "due_date": soon_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task D", "due_date": soon_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task E", "due_date": later_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task F", "due_date": later_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task G", "due_date": later_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task H", "due_date": later_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "60"}
    ]

    result = generate_schedule(tasks, [], [], [])

    tasks_sorted = sorted(result["tasks_to_schedule"], key=lambda task: task["priority_score"], reverse=True)

	# Task B should be first (high priority + not started + soon deadline)
	# Task G should be last (low priority + in progress + later deadline)
    assert tasks_sorted[0]["name"] == "Task B"
    assert tasks_sorted[-1]["name"] == "Task G"

    # Tasks with high priorities should come before those with low priorities
    task_names = [t["name"] for t in tasks_sorted]
    assert task_names.index("Task B") < task_names.index("Task A")
    assert task_names.index("Task D") < task_names.index("Task C")
    assert task_names.index("Task F") < task_names.index("Task E")
    assert task_names.index("Task H") < task_names.index("Task G")

    # Tasks with soon deadlines should come before those with later deadlines
    assert task_names.index("Task A") < task_names.index("Task E")
    assert task_names.index("Task B") < task_names.index("Task F")
    assert task_names.index("Task D") < task_names.index("Task G")
    assert task_names.index("Task D") < task_names.index("Task H")

    # Tasks not started should come before tasks in progress
    assert task_names.index("Task A") < task_names.index("Task C")
    assert task_names.index("Task B") < task_names.index("Task D")
    assert task_names.index("Task E") < task_names.index("Task G")
    assert task_names.index("Task F") < task_names.index("Task H")


### MOOD SCORES COMPUATION ###

# High Upwards-Trending Scores
def test_mood_scores_computation_1():
    today = datetime.today().date()

    ai_journals = [
        {"date": (today - timedelta(days=4)).strftime("%Y-%m-%d"), "sentiment_score": 4},
        {"date": (today - timedelta(days=3)).strftime("%Y-%m-%d"), "sentiment_score": 6},
        {"date": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "sentiment_score": 8},
        {"date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "sentiment_score": 9},
        {"date": today.strftime("%Y-%m-%d"), "sentiment_score": 10}
    ]

    result = generate_schedule([], ai_journals, [], [])

    # Mood uses time-weighted average so recent entries count more
    # Should be higher than simple average (7.4) since recent scores are higher
    assert result["mood_score"] > 7.4
    assert result["mood_score"] < 10

    # Trend should be positive since mood is improving
    assert result["trend_score"] > 0

# Low Downwards-Trending Scores
def test_mood_scores_computation_2():
    today = datetime.today().date()

    ai_journals = [
        {"date": (today - timedelta(days=2)).strftime("%Y-%m-%d"), "sentiment_score": 6},
        {"date": (today - timedelta(days=1)).strftime("%Y-%m-%d"), "sentiment_score": 4},
        {"date": today.strftime("%Y-%m-%d"), "sentiment_score": 2}
    ]

    result = generate_schedule([], ai_journals, [], [])

    # Mood uses time-weighted average so recent entries count more
    # Should be lower than simple average (4.0) since recent scores are lower
    assert result["mood_score"] < 4.0
    assert result["mood_score"] > 0

    # Trend should be negative since mood is declining
    assert result["trend_score"] < 0


### WEAK MODULE DETECTION ###

# One Comprehensive Test
def test_weak_module_detection():
    quiz_results = [
        {"file_name": "Module 1 File 1", "score": 5, "total_questions": 10, "created_at": "2026-04-01T00:00:00", "documents": {"module": "Module 1"}},
        {"file_name": "Module 1 File 1", "score": 10, "total_questions": 10, "created_at": "2026-04-02T00:00:00", "documents": {"module": "Module 1"}},
        {"file_name": "Module 1 File 1", "score": 10, "total_questions": 10, "created_at": "2026-04-03T00:00:00", "documents": {"module": "Module 1"}},
        {"file_name": "Module 1 File 2", "score": 10, "total_questions": 10, "created_at": "2026-04-01T00:00:00", "documents": {"module": "Module 1"}},
        {"file_name": "Module 1 File 2", "score": 5, "total_questions": 10, "created_at": "2026-04-02T00:00:00", "documents": {"module": "Module 1"}},
        {"file_name": "Module 1 File 2", "score": 5, "total_questions": 10, "created_at": "2026-04-03T00:00:00", "documents": {"module": "Module 1"}},
        {"file_name": "Module 2 File 1", "score": 5, "total_questions": 10, "created_at": "2026-04-01T00:00:00", "documents": {"module": "Module 2"}},
        {"file_name": "Module 2 File 1", "score": 10, "total_questions": 10, "created_at": "2026-04-02T00:00:00", "documents": {"module": "Module 2"}},
        {"file_name": "Module 2 File 1", "score": 10, "total_questions": 10, "created_at": "2026-04-03T00:00:00", "documents": {"module": "Module 2"}},
        {"file_name": "Module 2 File 2", "score": 5, "total_questions": 10, "created_at": "2026-04-01T00:00:00", "documents": {"module": "Module 2"}},
        {"file_name": "Module 2 File 2", "score": 10, "total_questions": 10, "created_at": "2026-04-02T00:00:00", "documents": {"module": "Module 2"}},
        {"file_name": "Module 2 File 2", "score": 10, "total_questions": 10, "created_at": "2026-04-03T00:00:00", "documents": {"module": "Module 2"}}
    ]

    result = generate_schedule([], [], [], quiz_results)
    
	# Expected results:

	# Module 1
	# File 1	5/10	10/10	10/10
	# File 2	10/10	5/10	5/10
	# Average = 7.5 (not weak)

	# Module 2
	# File 1	5/10	10/10	10/10
	# File 2	5/10	10/10	10/10
	# Average = 5 (weak)

    assert "Module 2" in result["weak_modules"]
    assert "Module 1" not in result["weak_modules"]


### NO OVERLAPS (WITHOUT TIMETABLE) ###

# One Comprehensive Test
def test_no_overlaps_without_timetable():
    today = datetime.today().date()
    due_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")

    tasks = [
        {"name": "Task A", "due_date": due_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task B", "due_date": due_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task C", "due_date": due_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task D", "due_date": due_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task E", "due_date": due_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task F", "due_date": due_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task G", "due_date": due_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task H", "due_date": due_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "60"}
    ]

    result = generate_schedule(tasks, [], [], [])

    scheduled_entries = result["scheduled_entries"]
    
    valid = True
    for x in range(len(scheduled_entries)):
        for y in range(x + 1, len(scheduled_entries)):
            current_entry = scheduled_entries[x]
            next_entry = scheduled_entries[y]
            if current_entry["date"] == next_entry["date"]:
                if ((next_entry["start_time"] >= current_entry["start_time"]) and (next_entry["start_time"] < current_entry["end_time"])):
                    valid = False
                    
    assert valid


### NO OVERLAPS (WITH TIMETABLE) ###

# Shorter Tasks + Deadlines Spread Out
def test_no_overlaps_with_timetable_1():
    today_date = datetime.today().date()
    due_date = (today_date + timedelta(days=7)).strftime("%Y-%m-%d")

    tasks = [
        {"name": "Task A", "due_date": due_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task B", "due_date": due_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task C", "due_date": due_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task D", "due_date": due_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task E", "due_date": due_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task F", "due_date": due_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "60"},
        {"name": "Task G", "due_date": due_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "60"},
        {"name": "Task H", "due_date": due_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "60"}
    ]

    timetable_entries = [
        {"title": "Lecture 1", "module": "Fake Module 1", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=1)).strftime("%Y-%m-%d"), "start_time": "12:00:00", "end_time": "14:00:00"},
        {"title": "Lecture 2", "module": "Fake Module 2", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=1)).strftime("%Y-%m-%d"), "start_time": "14:00:00", "end_time": "16:00:00"},
        {"title": "Lecture 3", "module": "Fake Module 3", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=2)).strftime("%Y-%m-%d"), "start_time": "15:00:00", "end_time": "17:00:00"},
        {"title": "Lecture 4", "module": "Fake Module 4", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=3)).strftime("%Y-%m-%d"), "start_time": "09:00:00", "end_time": "11:00:00"},
        {"title": "Lecture 5", "module": "Fake Module 5", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=3)).strftime("%Y-%m-%d"), "start_time": "13:00:00", "end_time": "15:00:00"}
    ]

    result = generate_schedule(tasks, [], timetable_entries, [])

    scheduled_entries = result["scheduled_entries"]
    
    all_entries = scheduled_entries + timetable_entries

    valid = True
    for x in range(len(all_entries)):
        for y in range(x + 1, len(all_entries)):
            current_entry = all_entries[x]
            next_entry = all_entries[y]
            if current_entry["date"] == next_entry["date"]:
                if ((next_entry["start_time"] >= current_entry["start_time"]) and (next_entry["start_time"] < current_entry["end_time"])):
                    valid = False
                    
    assert valid

# Longer Tasks + Deadlines Not Spread Out
def test_no_overlaps_with_timetable_2():
    today_date = datetime.today().date()
    due_date = (today_date + timedelta(days=2)).strftime("%Y-%m-%d")

    tasks = [
        {"name": "Task A", "due_date": due_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "120"},
        {"name": "Task B", "due_date": due_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "120"},
        {"name": "Task C", "due_date": due_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "120"},
        {"name": "Task D", "due_date": due_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "120"},
        {"name": "Task E", "due_date": due_date, "priority": "Low", "status": "Incomplete - Not Started", "estimated_duration": "120"},
        {"name": "Task F", "due_date": due_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "120"},
        {"name": "Task G", "due_date": due_date, "priority": "Low", "status": "Incomplete - In Progress", "estimated_duration": "120"},
        {"name": "Task H", "due_date": due_date, "priority": "High", "status": "Incomplete - In Progress", "estimated_duration": "120"}
    ]

    timetable_entries = [
        {"title": "Lecture 1", "module": "Fake Module 1", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=1)).strftime("%Y-%m-%d"), "start_time": "12:00:00", "end_time": "14:00:00"},
        {"title": "Lecture 2", "module": "Fake Module 2", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=1)).strftime("%Y-%m-%d"), "start_time": "14:00:00", "end_time": "16:00:00"},
        {"title": "Lecture 3", "module": "Fake Module 3", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=2)).strftime("%Y-%m-%d"), "start_time": "09:00:00", "end_time": "11:00:00"},
        {"title": "Lecture 4", "module": "Fake Module 4", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=2)).strftime("%Y-%m-%d"), "start_time": "13:00:00", "end_time": "15:00:00"},
        {"title": "Lecture 5", "module": "Fake Module 5", "type": "Lecture", "location": "Fake Location", "date": (today_date + timedelta(days=2)).strftime("%Y-%m-%d"), "start_time": "15:00:00", "end_time": "17:00:00"}
    ]

    result = generate_schedule(tasks, [], timetable_entries, [])

    scheduled_entries = result["scheduled_entries"]
    
    all_entries = scheduled_entries + timetable_entries

    valid = True
    for x in range(len(all_entries)):
        for y in range(x + 1, len(all_entries)):
            current_entry = all_entries[x]
            next_entry = all_entries[y]
            if current_entry["date"] == next_entry["date"]:
                if ((next_entry["start_time"] >= current_entry["start_time"]) and (next_entry["start_time"] < current_entry["end_time"])):
                    valid = False
                    
    assert valid


### TASK SESSIONS CREATED ###

# Task Sessions Created
def test_task_sessions_created_1():
    today = datetime.today().date()
    soon_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")

    tasks = [
        {"name": "Task 1", "due_date": soon_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "120"},
        {"name": "Task 2", "due_date": soon_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "120"}
    ]

    result = generate_schedule(tasks, [], [], [])

    scheduled_entries = result["scheduled_entries"]

    assert any(entry["name"] == "Task 1" for entry in scheduled_entries)
    assert any(entry["name"] == "Task 2" for entry in scheduled_entries)

# Task Sessions Not Created
def test_task_sessions_created_2():
    today = datetime.today().date()
    past_date = (today + timedelta(days=-5)).strftime("%Y-%m-%d")
    soon_date = (today + timedelta(days=5)).strftime("%Y-%m-%d")

    tasks = [
        {"name": "Task 1", "due_date": past_date, "priority": "High", "status": "Incomplete - Not Started", "estimated_duration": "120"},
        {"name": "Task 2", "due_date": soon_date, "priority": "High", "status": "Complete", "estimated_duration": "120"}
    ]

    result = generate_schedule(tasks, [], [], [])

    scheduled_entries = result["scheduled_entries"]

    assert len(scheduled_entries) == 0


### WELLBEING SESSIONS CREATED ###

# Wellbeing Sessions Created
def test_wellbeing_sessions_created_1():
    today = datetime.today().date()

    ai_journals = [
        {"date": today.strftime("%Y-%m-%d"), "sentiment_score": 3},
        {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "sentiment_score": 4},
        {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "sentiment_score": 5}
    ]

    result = generate_schedule([], ai_journals, [], [])

    scheduled_entries = result["scheduled_entries"]

    assert any(entry["category"] == "wellbeing" for entry in scheduled_entries)

# Wellbeing Sessions Not Created
def test_wellbeing_sessions_created_2():
    today = datetime.today().date()

    ai_journals = [
        {"date": today.strftime("%Y-%m-%d"), "sentiment_score": 8},
        {"date": (today + timedelta(days=1)).strftime("%Y-%m-%d"), "sentiment_score": 9},
        {"date": (today + timedelta(days=2)).strftime("%Y-%m-%d"), "sentiment_score": 10}
    ]

    result = generate_schedule([], ai_journals, [], [])

    scheduled_entries = result["scheduled_entries"]

    assert not any(entry["category"] == "wellbeing" for entry in scheduled_entries)


### STUDY SESSIONS CREATED ###

# Study Sessions Created
def test_study_sessions_created_1():
    quiz_results = [
        {"file_name": "Test Document", "score": 5, "total_questions": 10, "created_at": "2026-04-01T00:00:00", "documents": {"module": "Test Module"}},
        {"file_name": "Test Document", "score": 10, "total_questions": 10, "created_at": "2026-04-02T00:00:00", "documents": {"module": "Test Module"}}
	]

    result = generate_schedule([], [], [], quiz_results)

    scheduled_entries = result["scheduled_entries"]

    assert any(entry["category"] == "academic" for entry in scheduled_entries)

# Study Sessions Not Created
def test_study_sessions_created_2():
    quiz_results = [
        {"file_name": "Test Document", "score": 10, "total_questions": 10, "created_at": "2026-04-01T00:00:00", "documents": {"module": "Test Module"}},
        {"file_name": "Test Document", "score": 5, "total_questions": 10, "created_at": "2026-04-02T00:00:00", "documents": {"module": "Test Module"}}
	]

    result = generate_schedule([], [], [], quiz_results)

    scheduled_entries = result["scheduled_entries"]

    assert not any(entry["category"] == "academic" for entry in scheduled_entries)
