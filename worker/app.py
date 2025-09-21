"""
Worker Service - FastAPI application to expose repository parsing and indexing functionality.
This service provides HTTP endpoints for the backend to call for repository analysis.
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl, validator
from typing import Optional, Dict, List, Any, Union
import os
import logging
import asyncio
import time
from pathlib import Path
import tempfile
import shutil
from datetime import datetime

# Import our parsing and indexing modules
from parse_repo import (
    build_repository_graph, 
    build_repository_with_documents,
    generate_embedding_documents,
    make_document_for_node
)
from parser.utils import clone_repo
from indexer.embedder import embed_documents, MODEL_NAME, get_embedding_dimension
from indexer.qdrant_client import (
    QdrantClient, 
    create_or_recreate_collection, 
    upsert_embeddings, 
    create_node_payloads,
    get_collection_info
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="RepoCanvas Worker Service",
    description="Repository parsing and indexing service for RepoCanvas",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for tracking jobs
active_jobs = {}
job_results = {}

# Pydantic models for request validation
class ParseRequest(BaseModel):
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    branch: str = "main"
    output_path: Optional[str] = None
    
    @validator('repo_url', 'repo_path')
    def validate_repo_source(cls, v, values):
        # At least one of repo_url or repo_path must be provided
        if not v and not values.get('repo_url') and not values.get('repo_path'):
            raise ValueError('Either repo_url or repo_path must be provided')
        return v

class SearchRequest(BaseModel):
    query: str
    top_k: int = 10
    collection_name: str = "repocanvas"
    qdrant_url: Optional[str] = None

class IndexRequest(BaseModel):
    collection_name: str = "repocanvas"
    qdrant_url: Optional[str] = None
    model_name: str = MODEL_NAME
    graph_path: Optional[str] = None
    recreate_collection: bool = True

@app.post("/search")
async def search_repository(request: SearchRequest):
    """
    Semantic search for relevant nodes using Qdrant embeddings.
    
    This endpoint performs semantic search on the indexed repository data
    and returns the most relevant node IDs with scores.
    """
    try:
        # Connect to Qdrant
        qdrant_client_url = request.qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_client_url)
        
        # Check if collection exists
        try:
            collection_info = get_collection_info(client, request.collection_name)
            if not collection_info or collection_info.get('points_count', 0) == 0:
                return {
                    "success": False,
                    "error": f"Collection '{request.collection_name}' is empty or does not exist",
                    "results": [],
                    "query": request.query,
                    "total_results": 0
                }
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to access collection '{request.collection_name}': {str(e)}",
                "results": [],
                "query": request.query,
                "total_results": 0
            }
        
        # Generate embedding for the query
        from indexer.embedder import embed_documents, MODEL_NAME
        query_embedding = embed_documents([request.query], model_name=MODEL_NAME)
        
        if len(query_embedding) == 0:
            return {
                "success": False,
                "error": "Failed to generate query embedding",
                "results": [],
                "query": request.query,
                "total_results": 0
            }
        
        # Perform vector search
        search_results = client.search(
            collection_name=request.collection_name,
            query_vector=query_embedding[0].tolist(),
            limit=request.top_k,
            with_payload=True
        )
        
        # Format results as expected by backend
        results = []
        for result in search_results:
            payload = result.payload or {}
            results.append({
                "node_id": payload.get('node_id', str(result.id)),
                "score": float(result.score),
                "snippet": payload.get('snippet', '')[:200],
                "file": payload.get('file', ''),
                "start_line": payload.get('start_line', 0)
            })
        
        return {
            "success": True,
            "results": results,
            "query": request.query,
            "total_results": len(results),
            "collection_name": request.collection_name
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "query": request.query,
            "total_results": 0
        }
    collection_name: str = "repocanvas"
    qdrant_url: Optional[str] = None
    model_name: str = MODEL_NAME
    graph_path: Optional[str] = None
    recreate_collection: bool = True

class ParseAndIndexRequest(BaseModel):
    repo_url: Optional[str] = None
    repo_path: Optional[str] = None
    branch: str = "main"
    collection_name: str = "repocanvas"
    qdrant_url: Optional[str] = None
    model_name: str = MODEL_NAME
    recreate_collection: bool = True

# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "RepoCanvas Worker",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_jobs": len(active_jobs),
        "environment": {
            "qdrant_url": os.getenv("QDRANT_URL", "http://localhost:6333"),
            "model_name": MODEL_NAME
        }
    }

@app.post("/parse")
async def parse_repository(request: ParseRequest, background_tasks: BackgroundTasks):
    """
    Parse a repository and create graph.json with nodes and edges.
    
    This endpoint accepts either a Git repository URL or a local path,
    analyzes the code structure, and generates a comprehensive graph representation.
    """
    job_id = f"parse_{int(time.time())}"
    
    try:
        # Validate input
        if not request.repo_url and not request.repo_path:
            raise HTTPException(status_code=400, detail="Either repo_url or repo_path must be provided")
        
        # Start background parsing task
        background_tasks.add_task(
            _background_parse_task,
            job_id,
            request.repo_url,
            request.repo_path,
            request.branch,
            request.output_path
        )
        
        # Track the job
        active_jobs[job_id] = {
            "type": "parse",
            "status": "started",
            "start_time": datetime.now().isoformat(),
            "repo_url": request.repo_url,
            "repo_path": request.repo_path,
            "branch": request.branch
        }
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Repository parsing initiated",
            "status": "processing",
            "estimated_time": "30-120 seconds",
            "check_status_url": f"/status/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Parse request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate parsing: {str(e)}")

async def _background_parse_task(job_id: str, repo_url: str, repo_path: str, branch: str, output_path: str):
    """Background task for repository parsing"""
    start_time = time.time()
    try:
        logger.info(f"Starting parse job {job_id}")
        active_jobs[job_id]["status"] = "parsing"
        
        # Determine the repository source
        if repo_url:
            logger.info(f"Cloning repository from {repo_url}")
            temp_dir = tempfile.mkdtemp()
            try:
                repo_root = clone_repo(repo_url, temp_dir, branch=branch)
                logger.info(f"Repository cloned to {repo_root}")
            except Exception as e:
                raise Exception(f"Failed to clone repository: {str(e)}")
        else:
            repo_root = repo_path
            if not os.path.exists(repo_root):
                raise Exception(f"Repository path does not exist: {repo_root}")
        
        # Set output path
        if not output_path:
            output_path = os.path.join(repo_root, "graph.json")
        
        # Build the repository graph
        logger.info(f"Building repository graph for {repo_root}")
        nodes, edges, graph = build_repository_graph(repo_root, output_path)
        
        # Calculate statistics
        stats = {
            "files_processed": len(set(node.get('file', '') for node in nodes)),
            "functions_found": len([n for n in nodes if 'function:' in n.get('id', '')]),
            "classes_found": len([n for n in nodes if 'class:' in n.get('id', '')]),
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "graph_nodes": len(graph.nodes),
            "graph_edges": len(graph.edges)
        }
        
        # Store results
        job_results[job_id] = {
            "success": True,
            "job_id": job_id,
            "type": "parse",
            "status": "completed",
            "graph_path": output_path,
            "repo_root": repo_root,
            "nodes": len(nodes),
            "edges": len(edges),
            "stats": stats,
            "completion_time": datetime.now().isoformat(),
            # Add backend-compatible response format
            "message": "Repository parsing completed successfully",
            "processing_time": time.time() - start_time,
            "repo_url": repo_url,
            "branch": branch
        }
        
        # Clean up temporary directory if we cloned
        if repo_url and temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
        
        # Update job status
        active_jobs[job_id]["status"] = "completed"
        logger.info(f"Parse job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Parse job {job_id} failed: {e}")
        job_results[job_id] = {
            "success": False,
            "job_id": job_id,
            "type": "parse",
            "status": "failed",
            "error": str(e),
            "completion_time": datetime.now().isoformat()
        }
        active_jobs[job_id]["status"] = "failed"

@app.post("/index")
async def index_repository(request: IndexRequest, background_tasks: BackgroundTasks):
    """
    Index repository embeddings to Qdrant for semantic search.
    
    This endpoint takes parsed repository data and creates embeddings
    for all code nodes, then stores them in Qdrant for efficient retrieval.
    """
    job_id = f"index_{int(time.time())}"
    
    try:
        # Start background indexing task
        background_tasks.add_task(
            _background_index_task,
            job_id,
            request.collection_name,
            request.qdrant_url,
            request.model_name,
            request.graph_path,
            request.recreate_collection
        )
        
        # Track the job
        active_jobs[job_id] = {
            "type": "index",
            "status": "started",
            "start_time": datetime.now().isoformat(),
            "collection_name": request.collection_name,
            "model_name": request.model_name
        }
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Repository indexing initiated",
            "status": "processing",
            "collection_name": request.collection_name,
            "model_name": request.model_name,
            "estimated_time": "60-300 seconds",
            "check_status_url": f"/status/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Index request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate indexing: {str(e)}")

async def _background_index_task(job_id: str, collection_name: str, qdrant_url: str, 
                                 model_name: str, graph_path: str, recreate_collection: bool):
    """Background task for repository indexing"""
    try:
        logger.info(f"Starting index job {job_id}")
        active_jobs[job_id]["status"] = "loading_graph"
        
        # Load graph data
        if not graph_path:
            graph_path = "data/graph.json"
        
        if not os.path.exists(graph_path):
            raise Exception(f"Graph file not found: {graph_path}")
        
        import json
        with open(graph_path, 'r', encoding='utf-8') as f:
            graph_data = json.load(f)
        
        nodes = graph_data.get('nodes', [])
        if not nodes:
            raise Exception("No nodes found in graph data")
        
        logger.info(f"Loaded {len(nodes)} nodes from {graph_path}")
        
        # Generate documents for embedding
        active_jobs[job_id]["status"] = "generating_documents"
        logger.info("Generating semantic documents...")
        documents = [make_document_for_node(node) for node in nodes]
        
        # Generate embeddings
        active_jobs[job_id]["status"] = "generating_embeddings"
        logger.info(f"Generating embeddings with model: {model_name}")
        embeddings = embed_documents(documents, model_name=model_name)
        
        # Connect to Qdrant
        active_jobs[job_id]["status"] = "connecting_qdrant"
        qdrant_client_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        logger.info(f"Connecting to Qdrant at {qdrant_client_url}")
        client = QdrantClient(url=qdrant_client_url)
        
        # Create or recreate collection
        active_jobs[job_id]["status"] = "creating_collection"
        if recreate_collection:
            logger.info(f"Creating/recreating collection: {collection_name}")
            success = create_or_recreate_collection(client, collection_name, embeddings.shape[1])
            if not success:
                raise Exception(f"Failed to create collection: {collection_name}")
        
        # Prepare payloads
        active_jobs[job_id]["status"] = "preparing_payloads"
        logger.info("Preparing node payloads...")
        payloads = create_node_payloads(nodes)
        
        # Upsert embeddings
        active_jobs[job_id]["status"] = "upserting_embeddings"
        logger.info("Upserting embeddings to Qdrant...")
        mapping = upsert_embeddings(client, collection_name, embeddings, payloads)
        
        if not mapping:
            raise Exception("Failed to upsert embeddings - no mapping returned")
        
        # Get collection info
        collection_info = get_collection_info(client, collection_name)
        
        # Store results
        job_results[job_id] = {
            "success": True,
            "job_id": job_id,
            "type": "index",
            "status": "completed",
            "collection_name": collection_name,
            "model_name": model_name,
            "points_indexed": len(mapping),
            "embedding_dimension": embeddings.shape[1],
            "collection_info": collection_info,
            "completion_time": datetime.now().isoformat()
        }
        
        # Update job status
        active_jobs[job_id]["status"] = "completed"
        logger.info(f"Index job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Index job {job_id} failed: {e}")
        job_results[job_id] = {
            "success": False,
            "job_id": job_id,
            "type": "index",
            "status": "failed",
            "error": str(e),
            "completion_time": datetime.now().isoformat()
        }
        active_jobs[job_id]["status"] = "failed"

@app.post("/parse-and-index")
async def parse_and_index_repository(request: ParseAndIndexRequest, background_tasks: BackgroundTasks):
    """
    Complete pipeline: Parse repository and then index to Qdrant.
    
    This endpoint combines parsing and indexing into a single operation,
    ideal for end-to-end repository processing.
    """
    job_id = f"parse_index_{int(time.time())}"
    
    try:
        # Validate input
        if not request.repo_url and not request.repo_path:
            raise HTTPException(status_code=400, detail="Either repo_url or repo_path must be provided")
        
        # Start background task
        background_tasks.add_task(
            _background_parse_and_index_task,
            job_id,
            request.repo_url,
            request.repo_path,
            request.branch,
            request.collection_name,
            request.qdrant_url,
            request.model_name,
            request.recreate_collection
        )
        
        # Track the job
        active_jobs[job_id] = {
            "type": "parse_and_index",
            "status": "started",
            "start_time": datetime.now().isoformat(),
            "repo_url": request.repo_url,
            "repo_path": request.repo_path,
            "collection_name": request.collection_name,
            "model_name": request.model_name
        }
        
        return {
            "success": True,
            "job_id": job_id,
            "message": "Repository parsing and indexing initiated",
            "status": "processing",
            "pipeline": ["clone/load", "parse", "generate_embeddings", "index_to_qdrant"],
            "estimated_time": "120-600 seconds",
            "check_status_url": f"/status/{job_id}"
        }
        
    except Exception as e:
        logger.error(f"Parse and index request failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initiate parse and index: {str(e)}")

async def _background_parse_and_index_task(job_id: str, repo_url: str, repo_path: str, branch: str,
                                          collection_name: str, qdrant_url: str, model_name: str,
                                          recreate_collection: bool):
    """Background task for complete parse and index pipeline"""
    try:
        logger.info(f"Starting parse and index job {job_id}")
        
        # Phase 1: Repository setup
        active_jobs[job_id]["status"] = "cloning_repository"
        
        if repo_url:
            logger.info(f"Cloning repository from {repo_url}")
            temp_dir = tempfile.mkdtemp()
            try:
                repo_root = clone_repo(repo_url, temp_dir, branch=branch)
                logger.info(f"Repository cloned to {repo_root}")
            except Exception as e:
                raise Exception(f"Failed to clone repository: {str(e)}")
        else:
            repo_root = repo_path
            if not os.path.exists(repo_root):
                raise Exception(f"Repository path does not exist: {repo_root}")
        
        # Phase 2: Parsing
        active_jobs[job_id]["status"] = "parsing_repository"
        logger.info(f"Building repository graph for {repo_root}")
        
        output_path = os.path.join(repo_root, "graph.json")
        results = build_repository_with_documents(
            repo_root=repo_root,
            output_path=output_path,
            documents_dir=os.path.join(repo_root, "data", "documents")
        )
        
        nodes = results['nodes']
        edges = results['edges']
        documents = results['documents']
        
        # Phase 3: Generate embeddings
        active_jobs[job_id]["status"] = "generating_embeddings"
        logger.info(f"Generating embeddings with model: {model_name}")
        embeddings = embed_documents(documents, model_name=model_name)
        
        # Phase 4: Index to Qdrant
        active_jobs[job_id]["status"] = "indexing_to_qdrant"
        qdrant_client_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        logger.info(f"Connecting to Qdrant at {qdrant_client_url}")
        client = QdrantClient(url=qdrant_client_url)
        
        # Create collection
        if recreate_collection:
            logger.info(f"Creating/recreating collection: {collection_name}")
            success = create_or_recreate_collection(client, collection_name, embeddings.shape[1])
            if not success:
                raise Exception(f"Failed to create collection: {collection_name}")
        
        # Prepare and upsert
        payloads = create_node_payloads(nodes)
        mapping = upsert_embeddings(client, collection_name, embeddings, payloads)
        
        if not mapping:
            raise Exception("Failed to upsert embeddings")
        
        # Calculate final statistics
        parse_stats = results['analysis_summary']
        collection_info = get_collection_info(client, collection_name)
        
        # Store comprehensive results
        job_results[job_id] = {
            "success": True,
            "job_id": job_id,
            "type": "parse_and_index",
            "status": "completed",
            "repo_root": repo_root,
            "graph_path": output_path,
            "collection_name": collection_name,
            "model_name": model_name,
            "parse_stats": parse_stats,
            "index_stats": {
                "points_indexed": len(mapping),
                "embedding_dimension": embeddings.shape[1],
                "collection_info": collection_info
            },
            "completion_time": datetime.now().isoformat()
        }
        
        # Clean up
        if repo_url and temp_dir:
            try:
                shutil.rmtree(temp_dir)
            except Exception as e:
                logger.warning(f"Failed to clean up temp directory: {e}")
        
        active_jobs[job_id]["status"] = "completed"
        logger.info(f"Parse and index job {job_id} completed successfully")
        
    except Exception as e:
        logger.error(f"Parse and index job {job_id} failed: {e}")
        job_results[job_id] = {
            "success": False,
            "job_id": job_id,
            "type": "parse_and_index",
            "status": "failed",
            "error": str(e),
            "completion_time": datetime.now().isoformat()
        }
        active_jobs[job_id]["status"] = "failed"

@app.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get the status of a background job"""
    
    # Check if job exists in active jobs
    if job_id in active_jobs:
        job_info = active_jobs[job_id].copy()
        
        # Add results if completed
        if job_id in job_results:
            job_info.update(job_results[job_id])
        
        return job_info
    
    # Check if job exists in results only
    if job_id in job_results:
        return job_results[job_id]
    
    # Job not found
    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

@app.get("/jobs")
async def list_jobs():
    """List all jobs (active and completed)"""
    all_jobs = {}
    
    # Add active jobs
    for job_id, job_info in active_jobs.items():
        all_jobs[job_id] = job_info.copy()
        
        # Add results if available
        if job_id in job_results:
            all_jobs[job_id].update(job_results[job_id])
    
    # Add completed jobs not in active
    for job_id, result in job_results.items():
        if job_id not in all_jobs:
            all_jobs[job_id] = result
    
    return {
        "total_jobs": len(all_jobs),
        "active_jobs": len([j for j in all_jobs.values() if j.get('status') in ['started', 'processing']]),
        "completed_jobs": len([j for j in all_jobs.values() if j.get('status') == 'completed']),
        "failed_jobs": len([j for j in all_jobs.values() if j.get('status') == 'failed']),
        "jobs": all_jobs
    }

@app.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job (if possible) and remove from tracking"""
    
    if job_id not in active_jobs and job_id not in job_results:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    # Remove from tracking
    if job_id in active_jobs:
        del active_jobs[job_id]
    if job_id in job_results:
        del job_results[job_id]
    
    return {
        "success": True,
        "message": f"Job {job_id} removed from tracking",
        "job_id": job_id
    }

class AnalyzeRequest(BaseModel):
    query: str
    top_k: int = 10
    collection_name: str = "repocanvas"
    qdrant_url: Optional[str] = None
    include_full_graph: bool = False

@app.post("/analyze")
async def analyze_query(request: AnalyzeRequest):
    """
    Full analysis: embeds query, finds subgraph, returns path + snippets + summary.
    
    This endpoint performs the complete analysis pipeline:
    1. Semantic search to find relevant nodes
    2. Build subgraph connecting relevant nodes
    3. Extract code snippets for the path
    4. Return structured analysis results
    """
    start_time = time.time()
    
    try:
        # Step 1: Perform semantic search
        search_request = SearchRequest(
            query=request.query,
            top_k=request.top_k,
            collection_name=request.collection_name,
            qdrant_url=request.qdrant_url
        )
        
        search_response = await search_repository(search_request)
        
        if not search_response.get("success", False):
            return {
                "success": False,
                "error": f"Search failed: {search_response.get('error', 'Unknown error')}",
                "answer_path": [],
                "path_edges": [],
                "snippets": [],
                "summary": None,
                "processing_time": time.time() - start_time
            }
        
        search_results = search_response.get("results", [])
        
        if not search_results:
            return {
                "success": True,
                "answer_path": [],
                "path_edges": [],
                "snippets": [],
                "summary": {
                    "one_liner": f"No relevant code found for query: {request.query}",
                    "steps": [],
                    "inputs_outputs": [],
                    "caveats": ["No matching code components found"],
                    "node_refs": []
                },
                "query": request.query,
                "processing_time": time.time() - start_time
            }
        
        # Step 2: Extract node IDs and compute paths
        node_ids = [result["node_id"] for result in search_results]
        answer_path, path_edges = _compute_answer_path(node_ids)
        
        # Step 3: Get code snippets for path nodes
        snippets = await _get_code_snippets_from_qdrant(
            answer_path, 
            request.collection_name,
            request.qdrant_url
        )
        
        # Step 4: Generate summary
        summary = _generate_analysis_summary(snippets, request.query, search_results)
        
        return {
            "success": True,
            "answer_path": answer_path,
            "path_edges": path_edges,
            "snippets": snippets,
            "summary": summary,
            "query": request.query,
            "total_results": len(search_results),
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "answer_path": [],
            "path_edges": [],
            "snippets": [],
            "summary": None,
            "query": request.query,
            "processing_time": time.time() - start_time
        }

def _compute_answer_path(node_ids: List[str]) -> tuple:
    """
    Compute optimal path through relevant nodes using simple connection logic.
    Since we don't have NetworkX graph in worker, return nodes in relevance order.
    """
    if not node_ids:
        return [], []
    
    # For now, return nodes in order of relevance
    # In a full implementation, this would use graph analysis
    answer_path = node_ids
    
    # Create simple sequential edges between nodes
    path_edges = []
    for i in range(len(node_ids) - 1):
        path_edges.append({
            "source": node_ids[i],
            "target": node_ids[i + 1],
            "type": "connection"
        })
    
    return answer_path, path_edges

async def _get_code_snippets_from_qdrant(node_ids: List[str], collection_name: str, qdrant_url: str) -> List[Dict]:
    """Get code snippets for given node IDs from Qdrant"""
    snippets = []
    
    try:
        # Connect to Qdrant
        qdrant_client_url = qdrant_url or os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_client_url)
        
        # Get points by scrolling and filtering
        for node_id in node_ids:
            try:
                # Scroll through collection to find matching node_id
                all_points, _ = client.scroll(
                    collection_name=collection_name,
                    limit=100,
                    with_payload=True,
                    scroll_filter={"must": [{"key": "node_id", "match": {"value": node_id}}]}
                )
                
                for point in all_points:
                    payload = point.payload or {}
                    if payload.get('node_id') == node_id:
                        snippets.append({
                            "node_id": node_id,
                            "code": payload.get('snippet', ''),
                            "file": payload.get('file', ''),
                            "start_line": payload.get('start_line', 0),
                            "end_line": payload.get('end_line', 0),
                            "doc": payload.get('doc', '')
                        })
                        break
                        
            except Exception as e:
                logger.warning(f"Failed to get snippet for node {node_id}: {e}")
                # Add placeholder snippet
                snippets.append({
                    "node_id": node_id,
                    "code": "# Code snippet not available",
                    "file": "unknown",
                    "start_line": 0,
                    "end_line": 0,
                    "doc": ""
                })
    
    except Exception as e:
        logger.error(f"Failed to get code snippets: {e}")
        # Return placeholder snippets
        for node_id in node_ids:
            snippets.append({
                "node_id": node_id,
                "code": "# Code snippet not available",
                "file": "unknown",
                "start_line": 0,
                "end_line": 0,
                "doc": "Error retrieving code snippet"
            })
    
    return snippets

def _generate_analysis_summary(snippets: List[Dict], query: str, search_results: List[Dict]) -> Dict:
    """Generate analysis summary from code snippets"""
    
    # Extract key information
    files_involved = list(set(snippet.get('file', 'unknown') for snippet in snippets))
    total_snippets = len(snippets)
    
    # Generate one-liner summary
    one_liner = f"Analysis of {total_snippets} code components across {len(files_involved)} files related to: {query}"
    
    # Generate steps
    steps = []
    for i, snippet in enumerate(snippets[:5]):  # Limit to first 5
        node_name = snippet.get('node_id', '').split(':')[0] if ':' in snippet.get('node_id', '') else 'Component'
        file_name = snippet.get('file', 'unknown')
        steps.append(f"{i+1}. {node_name} in {file_name}: {snippet.get('doc', 'Code execution')[:50]}")
    
    # Generate inputs/outputs
    inputs_outputs = [
        f"Input: User query - '{query}'",
        f"Output: Analysis of {total_snippets} relevant code components",
        f"Files analyzed: {', '.join(files_involved[:3])}" + ("..." if len(files_involved) > 3 else "")
    ]
    
    # Generate caveats
    caveats = [
        "Analysis based on static code structure and semantic similarity",
        "Results limited to indexed code components",
        f"Search performed on top {len(search_results)} matches"
    ]
    
    # Generate node references
    node_refs = []
    for snippet in snippets[:3]:  # Limit to first 3
        code_lines = snippet.get('code', '').split('\n')
        excerpt = code_lines[0][:50] + "..." if code_lines and len(code_lines[0]) > 50 else (code_lines[0] if code_lines else "")
        node_refs.append({
            "node_id": snippet.get('node_id', ''),
            "excerpt_line": excerpt
        })
    
    return {
        "one_liner": one_liner,
        "steps": steps,
        "inputs_outputs": inputs_outputs,
        "caveats": caveats,
        "node_refs": node_refs
    }
async def list_qdrant_collections():
    """List available Qdrant collections"""
    try:
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        client = QdrantClient(url=qdrant_url)
        
        collections = client.get_collections()
        collection_details = []
        
        for collection in collections.collections:
            try:
                info = get_collection_info(client, collection.name)
                collection_details.append(info)
            except Exception as e:
                collection_details.append({
                    "name": collection.name,
                    "error": str(e)
                })
        
        return {
            "qdrant_url": qdrant_url,
            "total_collections": len(collection_details),
            "collections": collection_details
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect to Qdrant: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("WORKER_HOST", "0.0.0.0")
    port = int(os.getenv("WORKER_PORT", "8002"))
    
    logger.info(f"Starting Worker Service on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
