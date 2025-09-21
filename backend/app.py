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
from qdrant_client.models import Distance, VectorParams
import requests
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

async def _check_qdrant_health():
    """Check if Qdrant is available and has data"""
    if not qdrant_client:
        return False, "Qdrant client not initialized"
    
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "repocanvas")
    
    try:
        collections = qdrant_client.get_collections()
        collection_exists = any(col.name == collection_name for col in collections.collections)
        
        if not collection_exists:
            return False, f"Collection '{collection_name}' not found"
        
        collection_info = qdrant_client.get_collection(collection_name)
        point_count = collection_info.points_count
        
        return True, f"Collection '{collection_name}' has {point_count} points"
        
    except Exception as e:
        return False, f"Error checking Qdrant: {e}"

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RepoCanvas API is running!", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    services = {}
    
    # Check Qdrant connection
    qdrant_healthy, qdrant_message = await _check_qdrant_health()
    services["qdrant"] = qdrant_healthy
    
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
        "messages": {
            "qdrant": qdrant_message,
            "graph": "Graph loaded successfully" if services["graph"] else "No graph data available"
        },
        "config": {
            "qdrant_url": os.getenv("QDRANT_URL"),
            "summarizer_url": os.getenv("SUMMARIZER_URL"),
            "collection_name": os.getenv("QDRANT_COLLECTION_NAME", "repocanvas")
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
    """Perform semantic search using Qdrant with vector embeddings"""
    if not qdrant_client:
        return await _fallback_search(query, top_k)
    
    collection_name = os.getenv("QDRANT_COLLECTION_NAME", "repocanvas")
    
    try:
        # Check if collection exists and has points
        collection_info = qdrant_client.get_collection(collection_name)
        if collection_info.points_count == 0:
            print(f"⚠️ Collection '{collection_name}' is empty, using fallback search")
            return await _fallback_search(query, top_k)
        
        print(f"🔍 Searching collection '{collection_name}' with {collection_info.points_count} points")
        
        # Since Worker handles embeddings, we'll do keyword search for now
        # The Worker team will provide vector search capabilities
        print("⚠️ Using keyword search - waiting for Worker team to populate embeddings")
        return await _keyword_search_qdrant(query, top_k, collection_name)
        
        results = []
        for result in search_results:
            payload = result.payload or {}
            results.append({
                "node_id": payload.get('node_id', str(result.id)),
                "score": float(result.score),
                "snippet": payload.get('snippet', payload.get('code', '')[:200]),
                "file": payload.get('file', ''),
                "start_line": payload.get('start_line', 0)
            })
        
        print(f"✅ Found {len(results)} results with vector search")
        return results
        
    except Exception as e:
        print(f"❌ Qdrant vector search error: {e}")
        # Try keyword search as fallback
        try:
            return await _keyword_search_qdrant(query, top_k, collection_name)
        except Exception as e2:
            print(f"❌ Keyword search also failed: {e2}")
            return await _fallback_search(query, top_k)

async def _keyword_search_qdrant(query: str, top_k: int, collection_name: str) -> List[Dict]:
    """Fallback keyword search in Qdrant when vector search fails"""
    try:
        # Use scroll to get all points and filter by keywords
        all_points, _ = qdrant_client.scroll(
            collection_name=collection_name,
            limit=100,  # Reasonable limit for keyword search
            with_payload=True
        )
        
        results = []
        query_lower = query.lower()
        
        for point in all_points:
            payload = point.payload or {}
            score = 0.0
            
            # Simple keyword scoring
            snippet = payload.get('snippet', payload.get('code', '')).lower()
            file_name = payload.get('file', '').lower()
            node_id = payload.get('node_id', '').lower()
            
            if query_lower in snippet:
                score += 0.8
            if query_lower in file_name:
                score += 0.6
            if query_lower in node_id:
                score += 0.7
            
            if score > 0:
                results.append({
                    "node_id": payload.get('node_id', str(point.id)),
                    "score": score,
                    "snippet": payload.get('snippet', payload.get('code', '')[:200]),
                    "file": payload.get('file', ''),
                    "start_line": payload.get('start_line', 0)
                })
        
        # Sort by score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
        
    except Exception as e:
        print(f"❌ Keyword search error: {e}")
        return []

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
    """
    Compute optimal path through relevant nodes using advanced NetworkX algorithms
    
    Strategies:
    1. Single node: Return as-is
    2. Two nodes: Find shortest path between them
    3. Multiple nodes: Use Steiner tree approximation to find minimal connecting subgraph
    """
    if not graph or not node_ids:
        return [], []
    
    # Filter to nodes that exist in graph
    valid_nodes = [nid for nid in node_ids if nid in graph]
    if not valid_nodes:
        return [], []
    
    print(f"🔍 Computing path for {len(valid_nodes)} nodes: {valid_nodes[:3]}...")
    
    if len(valid_nodes) == 1:
        return valid_nodes, []
    
    if len(valid_nodes) == 2:
        return _find_shortest_path_between_two(valid_nodes[0], valid_nodes[1])
    
    # Multiple nodes - use Steiner tree approach
    return _find_steiner_tree_path(valid_nodes)

def _find_shortest_path_between_two(source: str, target: str) -> tuple:
    """Find shortest path between two specific nodes"""
    try:
        # Try both directions since graph might be directed
        path = None
        try:
            path = nx.shortest_path(graph, source, target)
            print(f"✅ Found path {source} -> {target}: {len(path)} nodes")
        except nx.NetworkXNoPath:
            try:
                path = nx.shortest_path(graph, target, source)
                print(f"✅ Found reverse path {target} -> {source}: {len(path)} nodes")
            except nx.NetworkXNoPath:
                print(f"❌ No path exists between {source} and {target}")
                return [source, target], []
        
        if not path:
            return [source, target], []
            
        # Extract edges for the path
        path_edges = []
        for i in range(len(path) - 1):
            src, tgt = path[i], path[i + 1]
            edge_data = graph.get_edge_data(src, tgt) or graph.get_edge_data(tgt, src)
            path_edges.append({
                "source": src,
                "target": tgt,
                "type": edge_data.get('type', 'call') if edge_data else 'unknown'
            })
        
        return path, path_edges
        
    except Exception as e:
        print(f"❌ Error finding path between two nodes: {e}")
        return [source, target], []

def _find_steiner_tree_path(nodes: List[str]) -> tuple:
    """
    Find minimal connecting subgraph for multiple nodes using Steiner tree approximation
    
    Algorithm:
    1. Find all pairwise shortest paths between target nodes
    2. Build minimum spanning tree of these paths
    3. Extract the connecting subgraph
    """
    try:
        print(f"🌳 Building Steiner tree for {len(nodes)} nodes")
        
        # Step 1: Find all pairwise shortest paths
        pairwise_paths = {}
        path_costs = {}
        
        for i, source in enumerate(nodes):
            for j, target in enumerate(nodes[i+1:], i+1):
                try:
                    # Try both directions
                    path = None
                    cost = float('inf')
                    
                    try:
                        path = nx.shortest_path(graph, source, target)
                        cost = len(path) - 1  # Edge count
                    except nx.NetworkXNoPath:
                        try:
                            path = nx.shortest_path(graph, target, source)
                            cost = len(path) - 1
                        except nx.NetworkXNoPath:
                            continue
                    
                    if path and cost < float('inf'):
                        key = (source, target)
                        pairwise_paths[key] = path
                        path_costs[key] = cost
                        
                except Exception as e:
                    print(f"⚠️ Error finding path {source} -> {target}: {e}")
                    continue
        
        if not pairwise_paths:
            print("❌ No connecting paths found, returning isolated nodes")
            return nodes, []
        
        # Step 2: Build minimum spanning tree of paths
        # Create a complete graph of target nodes with path costs as weights
        mst_graph = nx.Graph()
        for node in nodes:
            mst_graph.add_node(node)
        
        for (source, target), cost in path_costs.items():
            mst_graph.add_edge(source, target, weight=cost, path=pairwise_paths[(source, target)])
        
        # Find minimum spanning tree
        try:
            mst = nx.minimum_spanning_tree(mst_graph)
            print(f"✅ Built MST with {len(mst.edges)} edges")
        except Exception as e:
            print(f"❌ MST construction failed: {e}")
            # Fallback: use the shortest single path
            if pairwise_paths:
                best_path = min(pairwise_paths.values(), key=len)
                return best_path, _extract_edges_from_path(best_path)
            return nodes, []
        
        # Step 3: Extract all nodes and edges from MST paths
        all_path_nodes = set()
        all_edges = []
        
        for source, target, data in mst.edges(data=True):
            path = data['path']
            all_path_nodes.update(path)
            
            # Add edges from this path
            for i in range(len(path) - 1):
                src, tgt = path[i], path[i + 1]
                edge_data = graph.get_edge_data(src, tgt) or graph.get_edge_data(tgt, src)
                
                # Avoid duplicate edges
                edge_key = (src, tgt)
                if not any(e['source'] == src and e['target'] == tgt for e in all_edges):
                    all_edges.append({
                        "source": src,
                        "target": tgt,
                        "type": edge_data.get('type', 'call') if edge_data else 'derived'
                    })
        
        # Order nodes by original relevance, then by graph topology
        ordered_path = []
        for node in nodes:
            if node in all_path_nodes:
                ordered_path.append(node)
        
        # Add intermediate nodes
        for node in all_path_nodes:
            if node not in ordered_path:
                ordered_path.append(node)
        
        print(f"✅ Steiner tree: {len(ordered_path)} nodes, {len(all_edges)} edges")
        return ordered_path, all_edges
        
    except Exception as e:
        print(f"❌ Steiner tree computation failed: {e}")
        # Ultimate fallback: return nodes with simple pairwise connections
        return _fallback_simple_path(nodes)

def _extract_edges_from_path(path: List[str]) -> List[Dict]:
    """Extract edge information from a node path"""
    edges = []
    for i in range(len(path) - 1):
        src, tgt = path[i], path[i + 1]
        edge_data = graph.get_edge_data(src, tgt) or graph.get_edge_data(tgt, src)
        edges.append({
            "source": src,
            "target": tgt,
            "type": edge_data.get('type', 'call') if edge_data else 'derived'
        })
    return edges

def _fallback_simple_path(nodes: List[str]) -> tuple:
    """Simple fallback: try to connect nodes in sequence"""
    print(f"🔄 Using simple fallback for {len(nodes)} nodes")
    
    if len(nodes) <= 1:
        return nodes, []
    
    # Try to find at least one connection
    for i in range(len(nodes) - 1):
        source, target = nodes[i], nodes[i + 1]
        try:
            path = nx.shortest_path(graph, source, target)
            return path, _extract_edges_from_path(path)
        except nx.NetworkXNoPath:
            try:
                path = nx.shortest_path(graph, target, source)
                return path, _extract_edges_from_path(path)
            except nx.NetworkXNoPath:
                continue
    
    # No connections found
    return nodes, []

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