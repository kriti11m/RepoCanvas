from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict
from service import summarize
from schema import SummaryResponse

app = FastAPI(title="RepoCanvas AI Summarizer", version="1.0.0")

# Request model for the endpoint
class SummarizeRequest(BaseModel):
    question: str
    snippets: List[Dict[str, str]]  # Each snippet has node_id and code

@app.get("/")
def root():
    return {"message": "RepoCanvas AI Summarizer Service", "status": "running"}

@app.get("/health")
def health():
    return {"status": "healthy", "service": "ai-summarizer"}

@app.post("/summarize", response_model=SummaryResponse)
def summarize_endpoint(request: SummarizeRequest):
    try:
        print(f"Received request: {request.question}")
        print(f"Number of snippets: {len(request.snippets)}")
        
        result = summarize(request.question, request.snippets)
        return result
        
    except Exception as e:
        print(f"Error in summarize_endpoint: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Summarization failed: {str(e)}"
        )