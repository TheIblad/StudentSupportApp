from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.database import supabase
from typing import List, Dict
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re

router = APIRouter()

@router.get("/tasks")
def get_tasks(user_id: str): # Require user_id
    # Filter by user_id
    response = supabase.table("tasks").select("*").eq("user_id", user_id).order("id", desc=False).execute()
    return response.data

@router.delete("/tasks/{id}")
def delete_task(id: int):
    response = supabase.table("tasks").delete().eq("id", id).execute()
    if response.data is None or response.data == []: 
        raise HTTPException(status_code=404, detail="Task Not Found")
    return response.data

@router.post("/tasks")
def post_task(addedTask: dict):
    if "user_id" not in addedTask:
        raise HTTPException(status_code=400, detail="Missing user_id")

    response = supabase.table("tasks").insert({
        "user_id": addedTask["user_id"],
        "name": addedTask["name"],
        "description": addedTask["description"],
        "due_date": addedTask["due_date"],
        "priority": addedTask["priority"],
        "module": addedTask.get("module", ""),
        "estimated_duration": int(addedTask.get("estimated_duration", 0))
    }).execute()

    if response.data is None or response.data == []: 
        raise HTTPException(status_code=400, detail="Task Not Added")
    return response.data[0]

@router.put("/tasks/{id}")
def put_task(id: int, changedTask: dict):
    response = supabase.table("tasks").update({
        "name": changedTask["name"],
        "description": changedTask["description"],
        "due_date": changedTask["due_date"],
        "priority": changedTask["priority"],
        "status": changedTask["status"],
        "module": changedTask.get("module", ""),
        "estimated_duration": int(changedTask.get("estimated_duration", 0))
    }).eq("id", id).execute()

    if response.data is None or response.data == []: 
        raise HTTPException(status_code=400, detail="Task Not Found")
    return response.data[0]

@router.post("/timetable")
def post_timetable(entries: List[Dict]):

    response = supabase.table("timetable_entries").insert(entries).execute()

    if response.data is None or response.data == []:
        raise HTTPException(status_code=400, detail="Timetable entries not added")

    return response.data

@router.get("/timetable")
def get_timetable(user_id: str):
    response = supabase.table("timetable_entries") \
        .select("*") \
        .eq("user_id", user_id) \
        .order("date", desc=False) \
        .execute()
    return response.data

@router.delete("/timetable/{id}")
def delete_timetable_entry(id: int):
    response = supabase.table("timetable_entries").delete().eq("id", id).execute()

    if response.data is None or response.data == []:
        raise HTTPException(status_code=404, detail="Timetable entry not found")

    return response.data

@router.post("/timetable/upload")
async def upload_timetable(file: UploadFile = File(...), user_id: str = Form(...)):
    content = await file.read()
    html = content.decode("utf-8")

    soup = BeautifulSoup(html, "html.parser")

    entries = []

    base_time = datetime.strptime("08:00", "%H:%M")

    day_map = {
        "Mon": 0, "Tue": 1, "Wed": 2,
        "Thu": 3, "Fri": 4
    }

    def parse_weeks(weeks_text):
        weeks = []
        parts = [p.strip() for p in weeks_text.split(",")]

        for part in parts:
            if "-" in part:
                start, end = part.split("-")
                weeks.extend(range(int(start), int(end) + 1))
            else:
                if part:
                    weeks.append(int(part))
        return weeks

    def extract_constraint_weeks(title):
        match = re.search(r"<([^>]+)>", title)
        if not match:
            return None

        constraint_text = match.group(1)
        return parse_weeks(constraint_text)

    def clean_title(title):
        return re.sub(r"<[^>]+>", "", title).strip()

    sections = soup.find_all("table", class_="header-border-args")

    for section in sections:

        weeks_span = section.find("span", class_="header-1-2-1")
        date_span = section.find("span", class_="header-1-2-3")

        if not weeks_span or not date_span:
            continue

        weeks_text = weeks_span.text.strip()
        date_text = date_span.text.strip()

        start_date_str = date_text.split("-")[0].strip()
        try:
            term_start_date = datetime.strptime(start_date_str, "%d %b %Y")
        except:
            continue

        section_weeks = parse_weeks(weeks_text)
        first_week_number = min(section_weeks)

        grid = section.find_next("table", class_="grid-border-args")
        if not grid:
            continue

        rows = grid.find_all("tr")

        for row in rows:
            day_cell = row.find("td", class_="row-label-one")
            if not day_cell:
                continue

            day_name = day_cell.text.strip()

            if day_name not in day_map:
                continue

            cells = row.find_all("td")
            col_index = 0

            for cell in cells:
                cell_class = cell.get("class", [])

                if "cell-border" in cell_class:
                    col_index += 1
                    continue

                if not any(c in ["Lecture", "Lab", "Optional/Drop-in"] for c in cell_class):
                    continue

                colspan = int(cell.get("colspan", 1))

                start_time = base_time + timedelta(minutes=30 * col_index)
                end_time = start_time + timedelta(minutes=30 * colspan)

                text_blocks = cell.find_all("table")

                title = ""
                entry_type = ""
                location = ""

                if len(text_blocks) >= 1:
                    tds = text_blocks[0].find_all("td")
                    if len(tds) >= 2:
                        title = tds[0].text.strip()
                        entry_type = tds[1].text.strip()

                if len(text_blocks) >= 2:
                    location_text = text_blocks[1].text.strip()
                    location = location_text.replace("Location:", "").strip()

                constraint_weeks = extract_constraint_weeks(title)

                if constraint_weeks is not None:
                    valid_weeks = list(set(section_weeks) & set(constraint_weeks))
                else:
                    valid_weeks = section_weeks

                clean = clean_title(title)

                for week in valid_weeks:
                    week_start = term_start_date + timedelta(weeks=(week - first_week_number))
                    current_date = week_start + timedelta(days=day_map[day_name])

                    entries.append({
                        "title": clean,
                        "module": clean.split("/")[0] if clean else "",
                        "type": entry_type,
                        "start_time": start_time.strftime("%H:%M"),
                        "end_time": end_time.strftime("%H:%M"),
                        "location": location,
                        "notes": "",
                        "date": current_date.strftime("%Y-%m-%d"),
                        "user_id": user_id
                    })

                col_index += colspan

    response = supabase.table("timetable_entries").insert(entries).execute()

    return response.data

@router.get("/schedule")
def get_schedule(user_id: str):
    return supabase.table("scheduled_entries").select("*").eq("user_id", user_id).execute().data