# backend/worker/indexer/qdrant_client.py
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, PointStruct, Distance
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json

def create_or_recreate_collection(
    client: QdrantClient, 
    name: str, 
    vector_size: int,
    distance: str = "Cosine"
) -> bool:
    """
    Create or recreate a Qdrant collection with specified vector size.
    
    Args:
        client (QdrantClient): Qdrant client instance
        name (str): Name of the collection
        vector_size (int): Dimension of the vectors
        distance (str): Distance metric to use ("Cosine", "Dot", "Euclid")
    
    Returns:
        bool: True if successful
    """
    try:
        print(f"Creating/recreating collection '{name}' with vector size {vector_size}...")
        client.recreate_collection(
            collection_name=name, 
            vectors_config=VectorParams(size=vector_size, distance=distance)
        )
        print(f"✅ Collection '{name}' created successfully")
        return True
    except Exception as e:
        try:
            # Fallback to create if recreate fails
            client.create_collection(
                collection_name=name, 
                vectors_config=VectorParams(size=vector_size, distance=distance)
            )
            print(f"✅ Collection '{name}' created successfully (fallback)")
            return True
        except Exception as e2:
            print(f"❌ Failed to create collection '{name}': {e2}")
            return False

def upsert_embeddings(
    client: QdrantClient, 
    collection_name: str, 
    embeddings: np.ndarray, 
    payloads: List[Dict[str, Any]], 
    start_id: int = 1
) -> Dict[int, str]:
    """
    Upsert embeddings and payloads into Qdrant collection.
    
    Args:
        client (QdrantClient): Qdrant client instance
        collection_name (str): Name of the collection
        embeddings (np.ndarray): Array of embeddings
        payloads (List[Dict]): List of payload dictionaries
        start_id (int): Starting ID for points
    
    Returns:
        Dict[int, str]: Mapping from point ID to node_id
    """
    if len(embeddings) != len(payloads):
        raise ValueError(f"Embeddings ({len(embeddings)}) and payloads ({len(payloads)}) must have same length")
    
    points = []
    id_to_node_map = {}
    
    print(f"Preparing {len(embeddings)} points for upsert...")
    
    for i, (embedding, payload) in enumerate(zip(embeddings, payloads)):
        point_id = start_id + i
        node_id = payload.get('node_id', f'unknown_{i}')
        
        # Store the mapping
        id_to_node_map[point_id] = node_id
        
        # Create point structure
        point = PointStruct(
            id=point_id, 
            vector=embedding.tolist(), 
            payload=payload
        )
        points.append(point)
    
    try:
        # Upsert points in batches to avoid memory issues
        batch_size = 100
        total_batches = (len(points) + batch_size - 1) // batch_size
        
        print(f"Upserting {len(points)} points in {total_batches} batches...")
        
        for i in range(0, len(points), batch_size):
            batch = points[i:i + batch_size]
            client.upsert(collection_name=collection_name, points=batch)
            print(f"  Batch {i//batch_size + 1}/{total_batches} completed")
        
        print(f"✅ Successfully upserted {len(points)} points")
        return id_to_node_map
        
    except Exception as e:
        print(f"❌ Failed to upsert embeddings: {e}")
        return {}

def create_node_payloads(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create payload dictionaries for nodes to store in Qdrant.
    
    Args:
        nodes (List[Dict]): List of parsed node dictionaries
    
    Returns:
        List[Dict]: List of payload dictionaries with node_id, name, file, start_line, snippet
    """
    payloads = []
    
    for node in nodes:
        # Extract code snippet (truncate if too long)
        snippet = node.get('code', '')
        if len(snippet) > 500:
            snippet = snippet[:500] + "..."
        
        # Create comprehensive payload
        payload = {
            'node_id': node.get('id', ''),
            'name': node.get('name', ''),
            'file': node.get('file', ''),
            'start_line': int(node.get('start_line', 0)),
            'end_line': int(node.get('end_line', 0)),
            'snippet': snippet,
            'doc': node.get('doc', ''),
            'loc': int(node.get('loc', 0)),
            'cyclomatic': int(node.get('cyclomatic', 0)),
            'num_calls_in': int(node.get('num_calls_in', 0)),
            'num_calls_out': int(node.get('num_calls_out', 0)),
            'node_type': 'function' if 'function:' in node.get('id', '') else 'class'
        }
        
        payloads.append(payload)
    
    return payloads

def search_similar_nodes(
    client: QdrantClient,
    collection_name: str,
    query_embedding: np.ndarray,
    top_k: int = 10,
    score_threshold: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Search for similar nodes using vector similarity.
    
    Args:
        client (QdrantClient): Qdrant client instance
        collection_name (str): Name of the collection
        query_embedding (np.ndarray): Query vector
        top_k (int): Number of results to return
        score_threshold (float): Minimum similarity score
    
    Returns:
        List[Dict]: Search results with scores and payloads
    """
    try:
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_embedding.tolist(),
            limit=top_k,
            score_threshold=score_threshold
        )
        
        results = []
        for result in search_results:
            results.append({
                'id': result.id,
                'score': result.score,
                'payload': result.payload
            })
        
        return results
        
    except Exception as e:
        print(f"❌ Search failed: {e}")
        return []

def get_collection_info(client: QdrantClient, collection_name: str) -> Dict[str, Any]:
    """
    Get information about a Qdrant collection.
    
    Args:
        client (QdrantClient): Qdrant client instance
        collection_name (str): Name of the collection
    
    Returns:
        Dict: Collection information
    """
    try:
        collection_info = client.get_collection(collection_name)
        return {
            'name': collection_name,
            'status': collection_info.status,
            'points_count': collection_info.points_count,
            'vector_size': collection_info.config.params.vectors.size,
            'distance': collection_info.config.params.vectors.distance
        }
    except Exception as e:
        print(f"❌ Failed to get collection info: {e}")
        return {}
