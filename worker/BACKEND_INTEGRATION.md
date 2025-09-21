# Backend Integration Guide for Worker Service

This guide shows how to integrate the RepoCanvas backend with the Worker Service endpoints.

## Overview

The Worker Service provides the parsing and indexing functionality that the backend needs. Here's how to integrate the endpoints:

## Environment Configuration

Add these environment variables to your backend `.env`:

```bash
# Worker Service Configuration
WORKER_URL=http://localhost:8002
WORKER_TIMEOUT=300

# These should match worker settings
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=repocanvas
```

## Backend Endpoint Updates

### 1. Update the /parse Endpoint

Replace the mock implementation in `backend/app.py`:

```python
import aiohttp
import asyncio
from typing import Optional

@app.post("/parse")
async def parse_repository(request: dict):
    """Parse a repository using the Worker Service"""
    worker_url = os.getenv("WORKER_URL", "http://localhost:8002")
    timeout = int(os.getenv("WORKER_TIMEOUT", "300"))
    
    try:
        # Validate request
        repo_url = request.get("repo_url")
        repo_path = request.get("repo_path")
        
        if not repo_url and not repo_path:
            raise HTTPException(
                status_code=400, 
                detail="Either repo_url or repo_path must be provided"
            )
        
        # Prepare worker request
        worker_request = {
            "repo_url": repo_url,
            "repo_path": repo_path,
            "branch": request.get("branch", "main"),
            "output_path": request.get("output_path")
        }
        
        # Call worker service
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
            async with session.post(f"{worker_url}/parse", json=worker_request) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # For async processing, return job info
                    return {
                        "success": True,
                        "message": "Repository parsing initiated",
                        "job_id": result.get("job_id"),
                        "status": "processing",
                        "check_status_url": f"/parse/status/{result.get('job_id')}",
                        "worker_status_url": result.get("check_status_url")
                    }
                else:
                    error_detail = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Worker service error: {error_detail}"
                    )
                    
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Worker service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Parse request failed: {str(e)}"
        )

@app.get("/parse/status/{job_id}")
async def get_parse_status(job_id: str):
    """Get the status of a parsing job"""
    worker_url = os.getenv("WORKER_URL", "http://localhost:8002")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{worker_url}/status/{job_id}") as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Reload graph if parsing completed
                    if result.get("status") == "completed" and result.get("success"):
                        await reload_graph_data()
                    
                    return result
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
                else:
                    error_detail = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Worker service error: {error_detail}"
                    )
                    
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Worker service unavailable: {str(e)}"
        )

async def reload_graph_data():
    """Reload graph data after successful parsing"""
    global graph, graph_data
    
    graph_path = "./data/graph.json"
    if os.path.exists(graph_path):
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # Rebuild NetworkX graph
            graph = nx.DiGraph()
            for node in graph_data.get('nodes', []):
                graph.add_node(node['id'], **node)
            for edge in graph_data.get('edges', []):
                graph.add_edge(edge['source'], edge['target'], type=edge['type'])
            
            print(f"✅ Reloaded graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        except Exception as e:
            print(f"❌ Failed to reload graph: {e}")
```

### 2. Update the /search Endpoint

The search endpoint should work with the Qdrant collection populated by the Worker:

```python
@app.post("/search")
async def search_nodes(request: dict):
    """Enhanced search using Worker-populated Qdrant collection"""
    query = request.get("query", "")
    top_k = request.get("top_k", 10)
    start_time = time.time()
    
    # Check if we have Worker-populated data
    worker_collection = os.getenv("QDRANT_COLLECTION_NAME", "repocanvas")
    
    if not qdrant_client:
        # Fallback to basic search if Qdrant not available
        results = await _fallback_search(query, top_k)
    else:
        try:
            # Check if worker collection exists and has data
            collections = qdrant_client.get_collections()
            worker_collection_exists = any(
                col.name == worker_collection for col in collections.collections
            )
            
            if worker_collection_exists:
                collection_info = qdrant_client.get_collection(worker_collection)
                if collection_info.points_count > 0:
                    print(f"🔍 Using Worker-populated collection: {worker_collection}")
                    results = await _search_worker_collection(query, top_k, worker_collection)
                else:
                    print(f"⚠️ Worker collection {worker_collection} is empty")
                    results = await _fallback_search(query, top_k)
            else:
                print(f"⚠️ Worker collection {worker_collection} not found")
                results = await _fallback_search(query, top_k)
                
        except Exception as e:
            print(f"❌ Worker collection search failed: {e}")
            results = await _fallback_search(query, top_k)
    
    return {
        "results": results,
        "query": query,
        "total_results": len(results),
        "processing_time": time.time() - start_time,
        "source": "worker_collection" if results else "fallback"
    }

async def _search_worker_collection(query: str, top_k: int, collection_name: str) -> List[Dict]:
    """Search in Worker-populated Qdrant collection using keyword search for now"""
    try:
        # Since we don't have the embedding model in backend, use keyword search
        # The Worker team will provide vector search capabilities later
        
        # Scroll through collection and do keyword matching
        all_points, _ = qdrant_client.scroll(
            collection_name=collection_name,
            limit=200,  # Reasonable limit for keyword search
            with_payload=True
        )
        
        results = []
        query_lower = query.lower()
        
        for point in all_points:
            payload = point.payload or {}
            score = 0.0
            
            # Keyword scoring
            snippet = payload.get('snippet', '').lower()
            node_id = payload.get('node_id', '').lower()
            file_path = payload.get('file', '').lower()
            doc = payload.get('doc', '').lower()
            
            # Score based on matches
            if query_lower in snippet:
                score += 0.8
            if query_lower in doc:
                score += 0.7
            if query_lower in node_id:
                score += 0.6
            if query_lower in file_path:
                score += 0.4
            
            if score > 0:
                results.append({
                    "node_id": payload.get('node_id', str(point.id)),
                    "score": score,
                    "snippet": payload.get('snippet', '')[:200],
                    "file": payload.get('file', ''),
                    "start_line": payload.get('start_line', 0),
                    "doc": payload.get('doc', '')
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        print(f"❌ Worker collection search error: {e}")
        return []
```

### 3. Add Index Management Endpoint

Add an endpoint to trigger indexing via the Worker:

```python
@app.post("/index")
async def index_repository(request: dict):
    """Index repository to Qdrant using Worker Service"""
    worker_url = os.getenv("WORKER_URL", "http://localhost:8002")
    
    try:
        # Prepare indexing request
        index_request = {
            "collection_name": request.get("collection_name", "repocanvas"),
            "graph_path": request.get("graph_path", "./data/graph.json"),
            "model_name": request.get("model_name", "all-MiniLM-L6-v2"),
            "recreate_collection": request.get("recreate_collection", True)
        }
        
        # Call worker service
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{worker_url}/index", json=index_request) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "message": "Repository indexing initiated",
                        "job_id": result.get("job_id"),
                        "collection_name": index_request["collection_name"],
                        "check_status_url": f"/index/status/{result.get('job_id')}"
                    }
                else:
                    error_detail = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Worker service error: {error_detail}"
                    )
                    
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Worker service unavailable: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Index request failed: {str(e)}"
        )

@app.get("/index/status/{job_id}")
async def get_index_status(job_id: str):
    """Get the status of an indexing job"""
    worker_url = os.getenv("WORKER_URL", "http://localhost:8002")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{worker_url}/status/{job_id}") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
                else:
                    error_detail = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Worker service error: {error_detail}"
                    )
                    
    except aiohttp.ClientError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Worker service unavailable: {str(e)}"
        )
```

### 4. Enhanced Health Check

Update the health check to include Worker service status:

```python
@app.get("/health")
async def health_check():
    """Enhanced health check including Worker service"""
    services = {}
    
    # Check Qdrant connection
    qdrant_healthy, qdrant_message = await _check_qdrant_health()
    services["qdrant"] = qdrant_healthy
    
    # Check graph loading
    services["graph"] = graph is not None and graph_data is not None
    
    # Check Worker service
    services["worker"] = False
    worker_url = os.getenv("WORKER_URL")
    if worker_url:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{worker_url}/health") as response:
                    services["worker"] = response.status == 200
        except Exception:
            pass
    
    # Check summarizer service
    services["summarizer"] = False
    summarizer_url = os.getenv("SUMMARIZER_URL")
    if summarizer_url:
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.get(f"{summarizer_url}/health") as response:
                    services["summarizer"] = response.status == 200
        except Exception:
            pass
    
    overall_status = "healthy" if all(services.values()) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": int(time.time()),
        "services": services,
        "messages": {
            "qdrant": qdrant_message,
            "graph": "Graph loaded successfully" if services["graph"] else "No graph data available",
            "worker": "Worker service connected" if services["worker"] else "Worker service unavailable",
            "summarizer": "Summarizer connected" if services["summarizer"] else "Summarizer unavailable"
        },
        "config": {
            "qdrant_url": os.getenv("QDRANT_URL"),
            "worker_url": os.getenv("WORKER_URL"),
            "summarizer_url": os.getenv("SUMMARIZER_URL"),
            "collection_name": os.getenv("QDRANT_COLLECTION_NAME", "repocanvas")
        }
    }
```

## Usage Flow

### 1. Parse a Repository
```python
# Frontend calls backend
POST /parse
{
  "repo_url": "https://github.com/user/repo.git",
  "branch": "main"
}

# Backend calls worker
POST http://localhost:8002/parse
{
  "repo_url": "https://github.com/user/repo.git",
  "branch": "main"
}

# Returns job_id for status tracking
{
  "success": true,
  "job_id": "parse_1234567890",
  "status": "processing"
}
```

### 2. Check Parsing Status
```python
# Frontend polls backend
GET /parse/status/parse_1234567890

# Backend calls worker
GET http://localhost:8002/status/parse_1234567890

# Returns current status
{
  "status": "completed",
  "graph_path": "/path/to/graph.json",
  "stats": {...}
}
```

### 3. Index to Qdrant
```python
# After parsing completes, trigger indexing
POST /index
{
  "collection_name": "my_repo",
  "recreate_collection": true
}
```

### 4. Search Indexed Data
```python
# Search now uses Worker-populated Qdrant collection
POST /search
{
  "query": "payment processing",
  "top_k": 10
}
```

## Error Handling

### Worker Service Unavailable
```python
# Backend should gracefully handle worker unavailability
try:
    # Call worker service
    pass
except aiohttp.ClientError:
    # Fallback to mock/cached data
    return fallback_response()
```

### Job Tracking
```python
# Store job IDs in backend for tracking
active_parse_jobs = {}

@app.post("/parse")
async def parse_repository(request: dict):
    # ... call worker ...
    
    # Track the job
    job_id = result["job_id"]
    active_parse_jobs[job_id] = {
        "repo_url": request.get("repo_url"),
        "started_at": time.time(),
        "status": "processing"
    }
    
    return result
```

## Testing Integration

Create a test script to verify backend-worker integration:

```python
import requests
import time

def test_backend_worker_integration():
    backend_url = "http://localhost:8000"
    
    # 1. Test health check
    health = requests.get(f"{backend_url}/health").json()
    assert health["services"]["worker"] == True
    
    # 2. Test parse endpoint
    parse_response = requests.post(f"{backend_url}/parse", json={
        "repo_url": "https://github.com/octocat/Hello-World.git"
    })
    assert parse_response.status_code == 200
    
    job_id = parse_response.json()["job_id"]
    
    # 3. Poll for completion
    for _ in range(30):
        status = requests.get(f"{backend_url}/parse/status/{job_id}").json()
        if status["status"] == "completed":
            break
        time.sleep(10)
    
    # 4. Test search with indexed data
    search_response = requests.post(f"{backend_url}/search", json={
        "query": "hello world",
        "top_k": 5
    })
    assert search_response.status_code == 200
    
    print("✅ Backend-Worker integration test passed!")

if __name__ == "__main__":
    test_backend_worker_integration()
```

## Deployment Configuration

### Development
```bash
# Start services in order
cd worker && ./start.sh all
cd ../backend && python app.py
cd ../summarizer && python app.py
```

### Production
```yaml
# docker-compose.yml for full stack
version: '3.8'
services:
  qdrant:
    image: qdrant/qdrant:v1.7.0
    ports: ["6333:6333"]
    
  worker:
    build: ./worker
    ports: ["8002:8002"]
    depends_on: [qdrant]
    
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - WORKER_URL=http://worker:8002
      - QDRANT_URL=http://qdrant:6333
    depends_on: [worker]
    
  summarizer:
    build: ./summarizer
    ports: ["8001:8001"]
    
  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
```

This integration allows the backend to leverage the full parsing and indexing capabilities of the Worker Service while maintaining clean separation of concerns.
