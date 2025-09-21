#!/usr/bin/env python3
"""
Test script for embeddings and Qdrant integration.
This script tests the complete pipeline from parsing to vector search.
"""

import sys
import os
from pathlib import Path
import numpy as np

# Add worker directory to path
worker_dir = Path(__file__).parent / 'worker'
sys.path.append(str(worker_dir))

def test_embeddings_basic():
    """Test basic embedding functionality."""
    print("=" * 60)
    print("🧪 Testing Basic Embeddings")
    print("=" * 60)
    
    try:
        from indexer.embedder import embed_documents, chunk_text
        
        # Test document chunking
        long_text = "This is a test document. " * 100  # Long text to test chunking
        chunks = chunk_text(long_text, max_length=100, overlap=20)
        print(f"✅ Text chunking: {len(chunks)} chunks from {len(long_text)} chars")
        
        # Test embedding generation
        test_docs = [
            "def hello_world(): return 'Hello, World!'",
            "class Calculator: def add(self, a, b): return a + b",
            "import os\ndef read_file(path): return open(path).read()"
        ]
        
        print(f"🔄 Generating embeddings for {len(test_docs)} test documents...")
        embeddings = embed_documents(test_docs, batch_size=2)
        
        print(f"✅ Embeddings shape: {embeddings.shape}")
        print(f"✅ Embedding dimension: {embeddings.shape[1] if len(embeddings) > 0 else 0}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("   Install sentence-transformers: pip install sentence-transformers")
        return False
    except Exception as e:
        print(f"❌ Error testing embeddings: {e}")
        return False

def test_embeddings_with_nodes():
    """Test embedding generation from parsed nodes."""
    print("\n" + "=" * 60)
    print("🧪 Testing Node Embeddings")
    print("=" * 60)
    
    try:
        from parse_repo import build_nodes
        from indexer.embedder import embed_nodes_documents
        
        # Parse nodes from worker directory
        print("🔄 Parsing nodes from worker directory...")
        nodes, name_map = build_nodes(str(worker_dir))
        print(f"✅ Parsed {len(nodes)} nodes")
        
        # Generate embeddings for a subset of nodes (to save time)
        test_nodes = nodes[:5]  # Test with first 5 nodes
        print(f"🔄 Generating embeddings for {len(test_nodes)} nodes...")
        
        embeddings, documents = embed_nodes_documents(test_nodes)
        
        print(f"✅ Generated embeddings: {embeddings.shape}")
        print(f"✅ Generated documents: {len(documents)}")
        
        # Show sample document
        if documents:
            print(f"\n📄 Sample document preview:")
            print(f"   {documents[0][:200]}...")
        
        return True, test_nodes, embeddings, documents
        
    except Exception as e:
        print(f"❌ Error testing node embeddings: {e}")
        import traceback
        traceback.print_exc()
        return False, [], [], []

def test_qdrant_functions():
    """Test Qdrant wrapper functions (without actual Qdrant server)."""
    print("\n" + "=" * 60)
    print("🧪 Testing Qdrant Functions")
    print("=" * 60)
    
    try:
        from indexer.qdrant_client import create_node_payloads
        from parse_repo import build_nodes
        
        # Get some test nodes
        nodes, _ = build_nodes(str(worker_dir))
        test_nodes = nodes[:3]
        
        # Test payload creation
        print(f"🔄 Creating payloads for {len(test_nodes)} nodes...")
        payloads = create_node_payloads(test_nodes)
        
        print(f"✅ Created {len(payloads)} payloads")
        
        # Verify payload structure
        if payloads:
            sample_payload = payloads[0]
            required_fields = ['node_id', 'name', 'file', 'start_line', 'snippet']
            missing_fields = [f for f in required_fields if f not in sample_payload]
            
            if not missing_fields:
                print(f"✅ Payload structure is valid")
                print(f"   Sample payload keys: {list(sample_payload.keys())}")
            else:
                print(f"⚠️ Missing fields in payload: {missing_fields}")
        
        return True, payloads
        
    except Exception as e:
        print(f"❌ Error testing Qdrant functions: {e}")
        return False, []

def test_complete_pipeline():
    """Test the complete pipeline from parsing to embeddings."""
    print("\n" + "=" * 60)
    print("🧪 Testing Complete Pipeline")
    print("=" * 60)
    
    try:
        from parse_repo import build_nodes, make_document_for_node
        from indexer.embedder import embed_documents
        from indexer.qdrant_client import create_node_payloads
        
        # Step 1: Parse repository
        print("🔄 Step 1: Parsing repository...")
        nodes, name_map = build_nodes(str(worker_dir))
        print(f"✅ Parsed {len(nodes)} nodes, {len(name_map)} unique names")
        
        # Step 2: Create documents
        print("🔄 Step 2: Creating documents...")
        documents = []
        for node in nodes[:5]:  # Test with subset
            doc = make_document_for_node(node, max_lines=20)
            documents.append(doc)
        print(f"✅ Created {len(documents)} documents")
        
        # Step 3: Generate embeddings
        print("🔄 Step 3: Generating embeddings...")
        embeddings = embed_documents(documents)
        print(f"✅ Generated embeddings: {embeddings.shape}")
        
        # Step 4: Create payloads
        print("🔄 Step 4: Creating Qdrant payloads...")
        payloads = create_node_payloads(nodes[:5])
        print(f"✅ Created {len(payloads)} payloads")
        
        # Step 5: Simulate Qdrant operations
        print("🔄 Step 5: Simulating Qdrant operations...")
        
        # Simulate point creation (without actual Qdrant)
        simulated_points = []
        id_to_node_map = {}
        
        for i, (embedding, payload) in enumerate(zip(embeddings, payloads)):
            point_id = i + 1
            simulated_points.append({
                'id': point_id,
                'vector': embedding.tolist(),
                'payload': payload
            })
            id_to_node_map[point_id] = payload['node_id']
        
        print(f"✅ Simulated {len(simulated_points)} Qdrant points")
        print(f"✅ ID mapping: {len(id_to_node_map)} entries")
        
        # Test similarity calculation
        if len(embeddings) >= 2:
            similarity = np.dot(embeddings[0], embeddings[1])
            print(f"✅ Sample similarity score: {similarity:.4f}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in complete pipeline: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🚀 RepoCanvas Embeddings & Qdrant Testing Suite")
    print("=" * 60)
    
    # Check dependencies
    missing_deps = []
    try:
        import sentence_transformers
    except ImportError:
        missing_deps.append("sentence-transformers")
    
    try:
        import qdrant_client
    except ImportError:
        missing_deps.append("qdrant-client")
    
    if missing_deps:
        print(f"⚠️ Missing dependencies: {missing_deps}")
        print("   Install with: pip install sentence-transformers qdrant-client")
        print("   These tests will run in limited mode...")
    
    # Run tests
    results = []
    
    # Test 1: Basic embeddings
    success = test_embeddings_basic()
    results.append(("Basic Embeddings", success))
    
    # Test 2: Node embeddings
    success, nodes, embeddings, documents = test_embeddings_with_nodes()
    results.append(("Node Embeddings", success))
    
    # Test 3: Qdrant functions
    success, payloads = test_qdrant_functions()
    results.append(("Qdrant Functions", success))
    
    # Test 4: Complete pipeline
    success = test_complete_pipeline()
    results.append(("Complete Pipeline", success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if success:
            passed += 1
    
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All tests passed! Your embeddings pipeline is ready!")
        print("\n💡 Next steps:")
        print("   1. Set up Qdrant server (local or cloud)")
        print("   2. Test with actual Qdrant connection")
        print("   3. Integrate with search API endpoints")
    else:
        print("⚠️ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()
