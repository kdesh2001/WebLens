from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import httpx
import os

from main import invoke_agent

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SummarizeRequest(BaseModel):
    text: str
    url: str | None = None

@app.post("/summarize")
async def summarize(req: SummarizeRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text is empty")

    try:
        summary = invoke_agent(req.text)
        return {"summary": summary}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error summarizing: {e}")

# Run with: uvicorn server:app --reload --host 0.0.0.0 --port 8000
