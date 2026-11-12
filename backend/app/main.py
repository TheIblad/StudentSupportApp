from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import tasks, journals, documents, ai

app = FastAPI()

# Allow frontend requests from any domain (local or Vercel)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks.router)
app.include_router(journals.router)
app.include_router(documents.router)
app.include_router(ai.router)

@app.get("/")
def root():
    return {"status": "API running"}