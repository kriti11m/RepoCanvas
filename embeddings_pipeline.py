#!/usr/bin/env python3
"""
Complete RepoCanvas Embeddings Pipeline Demo

This script demonstrates the full pipeline:
1. Parse repository code into nodes
2. Generate semantic documents for each node
3. Create vector embeddings using sentence-transformers
4. Prepare data for Qdrant vector database
5. Simulate semantic search functionality
"""

import sys
import os
import json
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Tuple
import time

# Add worker directory to path
worker_dir = Path(__file__).parent / 'worker'
sys.path.append(str(worker_dir))

def run_complete_pipeline(repo_path: str, output_dir: str = "data") -> Dict[str, Any]:
    """
    Run the complete embeddings pipeline.
    
    Args:
        repo_path (str): Path to repository to analyze
        output_dir (str): Directory to save outputs
    
    Returns:
        Dict: Pipeline results and statistics
    """
    print("🚀 RepoCanvas Complete Embeddings Pipeline")
    print("=" * 60)
    
    start_time = time.time()
    results = {}
    
    # Step 1: Parse Repository
    print("🔄 Step 1: Parsing Repository...")
    from parse_repo import build_repository_graph, build_nodes, make_document_for_node
    
    nodes, name_map = build_nodes(repo_path)
    print(f"✅ Parsed {len(nodes)} code nodes")
    results['nodes_count'] = len(nodes)
    results['unique_names'] = len(name_map)
    
    # Step 2: Generate Documents
    print("\n🔄 Step 2: Generating Semantic Documents...")
    documents = []
    doc_metadata = []
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    docs_dir = os.path.join(output_dir, "documents")
    os.makedirs(docs_dir, exist_ok=True)
    
    for i, node in enumerate(nodes):
        try:
            # Generate document content
            doc_content = make_document_for_node(node, max_lines=40)
            documents.append(doc_content)
            
            # Save individual document file
            safe_id = node['id'].replace(':', '_').replace('/', '_')
            doc_path = os.path.join(docs_dir, f"{safe_id}.md")
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            # Track metadata
            doc_metadata.append({
                'index': i,
                'node_id': node['id'],
                'name': node['name'],
                'file': node['file'],
                'doc_path': doc_path
            })
            
        except Exception as e:
            print(f"⚠️ Failed to create document for {node.get('name')}: {e}")
            continue
    
    print(f"✅ Generated {len(documents)} semantic documents")
    print(f"✅ Saved to: {docs_dir}")
    results['documents_count'] = len(documents)
    
    # Step 3: Generate Embeddings
    print("\n🔄 Step 3: Generating Vector Embeddings...")
    from indexer.embedder import embed_documents
    
    embeddings = embed_documents(documents, model_name='all-MiniLM-L6-v2', batch_size=32)
    embedding_dim = embeddings.shape[1] if len(embeddings) > 0 else 0
    
    print(f"✅ Generated embeddings: {embeddings.shape}")
    results['embedding_dimension'] = embedding_dim
    
    # Save embeddings
    embeddings_path = os.path.join(output_dir, "embeddings.npy")
    np.save(embeddings_path, embeddings)
    print(f"✅ Saved embeddings to: {embeddings_path}")
    
    # Step 4: Prepare Qdrant Data
    print("\n🔄 Step 4: Preparing Qdrant Data...")
    from indexer.qdrant_client import create_node_payloads
    
    payloads = create_node_payloads(nodes)
    
    # Create Qdrant-ready data structure
    qdrant_data = {
        'collection_name': 'repocanvas_nodes',
        'vector_size': embedding_dim,
        'points': []
    }
    
    for i, (embedding, payload) in enumerate(zip(embeddings, payloads)):
        point = {
            'id': i + 1,
            'vector': embedding.tolist(),
            'payload': payload
        }
        qdrant_data['points'].append(point)
    
    # Save Qdrant data
    qdrant_path = os.path.join(output_dir, "qdrant_data.json")
    with open(qdrant_path, 'w', encoding='utf-8') as f:
        json.dump(qdrant_data, f, indent=2)
    
    print(f"✅ Prepared {len(qdrant_data['points'])} Qdrant points")
    print(f"✅ Saved to: {qdrant_path}")
    results['qdrant_points'] = len(qdrant_data['points'])
    
    # Step 5: Save Metadata
    print("\n🔄 Step 5: Saving Metadata...")
    metadata = {
        'pipeline_info': {
            'timestamp': int(time.time()),
            'repo_path': repo_path,
            'model_name': 'all-MiniLM-L6-v2',
            'embedding_dimension': embedding_dim
        },
        'statistics': results,
        'documents': doc_metadata
    }
    
    metadata_path = os.path.join(output_dir, "metadata.json")
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Saved metadata to: {metadata_path}")
    
    # Step 6: Demonstrate Search
    print("\n🔄 Step 6: Demonstrating Semantic Search...")
    demo_search_queries(embeddings, payloads, documents[:10])  # Demo with first 10
    
    # Final results
    elapsed_time = time.time() - start_time
    results['processing_time'] = elapsed_time
    
    print("\n" + "=" * 60)
    print("✅ PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📊 Statistics:")
    print(f"   - Processed: {results['nodes_count']} code nodes")
    print(f"   - Generated: {results['documents_count']} documents")
    print(f"   - Embeddings: {embeddings.shape}")
    print(f"   - Qdrant points: {results['qdrant_points']}")
    print(f"   - Processing time: {elapsed_time:.2f} seconds")
    
    return results

def demo_search_queries(embeddings: np.ndarray, payloads: List[Dict], documents: List[str]):
    """
    Demonstrate semantic search functionality.
    
    Args:
        embeddings (np.ndarray): Code embeddings
        payloads (List[Dict]): Node metadata
        documents (List[str]): Document texts
    """
    print("🔍 Semantic Search Demo")
    print("-" * 40)
    
    if len(embeddings) < 2:
        print("⚠️ Need at least 2 embeddings for search demo")
        return
    
    # Calculate similarity matrix
    similarities = np.dot(embeddings, embeddings.T)
    
    # Find most similar pairs
    similarity_pairs = []
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            similarity_pairs.append((i, j, similarities[i, j]))
    
    # Sort by similarity
    similarity_pairs.sort(key=lambda x: x[2], reverse=True)
    
    print("🔗 Most Similar Code Pairs:")
    for i, (idx1, idx2, score) in enumerate(similarity_pairs[:3]):
        node1 = payloads[idx1]['name']
        node2 = payloads[idx2]['name']
        file1 = payloads[idx1]['file']
        file2 = payloads[idx2]['file']
        
        print(f"\n{i+1}. Similarity: {score:.4f}")
        print(f"   📄 {node1} ({file1})")
        print(f"   📄 {node2} ({file2})")
    
    # Simulate query search
    print(f"\n🔍 Query Search Simulation:")
    if len(embeddings) >= 1:
        query_embedding = embeddings[0]  # Use first embedding as query
        query_node = payloads[0]['name']
        
        # Calculate similarities to all other nodes
        scores = np.dot(query_embedding, embeddings.T)
        
        # Get top results (excluding self)
        top_indices = np.argsort(scores)[::-1][1:4]  # Top 3, excluding self
        
        print(f"   Query: '{query_node}'")
        print(f"   Top similar functions:")
        
        for i, idx in enumerate(top_indices):
            node_name = payloads[idx]['name']
            node_file = payloads[idx]['file']
            score = scores[idx]
            print(f"   {i+1}. {node_name} ({node_file}) - Score: {score:.4f}")

def demonstrate_qdrant_integration():
    """
    Show how to integrate with actual Qdrant server.
    """
    print("\n🔌 Qdrant Integration Guide")
    print("-" * 40)
    
    integration_code = '''
# Example: Connect to Qdrant and index your embeddings

from qdrant_client import QdrantClient
from indexer.qdrant_client import create_or_recreate_collection, upsert_embeddings

# 1. Connect to Qdrant (local or cloud)
client = QdrantClient("localhost", port=6333)  # Local
# client = QdrantClient(url="your-cloud-url", api_key="your-api-key")  # Cloud

# 2. Load your data
import numpy as np
import json

embeddings = np.load("data/embeddings.npy")
with open("data/qdrant_data.json", "r") as f:
    qdrant_data = json.load(f)

payloads = [point["payload"] for point in qdrant_data["points"]]

# 3. Create collection
create_or_recreate_collection(client, "repocanvas_nodes", embeddings.shape[1])

# 4. Upload embeddings
id_mapping = upsert_embeddings(client, "repocanvas_nodes", embeddings, payloads)

# 5. Search for similar code
from indexer.qdrant_client import search_similar_nodes

query_embedding = embeddings[0]  # Your query embedding
results = search_similar_nodes(client, "repocanvas_nodes", query_embedding, top_k=5)

for result in results:
    print(f"Score: {result['score']:.4f} - {result['payload']['name']}")
'''
    
    print(integration_code)

def main():
    """Main function to run the complete pipeline."""
    print("🎯 RepoCanvas Embeddings Pipeline")
    print("This will analyze the worker directory and create embeddings")
    
    # Configuration
    repo_path = str(worker_dir)
    output_dir = "data"
    
    print(f"\n📂 Repository: {repo_path}")
    print(f"💾 Output: {output_dir}")
    
    # Check if we should proceed
    response = input("\nProceed with pipeline? (y/n): ").lower().strip()
    if response != 'y':
        print("Pipeline cancelled.")
        return
    
    try:
        # Run the complete pipeline
        results = run_complete_pipeline(repo_path, output_dir)
        
        # Show integration guide
        demonstrate_qdrant_integration()
        
        print(f"\n🎉 Success! Your embeddings are ready for use.")
        print(f"📁 Check the '{output_dir}' directory for all generated files:")
        print(f"   - documents/: Individual markdown documents")
        print(f"   - embeddings.npy: Vector embeddings")
        print(f"   - qdrant_data.json: Ready for Qdrant upload")
        print(f"   - metadata.json: Pipeline metadata")
        
    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
