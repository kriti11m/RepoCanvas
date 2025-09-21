#!/usr/bin/env python3
"""
Integration test script for RepoCanvas Backend
Tests the complete pipeline integration
"""

import asyncio
import json
import time
from app import app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(app)

def test_basic_endpoints():
    """Test basic API endpoints"""
    print("🧪 Testing basic endpoints...")
    
    # Test root endpoint
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    print(f"✅ Root endpoint: {data['message']}")
    
    # Test info endpoint
    response = client.get("/info")
    assert response.status_code == 200
    data = response.json()
    print(f"✅ Info endpoint: {data['name']}")
    
    # Test health endpoint
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    print(f"✅ Health check: {data['status']}")
    print(f"   Services: {data['services']}")

def test_search_fallback():
    """Test search with fallback when services are unavailable"""
    print("\n🧪 Testing search fallback...")
    
    search_data = {
        "query": "authentication function",
        "top_k": 5
    }
    
    response = client.post("/search", json=search_data)
    print(f"Search response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Search fallback works: {data.get('total_results', 0)} results")
        if data.get("fallback"):
            print("   Using fallback mode (worker service unavailable)")
    else:
        print(f"⚠️ Search failed: {response.status_code}")

def test_ask_endpoint():
    """Test the integrated ask endpoint"""
    print("\n🧪 Testing integrated ask endpoint...")
    
    ask_data = {
        "question": "How does user authentication work?",
        "top_k": 3
    }
    
    response = client.post("/ask", json=ask_data)
    print(f"Ask response status: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Ask endpoint works")
        print(f"   Success: {data.get('success', False)}")
        if data.get('success'):
            print(f"   Snippets found: {len(data.get('snippets', []))}")
            if 'ai_summary' in data:
                summary = data['ai_summary']
                print(f"   AI Summary: {summary.get('one_liner', 'N/A')[:80]}...")
    else:
        print(f"⚠️ Ask endpoint failed: {response.status_code}")

def main():
    """Run all integration tests"""
    print("🚀 RepoCanvas Backend Integration Test")
    print("=" * 50)
    
    try:
        test_basic_endpoints()
        test_search_fallback()
        test_ask_endpoint()
        
        print("\n" + "=" * 50)
        print("✅ Integration tests completed!")
        print("\nNext steps:")
        print("1. Start worker service: python worker/app.py")
        print("2. Start summarizer service: python summarizer/app.py")
        print("3. Start backend: python backend/app.py")
        print("4. Test with real data!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)