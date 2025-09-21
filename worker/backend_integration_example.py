"""
Backend Integration Example for Worker Service
This file shows exactly how the backend should integrate with the Worker Service.
"""

import asyncio
import aiohttp
import json
import time
from typing import Dict, List, Optional, Tuple

class WorkerServiceClient:
    """Client for interacting with the Worker Service"""
    
    def __init__(self, worker_url: str = "http://localhost:8002"):
        self.worker_url = worker_url
        self.timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
    
    async def parse_repository(self, repo_url: str, branch: str = "main") -> Dict:
        """
        Parse a repository using the Worker Service.
        Returns job information for status tracking.
        """
        payload = {
            "repo_url": repo_url,
            "branch": branch
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(f"{self.worker_url}/parse", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Parse failed: {error_text}")
    
    async def get_job_status(self, job_id: str) -> Dict:
        """Get the status of a background job"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.worker_url}/status/{job_id}") as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 404:
                    raise Exception(f"Job {job_id} not found")
                else:
                    error_text = await response.text()
                    raise Exception(f"Status check failed: {error_text}")
    
    async def wait_for_job_completion(self, job_id: str, max_wait: int = 300) -> Dict:
        """Wait for a job to complete and return the results"""
        start_time = time.time()
        
        while time.time() - start_time < max_wait:
            status = await self.get_job_status(job_id)
            
            if status.get("status") == "completed":
                return status
            elif status.get("status") == "failed":
                raise Exception(f"Job failed: {status.get('error', 'Unknown error')}")
            
            # Wait before polling again
            await asyncio.sleep(5)
        
        raise Exception(f"Job {job_id} timed out after {max_wait} seconds")
    
    async def search_repository(self, query: str, top_k: int = 10, collection_name: str = "repocanvas") -> Dict:
        """
        Perform semantic search on indexed repository data.
        Returns top-k node IDs with scores.
        """
        payload = {
            "query": query,
            "top_k": top_k,
            "collection_name": collection_name
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.worker_url}/search", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Search failed: {error_text}")
    
    async def analyze_query(self, query: str, top_k: int = 10, collection_name: str = "repocanvas") -> Dict:
        """
        Full analysis: embeds query, finds subgraph, returns path + snippets + summary.
        """
        payload = {
            "query": query,
            "top_k": top_k,
            "collection_name": collection_name,
            "include_full_graph": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{self.worker_url}/analyze", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Analysis failed: {error_text}")
    
    async def index_repository(self, collection_name: str = "repocanvas", graph_path: str = None) -> Dict:
        """Index repository data to Qdrant for semantic search"""
        payload = {
            "collection_name": collection_name,
            "recreate_collection": True
        }
        
        if graph_path:
            payload["graph_path"] = graph_path
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(f"{self.worker_url}/index", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Indexing failed: {error_text}")
    
    async def parse_and_index_repository(self, repo_url: str, branch: str = "main", collection_name: str = "repocanvas") -> Dict:
        """Complete pipeline: parse repository and index to Qdrant"""
        payload = {
            "repo_url": repo_url,
            "branch": branch,
            "collection_name": collection_name,
            "recreate_collection": True
        }
        
        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            async with session.post(f"{self.worker_url}/parse-and-index", json=payload) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"Parse and index failed: {error_text}")


# Example usage in FastAPI backend
"""
from fastapi import FastAPI, HTTPException
import asyncio

app = FastAPI()
worker_client = WorkerServiceClient("http://localhost:8002")

@app.post("/parse")
async def parse_repository(request: dict):
    '''Updated backend /parse endpoint'''
    try:
        repo_url = request.get("repo_url")
        branch = request.get("branch", "main")
        
        if not repo_url:
            raise HTTPException(status_code=400, detail="repo_url is required")
        
        # Call worker service
        result = await worker_client.parse_repository(repo_url, branch)
        
        return {
            "success": True,
            "message": "Repository parsing initiated",
            "job_id": result.get("job_id"),
            "status": "processing",
            "check_status_url": f"/parse/status/{result.get('job_id')}"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/parse/status/{job_id}")
async def get_parse_status(job_id: str):
    '''Get parsing job status'''
    try:
        status = await worker_client.get_job_status(job_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/search")
async def search_nodes(request: dict):
    '''Updated backend /search endpoint'''
    try:
        query = request.get("query", "")
        top_k = request.get("top_k", 10)
        
        # Use worker's search endpoint
        result = await worker_client.search_repository(query, top_k)
        
        if result.get("success"):
            return {
                "results": result.get("results", []),
                "query": query,
                "total_results": result.get("total_results", 0),
                "processing_time": 0.1  # Worker handles timing
            }
        else:
            # Fallback to existing logic if worker search fails
            return await fallback_search(query, top_k)
            
    except Exception as e:
        # Fallback on error
        return await fallback_search(request.get("query", ""), request.get("top_k", 10))

@app.post("/analyze")
async def analyze_query(request: dict):
    '''Updated backend /analyze endpoint'''
    try:
        query = request.get("query", "")
        top_k = request.get("top_k", 10)
        
        # Use worker's analyze endpoint
        result = await worker_client.analyze_query(query, top_k)
        
        if result.get("success"):
            return {
                "answer_path": result.get("answer_path", []),
                "path_edges": result.get("path_edges", []),
                "snippets": result.get("snippets", []),
                "summary": result.get("summary"),
                "processing_time": result.get("processing_time", 0)
            }
        else:
            # Fallback to existing logic
            return await fallback_analyze(query, top_k)
            
    except Exception as e:
        # Fallback on error
        return await fallback_analyze(request.get("query", ""), request.get("top_k", 10))
"""

# Example integration workflow
async def example_integration_workflow():
    """Example of how to use the Worker Service from backend"""
    
    worker = WorkerServiceClient()
    
    print("🚀 Starting integration workflow example...")
    
    try:
        # Step 1: Parse a repository
        print("\n📝 Step 1: Parse repository")
        parse_result = await worker.parse_repository(
            repo_url="https://github.com/octocat/Hello-World.git",
            branch="main"
        )
        
        job_id = parse_result["job_id"]
        print(f"✅ Parse job started: {job_id}")
        
        # Step 2: Wait for parsing to complete
        print("\n⏳ Step 2: Wait for parsing completion")
        completed_result = await worker.wait_for_job_completion(job_id)
        print(f"✅ Parsing completed! Graph saved to: {completed_result.get('graph_path')}")
        
        # Step 3: Index the parsed data
        print("\n🔍 Step 3: Index to Qdrant")
        index_result = await worker.index_repository(
            collection_name="example_repo",
            graph_path=completed_result.get('graph_path')
        )
        
        index_job_id = index_result["job_id"]
        print(f"✅ Index job started: {index_job_id}")
        
        # Step 4: Wait for indexing to complete
        print("\n⏳ Step 4: Wait for indexing completion")
        index_completed = await worker.wait_for_job_completion(index_job_id)
        print(f"✅ Indexing completed! Collection: {index_completed.get('collection_name')}")
        
        # Step 5: Perform semantic search
        print("\n🔍 Step 5: Semantic search")
        search_result = await worker.search_repository(
            query="hello world function",
            top_k=5,
            collection_name="example_repo"
        )
        
        if search_result.get("success"):
            results = search_result.get("results", [])
            print(f"✅ Found {len(results)} search results:")
            for i, result in enumerate(results[:3]):
                print(f"   {i+1}. {result.get('node_id')} (score: {result.get('score', 0):.3f})")
        else:
            print(f"❌ Search failed: {search_result.get('error')}")
        
        # Step 6: Full analysis
        print("\n📊 Step 6: Full analysis")
        analysis_result = await worker.analyze_query(
            query="main function implementation",
            top_k=5,
            collection_name="example_repo"
        )
        
        if analysis_result.get("success"):
            print("✅ Analysis completed:")
            print(f"   Answer path: {len(analysis_result.get('answer_path', []))} nodes")
            print(f"   Code snippets: {len(analysis_result.get('snippets', []))} snippets")
            
            summary = analysis_result.get('summary', {})
            if summary:
                print(f"   Summary: {summary.get('one_liner', 'No summary')}")
        else:
            print(f"❌ Analysis failed: {analysis_result.get('error')}")
        
        print("\n🎉 Integration workflow completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Integration workflow failed: {e}")


# Example of expected graph JSON format
EXPECTED_GRAPH_FORMAT = {
    "nodes": [
        {
            "id": "function:hello_world:hello.py:1",
            "label": "hello_world",  # Added by worker
            "name": "hello_world",   # Original node name
            "file": "hello.py",
            "start_line": 1,
            "end_line": 5,
            "code": "def hello_world():\n    print('Hello, World!')\n    return True",
            "doc": "Main hello world function",
            "loc": 5,
            "cyclomatic": 1,
            "num_calls_in": 0,
            "num_calls_out": 1
        },
        {
            "id": "function:main:main.py:7",
            "label": "main",
            "name": "main",
            "file": "main.py", 
            "start_line": 7,
            "end_line": 10,
            "code": "def main():\n    hello_world()\n    print('Done')",
            "doc": "Main entry point",
            "loc": 4,
            "cyclomatic": 1,
            "num_calls_in": 0,
            "num_calls_out": 2
        }
    ],
    "edges": [
        {
            "source": "function:main:main.py:7",      # Uses 'source' not 'from'
            "target": "function:hello_world:hello.py:1", # Uses 'target' not 'to'
            "type": "call"
        }
    ],
    "metadata": {
        "node_count": 2,
        "edge_count": 1,
        "generated_by": "RepoCanvas parser",
        "schema_version": "1.0"
    }
}

# Example search response format
EXPECTED_SEARCH_RESPONSE = {
    "success": True,
    "results": [
        {
            "node_id": "function:hello_world:hello.py:1",
            "score": 0.8945,
            "snippet": "def hello_world():\n    print('Hello, World!')",
            "file": "hello.py",
            "start_line": 1
        },
        {
            "node_id": "function:main:main.py:7", 
            "score": 0.7234,
            "snippet": "def main():\n    hello_world()",
            "file": "main.py",
            "start_line": 7
        }
    ],
    "query": "hello world function",
    "total_results": 2,
    "collection_name": "example_repo"
}

# Example analyze response format
EXPECTED_ANALYZE_RESPONSE = {
    "success": True,
    "answer_path": [
        "function:main:main.py:7",
        "function:hello_world:hello.py:1"
    ],
    "path_edges": [
        {
            "source": "function:main:main.py:7",
            "target": "function:hello_world:hello.py:1",
            "type": "connection"
        }
    ],
    "snippets": [
        {
            "node_id": "function:main:main.py:7",
            "code": "def main():\n    hello_world()\n    print('Done')",
            "file": "main.py",
            "start_line": 7,
            "end_line": 10,
            "doc": "Main entry point"
        },
        {
            "node_id": "function:hello_world:hello.py:1",
            "code": "def hello_world():\n    print('Hello, World!')\n    return True",
            "file": "hello.py", 
            "start_line": 1,
            "end_line": 5,
            "doc": "Main hello world function"
        }
    ],
    "summary": {
        "one_liner": "Analysis of 2 code components across 2 files related to: hello world function",
        "steps": [
            "1. main in main.py: Main entry point",
            "2. hello_world in hello.py: Main hello world function"
        ],
        "inputs_outputs": [
            "Input: User query - 'hello world function'",
            "Output: Analysis of 2 relevant code components",
            "Files analyzed: main.py, hello.py"
        ],
        "caveats": [
            "Analysis based on static code structure and semantic similarity",
            "Results limited to indexed code components",
            "Search performed on top 2 matches"
        ],
        "node_refs": [
            {
                "node_id": "function:main:main.py:7",
                "excerpt_line": "def main():"
            },
            {
                "node_id": "function:hello_world:hello.py:1", 
                "excerpt_line": "def hello_world():"
            }
        ]
    },
    "query": "hello world function",
    "total_results": 2,
    "processing_time": 0.156
}

if __name__ == "__main__":
    # Run the example workflow
    asyncio.run(example_integration_workflow())
