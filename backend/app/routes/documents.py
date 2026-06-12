import uuid
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.database import supabase

router = APIRouter()

@router.get("/documents")
def get_documents(user_id: str):
    response = supabase.table("documents").select("*").eq("user_id", user_id).order("date_uploaded", desc=True).execute()
    return response.data

@router.post("/documents")
def create_document(document: dict):
    response = supabase.table("documents").insert(document).execute()
    return response.data[0]

@router.put("/documents/{id}")
def update_document(id: int, document: dict):
    response = supabase.table("documents").update(document).eq("id", id).execute()
    return response.data[0]

@router.delete("/documents/{id}")
def delete_document(id: int):
    supabase.table("documents").delete().eq("id", id).execute()
    return {"message": "Document deleted"}

@router.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    module: str = Form(default=""),
    tags: str = Form(default=""),
    date_uploaded: str = Form(...),
    user_id: str = Form(...) # Require user_id from frontend
):
    file_bytes = await file.read()
    # Good practice: store files inside a folder named after the user_id
    storage_path = f"{user_id}/{uuid.uuid4()}_{file.filename}"

    supabase.storage.from_("documents").upload(
        storage_path,
        file_bytes,
        {"content-type": file.content_type}
    )

    file_location = supabase.storage.from_("documents").get_public_url(storage_path)

    record = {
        "user_id": user_id,
        "file_name": file.filename,
        "file_location": file_location,
        "module": module if module else None,
        "tags": tags if tags else None,
        "date_uploaded": date_uploaded
    }

    response = supabase.table("documents").insert(record).execute()
    return response.data[0]