#!/usr/bin/env python3
"""
RepoCanvas Backend API Testing Guide
Tests all endpoints with proper error handling for unavailable services
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def test_endpoint(method: str, endpoint: str, data: Dict[Any, Any] = None, description: str = "") -> Dict:
    """Test a single endpoint with error handling"""
    url = f"{BASE_URL}{endpoint}"
    
    print(f"\n🧪 Testing {method} {endpoint}")
    if description:
        print(f"   {description}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=10)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=30)
        else:
            print(f"❌ Unsupported method: {method}")
            return {"error": "Unsupported method"}
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success")
            return {"status": "success", "data": result}
        else:
            error_text = response.text
            print(f"   ⚠️ Error: {error_text[:100]}...")
            return {"status": "error", "code": response.status_code, "message": error_text}
            
    except requests.exceptions.ConnectionError:
        print(f"   ❌ Connection failed - is the backend server running?")
        return {"status": "connection_error"}
    except requests.exceptions.Timeout:
        print(f"   ❌ Request timed out")
        return {"status": "timeout"}
    except Exception as e:
        print(f"   ❌ Unexpected error: {e}")
        return {"status": "error", "message": str(e)}

def main():
    """Run comprehensive API tests"""
    print("🚀 RepoCanvas Backend API Testing")
    print("=" * 60)
    
    # Test 1: Basic endpoints
    print("\n📋 BASIC ENDPOINTS")
    print("-" * 30)
    
    test_endpoint("GET", "/", description="Root endpoint with API info")
    test_endpoint("GET", "/info", description="Detailed API information")
    test_endpoint("GET", "/health", description="Service health check")
    test_endpoint("GET", "/graph", description="Current graph data")
    
    # Test 2: Search endpoints
    print("\n🔍 SEARCH ENDPOINTS")
    print("-" * 30)
    
    search_data = {
        "query": "user authentication",
        "top_k": 5
    }
    test_endpoint("POST", "/search", search_data, "Semantic search for code")
    
    # Test 3: Analysis endpoints  
    print("\n🤖 ANALYSIS ENDPOINTS")
    print("-" * 30)
    
    analyze_data = {
        "query": "how does authentication work",
        "top_k": 3,
        "include_summary": True
    }
    test_endpoint("POST", "/analyze", analyze_data, "Complete analysis with AI summary")
    
    ask_data = {
        "question": "How do I authenticate users?",
        "top_k": 3
    }
    test_endpoint("POST", "/ask", ask_data, "Simple question-answering endpoint")
    
    # Test 4: Repository management
    print("\n📦 REPOSITORY ENDPOINTS")
    print("-" * 30)
    
    parse_data = {
        "repo_url": "https://github.com/example/test-repo",
        "branch": "main"
    }
    test_endpoint("POST", "/parse", parse_data, "Parse repository structure")
    
    parse_index_data = {
        "repo_url": "https://github.com/example/test-repo",
        "branch": "main"
    }
    test_endpoint("POST", "/parse-and-index", parse_index_data, "Parse and index repository")
    
    test_endpoint("GET", "/jobs", description="List all processing jobs")
    
    # Test 5: Edge cases
    print("\n⚠️ EDGE CASE TESTS")
    print("-" * 30)
    
    # Empty query
    test_endpoint("POST", "/search", {"query": "", "top_k": 5}, "Empty search query")
    
    # Invalid data
    test_endpoint("POST", "/ask", {"invalid": "data"}, "Invalid request data")
    
    # Non-existent job status
    test_endpoint("GET", "/status/nonexistent", description="Non-existent job status")
    
    print("\n" + "=" * 60)
    print("✅ Testing completed!")
    print("\nNext steps:")
    print("1. Check service health in /health endpoint")
    print("2. If services are down, check:")
    print("   - Worker service: http://localhost:8002/health")
    print("   - Summarizer service: http://localhost:8001/health")
    print("3. Use the interactive docs at: http://localhost:8000/docs")

if __name__ == "__main__":
    main()