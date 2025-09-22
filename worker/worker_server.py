#!/usr/bin/env python3
"""
Worker service for RepoCanvas
Provides HTTP endpoints for repository parsing, analysis, and Qdrant integration
"""

import os
import json
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(title="RepoCanvas Worker", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global storage for job status
job_status: Dict[str, Dict[str, Any]] = {}

# Pydantic models
class ParseRequest(BaseModel):
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    branch: str = "main"
    output_path: Optional[str] = None

class ParseAndIndexRequest(BaseModel):
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    branch: str = "main"
    collection_name: str = "repocanvas"
    qdrant_url: str = "http://localhost:6333"
    recreate_collection: bool = True

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    collection_name: str = "repocanvas"
    qdrant_url: str = "http://localhost:6333"

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RepoCanvas Worker is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "worker"}

@app.post("/parse")
async def parse_repository(request: ParseRequest, background_tasks: BackgroundTasks):
    """Parse repository and generate graph.json"""
    job_id = f"parse_{len(job_status) + 1}"
    
    # Initialize job status
    job_status[job_id] = {
        "status": "started",
        "message": "Starting repository parsing...",
        "progress": 0
    }
    
    # Add background task
    background_tasks.add_task(run_parse_task, job_id, request)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Parsing job started",
        "status_url": f"/status/{job_id}"
    }

@app.post("/parse-and-index")
async def parse_and_index_repository(request: ParseAndIndexRequest, background_tasks: BackgroundTasks):
    """Parse repository and index to Qdrant"""
    job_id = f"parse_index_{len(job_status) + 1}"
    
    # Initialize job status
    job_status[job_id] = {
        "status": "started",
        "message": "Starting repository parsing and indexing...",
        "progress": 0
    }
    
    # Add background task
    background_tasks.add_task(run_parse_and_index_task, job_id, request)
    
    return {
        "success": True,
        "job_id": job_id,
        "message": "Parsing and indexing job started",
        "status_url": f"/status/{job_id}"
    }

@app.post("/search")
async def search_embeddings(request: SearchRequest):
    """Search for similar code using Qdrant embeddings"""
    try:
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        
        # Initialize clients
        client = QdrantClient(url=request.qdrant_url)
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Generate query embedding
        query_vector = model.encode([request.query])[0].tolist()
        
        # Search in Qdrant
        search_results = client.search(
            collection_name=request.collection_name,
            query_vector=query_vector,
            limit=request.top_k,
            with_payload=True
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append({
                "node_id": result.payload.get("node_id", ""),
                "file": result.payload.get("file", ""),
                "function": result.payload.get("function", ""),
                "code": result.payload.get("code", ""),
                "score": float(result.score),
                "line": result.payload.get("line", 0)
            })
        
        return {
            "success": True,
            "results": results,
            "query": request.query,
            "total_results": len(results)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status"""
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return job_status[job_id]

@app.get("/jobs")
async def list_jobs():
    """List all jobs"""
    return {
        "jobs": [
            {"job_id": job_id, **status}
            for job_id, status in job_status.items()
        ]
    }

async def run_parse_task(job_id: str, request: ParseRequest):
    """Run parsing task in background"""
    try:
        job_status[job_id]["status"] = "running"
        job_status[job_id]["message"] = "Parsing repository..."
        job_status[job_id]["progress"] = 25
        
        # Build command
        cmd = ["python", "parse_repo.py"]
        
        if request.repo_url:
            cmd.extend(["--repo", request.repo_url])
        elif request.repo_path:
            cmd.extend(["--repo", request.repo_path])
        else:
            raise ValueError("Either repo_url or repo_path is required")
        
        if request.output_path:
            cmd.extend(["--out", request.output_path])
        
        cmd.append("--verbose")
        
        # Run command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["message"] = "Repository parsed successfully"
            job_status[job_id]["progress"] = 100
            job_status[job_id]["result"] = {
                "output": result.stdout,
                "graph_file": request.output_path or "data/graph.json"
            }
        else:
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["message"] = f"Parsing failed: {result.stderr}"
            job_status[job_id]["error"] = result.stderr
            
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = f"Parsing failed: {str(e)}"
        job_status[job_id]["error"] = str(e)

async def run_parse_and_index_task(job_id: str, request: ParseAndIndexRequest):
    """Run parsing and indexing task in background"""
    try:
        job_status[job_id]["status"] = "running"
        job_status[job_id]["message"] = "Parsing and indexing repository..."
        job_status[job_id]["progress"] = 25
        
        # Build command
        cmd = ["python", "parse_repo.py"]
        
        if request.repo_url:
            cmd.extend(["--repo", request.repo_url])
        elif request.repo_path:
            cmd.extend(["--repo", request.repo_path])
        else:
            raise ValueError("Either repo_url or repo_path is required")
        
        cmd.extend([
            "--index",
            "--collection", request.collection_name,
            "--qdrant-url", request.qdrant_url,
            "--verbose"
        ])
        
        # Run command
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            job_status[job_id]["status"] = "completed"
            job_status[job_id]["message"] = "Repository parsed and indexed successfully"
            job_status[job_id]["progress"] = 100
            job_status[job_id]["result"] = {
                "output": result.stdout,
                "collection": request.collection_name
            }
        else:
            job_status[job_id]["status"] = "failed"
            job_status[job_id]["message"] = f"Parsing and indexing failed: {result.stderr}"
            job_status[job_id]["error"] = result.stderr
            
    except Exception as e:
        job_status[job_id]["status"] = "failed"
        job_status[job_id]["message"] = f"Parsing and indexing failed: {str(e)}"
        job_status[job_id]["error"] = str(e)

if __name__ == "__main__":
    port = int(os.getenv("WORKER_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")