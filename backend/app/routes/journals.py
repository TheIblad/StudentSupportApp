from fastapi import APIRouter, HTTPException
from app.database import supabase

router = APIRouter()

@router.get("/journals")
def get_journals(user_id: str):
    response = supabase.table("journals").select("*").eq("user_id", user_id).order("date", desc=True).execute()
    return response.data

@router.post("/journals")
def create_journal(journal: dict):
    if "user_id" not in journal:
        raise HTTPException(status_code=400, detail="Missing user_id")
        
    response = supabase.table("journals").insert(journal).execute()
    return response.data[0]

@router.put("/journals/{id}")
def update_journal(id: int, journal: dict):
    response = supabase.table("journals").update(journal).eq("id", id).execute()
    return response.data[0]

@router.delete("/journals/{id}")
def delete_journal(id: int):
    supabase.table("journals").delete().eq("id", id).execute()
    return {"message": "Journal deleted"}

@router.get("/journals/date/{date}")
def get_journal_by_date(date: str, user_id: str): # Require user_id here too
    response = supabase.table("journals").select("*").eq("date", date).eq("user_id", user_id).execute()
    if response.data:
        return response.data[0]
    return None