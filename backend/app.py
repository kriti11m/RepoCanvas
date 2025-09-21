from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import time
from typing import Dict, List, Any

from schemas import (
    GraphResponse, SearchRequest, SearchResponse, 
    SummarizeRequest, SummarizeResponse, AnswerRequest, AnswerResponse
)

app = FastAPI(title="RepoCanvas Backend", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for graph data
graph_data = None

@app.on_event("startup")
async def startup_event():
    """Load graph data on startup"""
    global graph_data
    
    # Load graph data
    graph_path = "data/graph.json"
    if os.path.exists(graph_path):
        try:
            with open(graph_path, 'r') as f:
                graph_data = json.load(f)
            print(f"Loaded graph with {len(graph_data.get('nodes', []))} nodes")
        except Exception as e:
            print(f"Failed to load graph: {e}")
            graph_data = {"nodes": [], "edges": []}
    else:
        print("Graph file not found, using empty graph")
        graph_data = {"nodes": [], "edges": []}

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RepoCanvas Backend API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": int(time.time()),
        "services": {
            "graph": graph_data is not None,
            "search": True,
            "summarizer": True
        }
    }

@app.get("/graph", response_model=GraphResponse)
async def get_graph():
    """Get the repository dependency graph"""
    if graph_data is None:
        return GraphResponse(nodes=[], edges=[])
    
    return GraphResponse(
        nodes=graph_data.get("nodes", []),
        edges=graph_data.get("edges", [])
    )

@app.post("/search", response_model=SearchResponse)
async def search_code(request: SearchRequest):
    """Search for code snippets using semantic similarity"""
    # Mock response for initial commit
    mock_results = [
        {
            "file_path": "src/components/Button.tsx",
            "content": "export const Button = ({ onClick, children }) => {\n  return <button onClick={onClick}>{children}</button>;\n};",
            "score": 0.95,
            "line_start": 1,
            "line_end": 3
        },
        {
            "file_path": "src/utils/helpers.py",
            "content": "def format_date(date):\n    return date.strftime('%Y-%m-%d')",
            "score": 0.87,
            "line_start": 15,
            "line_end": 16
        }
    ]
    
    return SearchResponse(
        query=request.query,
        results=mock_results,
        total_results=len(mock_results)
    )

@app.post("/answer", response_model=AnswerResponse)
async def get_answer(request: AnswerRequest):
    """Get an answer with dependency path analysis"""
    # Mock response for initial commit
    mock_path = ["component_a.py", "utils.py", "component_b.py"]
    
    return AnswerResponse(
        question=request.question,
        answer="This is a mock answer showing how components are connected through the dependency graph.",
        dependency_path=mock_path,
        related_files=["related_file_1.py", "related_file_2.py"],
        confidence_score=0.85
    )

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize_code(request: SummarizeRequest):
    """Summarize code or documentation"""
    # Mock response for initial commit
    mock_summary = f"This code appears to implement functionality related to '{request.content[:50]}...'. The main components include data processing and user interface elements."
    
    return SummarizeResponse(
        content=request.content,
        summary=mock_summary,
        key_points=[
            "Implements core business logic",
            "Handles user input validation", 
            "Integrates with external APIs",
            "Provides error handling"
        ],
        word_count=len(request.content.split())
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)