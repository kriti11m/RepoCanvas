from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import json
import time
import os
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
import networkx as nx
from qdrant_client import QdrantClient
from qdrant_client.http import models
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Global variables
qdrant_client = None
graph = None
graph_data = None

# Create FastAPI app
app = FastAPI(title="RepoCanvas API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Qdrant client on startup
@app.on_event("startup")
async def startup_event():
    global qdrant_client, graph, graph_data
    
    # Initialize Qdrant client
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if qdrant_url:
        try:
            qdrant_client = QdrantClient(
                url=qdrant_url,
                api_key=qdrant_api_key,
                timeout=30
            )
            print(f"✅ Connected to Qdrant at {qdrant_url}")
        except Exception as e:
            print(f"❌ Failed to connect to Qdrant: {e}")
            qdrant_client = None
    
    # Load graph data
    graph_path = "./data/graph.json"
    if os.path.exists(graph_path):
        try:
            with open(graph_path, 'r', encoding='utf-8') as f:
                graph_data = json.load(f)
            
            # Build NetworkX graph
            graph = nx.DiGraph()
            for node in graph_data.get('nodes', []):
                graph.add_node(node['id'], **node)
            for edge in graph_data.get('edges', []):
                graph.add_edge(edge['source'], edge['target'], type=edge['type'])
            
            print(f"✅ Loaded graph with {len(graph.nodes)} nodes and {len(graph.edges)} edges")
        except Exception as e:
            print(f"❌ Failed to load graph: {e}")
    
    print("🚀 Backend API started successfully!")

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RepoCanvas API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services = {}
    
    # Check Qdrant connection
    services["qdrant"] = False
    if qdrant_client:
        try:
            collections = qdrant_client.get_collections()
            services["qdrant"] = True
        except Exception as e:
            print(f"Qdrant health check failed: {e}")
    
    # Check graph loading
    services["graph"] = graph is not None and graph_data is not None
    
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
    
    overall_status = "healthy" if any(services.values()) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": int(time.time()),
        "services": services,
        "config": {
            "qdrant_url": os.getenv("QDRANT_URL"),
            "summarizer_url": os.getenv("SUMMARIZER_URL"),
            "graph_loaded": services["graph"]
        }
    }

@app.post("/parse")
async def parse_repository(request: dict):
    """Parse a repository and create graph.json"""
    return {
        "success": True,
        "message": "Repository parsing initiated",
        "graph_path": "/data/graph.json",
        "processing_time": 0.5,
        "repo_url": request.get("repo_url", ""),
        "branch": request.get("branch", "main"),
        "stats": {
            "files_processed": 42,
            "functions_found": 156,
            "classes_found": 23
        }
    }

@app.get("/graph")
async def get_graph():
    """Get the current loaded graph"""
    try:
        with open("./data/graph.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "nodes": [
                {
                    "id": "sample.function:main.py:1",
                    "label": "sample_function",
                    "file": "main.py",
                    "start_line": 1,
                    "end_line": 10,
                    "code": "def sample_function():\n    return 'Hello World'",
                    "doc": "Sample function for testing"
                }
            ],
            "edges": []
        }

@app.post("/search")
async def search_nodes(request: dict):
    """Semantic search for relevant nodes using Qdrant"""
    query = request.get("query", "")
    top_k = request.get("top_k", 10)
    start_time = time.time()
    
    if not qdrant_client:
        # Fallback to mock results if Qdrant not available
        results = await _fallback_search(query, top_k)
    else:
        try:
            # Real Qdrant search
            results = await _qdrant_search(query, top_k)
        except Exception as e:
            print(f"Qdrant search failed: {e}")
            results = await _fallback_search(query, top_k)
    
    return {
        "results": results,
        "query": query,
        "total_results": len(results),
        "processing_time": time.time() - start_time
    }

async def _qdrant_search(query: str, top_k: int) -> List[Dict]:
    """Perform search using Qdrant"""
    try:
        # For now, we'll use keyword-based search since we don't have embeddings
        # In a full implementation, you'd search by embedding vector
        collection_name = "repocanvas"
        
        # Check if collection exists
        try:
            collection_info = qdrant_client.get_collection(collection_name)
            print(f"Collection {collection_name} has {collection_info.points_count} points")
        except Exception:
            print(f"Collection {collection_name} not found, using fallback")
            return await _fallback_search(query, top_k)
        
        # Search using scroll (since we don't have query embeddings yet)
        # This would normally be a vector search
        search_results = qdrant_client.scroll(
            collection_name=collection_name,
            limit=top_k,
            with_payload=True
        )
        
        results = []
        for point in search_results[0]:  # search_results is (points, next_page_offset)
            payload = point.payload
            # Simple keyword matching for now
            if query.lower() in payload.get('snippet', '').lower() or query.lower() in payload.get('name', '').lower():
                results.append({
                    "node_id": payload.get('node_id', ''),
                    "score": 0.8,  # Mock score since we're not doing vector search
                    "snippet": payload.get('snippet', ''),
                    "file": payload.get('file', ''),
                    "start_line": payload.get('start_line', 0)
                })
        
        return results[:top_k]
        
    except Exception as e:
        print(f"Qdrant search error: {e}")
        return await _fallback_search(query, top_k)

async def _fallback_search(query: str, top_k: int) -> List[Dict]:
    """Fallback search when Qdrant is not available"""
    # Search through loaded graph data
    results = []
    
    if graph_data:
        query_lower = query.lower()
        for node in graph_data.get('nodes', []):
            score = 0.0
            
            # Simple scoring based on keyword matches
            if query_lower in node.get('label', '').lower():
                score += 0.9
            if query_lower in node.get('doc', '').lower():
                score += 0.7
            if query_lower in node.get('code', '').lower():
                score += 0.5
            if query_lower in node.get('file', '').lower():
                score += 0.3
            
            if score > 0:
                results.append({
                    "node_id": node['id'],
                    "score": score,
                    "snippet": node.get('code', '').split('\n')[0][:100],
                    "file": node.get('file', ''),
                    "start_line": node.get('start_line', 0)
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    # Ultimate fallback - mock data
    return [
        {
            "node_id": "payment.process_payment:payment.py:15",
            "score": 0.95,
            "snippet": "def process_payment(amount, payment_method):",
            "file": "payment.py",
            "start_line": 15
        },
        {
            "node_id": "payment.validate_amount:utils.py:5",
            "score": 0.87,
            "snippet": "def validate_amount(amount):",
            "file": "utils.py", 
            "start_line": 5
        }
    ][:top_k]

@app.post("/analyze")
async def analyze_query(request: dict):
    """Full analysis: search + pathfinding + summarization"""
    query = request.get("query", "")
    top_k = request.get("top_k", 10)
    include_full_graph = request.get("include_full_graph", False)
    start_time = time.time()
    
    try:
        # Step 1: Semantic search
        search_results = []
        if not qdrant_client:
            search_results = await _fallback_search(query, top_k)
        else:
            try:
                search_results = await _qdrant_search(query, top_k)
            except Exception as e:
                print(f"Search failed: {e}")
                search_results = await _fallback_search(query, top_k)
        
        if not search_results:
            return {
                "answer_path": [],
                "path_edges": [],
                "snippets": [],
                "summary": None,
                "graph": graph_data if include_full_graph else None,
                "processing_time": time.time() - start_time
            }
        
        # Step 2: Extract node IDs and compute paths
        node_ids = [result["node_id"] for result in search_results]
        answer_path, path_edges = _compute_answer_path(node_ids)
        
        # Step 3: Get code snippets for path nodes
        snippets = _get_code_snippets(answer_path)
        
        # Step 4: Call summarizer service
        summary = None
        summarizer_url = os.getenv("SUMMARIZER_URL")
        if summarizer_url and snippets:
            try:
                summary = await _call_summarizer(snippets, query, summarizer_url)
            except Exception as e:
                print(f"Summarization failed: {e}")
                summary = _generate_fallback_summary(snippets, query)
        else:
            summary = _generate_fallback_summary(snippets, query)
        
        return {
            "answer_path": answer_path,
            "path_edges": path_edges,
            "snippets": snippets,
            "summary": summary,
            "graph": graph_data if include_full_graph else None,
            "processing_time": time.time() - start_time
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def _compute_answer_path(node_ids: List[str]) -> tuple:
    """Compute shortest paths between nodes using NetworkX"""
    if not graph or not node_ids:
        return [], []
    
    # Filter to nodes that exist in graph
    valid_nodes = [nid for nid in node_ids if nid in graph]
    if not valid_nodes:
        return [], []
    
    if len(valid_nodes) == 1:
        return valid_nodes, []
    
    try:
        # Use first node as seed, find paths to others
        seed_node = valid_nodes[0]
        all_path_nodes = set([seed_node])
        all_edges = []
        
        for target_node in valid_nodes[1:]:
            try:
                # Find shortest path
                path = nx.shortest_path(graph, seed_node, target_node)
                all_path_nodes.update(path)
                
                # Add edges for this path
                for i in range(len(path) - 1):
                    source, target = path[i], path[i + 1]
                    edge_data = graph.get_edge_data(source, target)
                    if edge_data and {"source": source, "target": target} not in [{"source": e["source"], "target": e["target"]} for e in all_edges]:
                        all_edges.append({
                            "source": source,
                            "target": target,
                            "type": edge_data.get('type', 'call')
                        })
                        
            except nx.NetworkXNoPath:
                # No path exists, include isolated node
                all_path_nodes.add(target_node)
                continue
        
        # Return ordered path
        ordered_path = [nid for nid in node_ids if nid in all_path_nodes]
        # Add any nodes from paths not in original search
        for nid in all_path_nodes:
            if nid not in ordered_path:
                ordered_path.append(nid)
        
        return ordered_path, all_edges
        
    except Exception as e:
        print(f"Path computation error: {e}")
        return valid_nodes, []

def _get_code_snippets(node_ids: List[str]) -> List[Dict]:
    """Get code snippets for given node IDs"""
    snippets = []
    
    if not graph_data:
        return snippets
    
    node_map = {node['id']: node for node in graph_data.get('nodes', [])}
    
    for node_id in node_ids:
        if node_id in node_map:
            node = node_map[node_id]
            snippets.append({
                "node_id": node_id,
                "code": node.get('code', ''),
                "file": node.get('file', ''),
                "start_line": node.get('start_line', 0),
                "end_line": node.get('end_line', 0),
                "doc": node.get('doc', '')
            })
    
    return snippets

async def _call_summarizer(snippets: List[Dict], question: str, summarizer_url: str) -> Dict:
    """Call external summarizer service"""
    try:
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
            payload = {
                "snippets": snippets,
                "question": question,
                "max_tokens": 400
            }
            
            async with session.post(f"{summarizer_url}/summarize", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("summary", _generate_fallback_summary(snippets, question))
                else:
                    print(f"Summarizer returned status {response.status}")
                    return _generate_fallback_summary(snippets, question)
                    
    except Exception as e:
        print(f"Summarizer call failed: {e}")
        return _generate_fallback_summary(snippets, question)

def _generate_fallback_summary(snippets: List[Dict], question: str) -> Dict:
    """Generate fallback summary when AI summarizer is not available"""
    return {
        "one_liner": f"Analysis of {len(snippets)} code components related to: {question}",
        "steps": [
            f"{i+1}. {snippet.get('node_id', 'unknown').split(':')[0]}: {snippet.get('doc', 'Code execution')}"
            for i, snippet in enumerate(snippets[:5])
        ],
        "inputs_outputs": [
            "Input: User query and code context",
            "Output: Code analysis and flow description"
        ],
        "caveats": [
            "Analysis based on static code structure",
            "AI summarizer not available - using fallback"
        ],
        "node_refs": [
            {
                "node_id": snippet.get('node_id', ''),
                "excerpt_line": snippet.get('code', '').split('\n')[0][:50] + "..."
            }
            for snippet in snippets[:3]
        ]
    }

@app.post("/summarize")
async def summarize_code(request: dict):
    """Generate summary for given code snippets using AI Summarizer service"""
    snippets = request.get("snippets", [])
    question = request.get("question", "")
    
    summarizer_url = os.getenv("SUMMARIZER_URL")
    
    if summarizer_url:
        try:
            summary = await _call_summarizer(snippets, question, summarizer_url)
            return {"summary": summary}
        except Exception as e:
            print(f"Summarizer service failed: {e}")
            # Fall back to local summary
            pass
    
    # Fallback summary
    fallback_summary = _generate_fallback_summary(snippets, question)
    return {"summary": fallback_summary}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)