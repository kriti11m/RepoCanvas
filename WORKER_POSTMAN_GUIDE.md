# 🧪 Worker Service - Postman Testing Guide

**Worker Service URL:** `http://localhost:8002`

## 📋 All Available Endpoints

### 1. 🏠 **GET /** - Root Endpoint
**URL:** `http://localhost:8002/`
**Method:** GET
**Description:** Basic service info
**Expected Response:**
```json
{
  "service": "RepoCanvas Worker",
  "version": "1.0.0", 
  "status": "running",
  "timestamp": "2025-09-22T00:54:01"
}
```

---

### 2. ❤️ **GET /health** - Health Check
**URL:** `http://localhost:8002/health`
**Method:** GET
**Description:** Service health status
**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-22T00:54:01",
  "active_jobs": 0,
  "environment": {
    "qdrant_url": "http://localhost:6333",
    "model_name": "all-MiniLM-L6-v2"
  }
}
```

---

### 3. 📝 **POST /parse** - Parse Repository
**URL:** `http://localhost:8002/parse`
**Method:** POST
**Headers:** `Content-Type: application/json`
**Body (JSON):**
```json
{
  "repo_url": "https://github.com/your-username/your-repo",
  "branch": "main",
  "output_path": "./data/graph.json"
}
```
**OR for local repo:**
```json
{
  "repo_path": "/path/to/local/repo",
  "branch": "main",
  "output_path": "./data/graph.json"
}
```
**Expected Response:**
```json
{
  "success": true,
  "job_id": "parse_1695336841",
  "message": "Repository parsing initiated",
  "status": "processing",
  "estimated_time": "5-10 seconds",
  "check_status_url": "/status/parse_1695336841"
}
```

---

### 4. 🗂️ **POST /index** - Index to Qdrant
**URL:** `http://localhost:8002/index`
**Method:** POST
**Headers:** `Content-Type: application/json`
**Body (JSON):**
```json
{
  "graph_path": "./data/graph.json",
  "collection_name": "repocanvas",
  "qdrant_url": "http://localhost:6333",
  "recreate_collection": true
}
```
**Expected Response:**
```json
{
  "success": true,
  "job_id": "index_1695336841",
  "message": "Indexing initiated",
  "status": "processing",
  "collection_name": "repocanvas",
  "check_status_url": "/status/index_1695336841"
}
```

---

### 5. 🚀 **POST /parse-and-index** - Parse + Index (Full Pipeline)
**URL:** `http://localhost:8002/parse-and-index`
**Method:** POST
**Headers:** `Content-Type: application/json`
**Body (JSON):**
```json
{
  "repo_url": "https://github.com/your-username/your-repo",
  "branch": "main",
  "collection_name": "repocanvas",
  "qdrant_url": "http://localhost:6333",
  "recreate_collection": true
}
```
**Expected Response:**
```json
{
  "success": true,
  "job_id": "parse_index_1695336841",
  "message": "Repository parsing and indexing initiated",
  "status": "processing",
  "estimated_time": "30-60 seconds",
  "check_status_url": "/status/parse_index_1695336841"
}
```

---

### 6. 🔍 **POST /search** - Semantic Search
**URL:** `http://localhost:8002/search`
**Method:** POST
**Headers:** `Content-Type: application/json`
**Body (JSON):**
```json
{
  "query": "user authentication",
  "top_k": 5,
  "collection_name": "repocanvas",
  "qdrant_url": "http://localhost:6333"
}
```
**Expected Response:**
```json
{
  "success": true,
  "results": [
    {
      "node_id": "function:authenticate_user:auth.py:15",
      "score": 0.95,
      "snippet": "def authenticate_user(username, password):",
      "file": "auth.py",
      "start_line": 15
    }
  ],
  "query": "user authentication",
  "total_results": 1,
  "collection_name": "repocanvas"
}
```

---

### 7. 🧠 **POST /analyze** - Full Analysis
**URL:** `http://localhost:8002/analyze`
**Method:** POST
**Headers:** `Content-Type: application/json`
**Body (JSON):**
```json
{
  "query": "how does user authentication work",
  "top_k": 5,
  "collection_name": "repocanvas",
  "qdrant_url": "http://localhost:6333",
  "include_full_graph": false
}
```
**Expected Response:**
```json
{
  "success": true,
  "answer_path": ["function:authenticate_user:auth.py:15"],
  "path_edges": [],
  "snippets": [
    {
      "node_id": "function:authenticate_user:auth.py:15",
      "code": "def authenticate_user(username, password):\n    # Authentication logic\n    return validate_credentials(username, password)",
      "file": "auth.py",
      "start_line": 15,
      "end_line": 20
    }
  ],
  "summary": {
    "one_liner": "Authentication system using credential validation",
    "steps": ["1. Receive credentials", "2. Validate against database"],
    "node_refs": []
  },
  "query": "how does user authentication work",
  "processing_time": 0.05
}
```

---

### 8. 📊 **GET /status/{job_id}** - Job Status
**URL:** `http://localhost:8002/status/parse_1695336841`
**Method:** GET
**Description:** Check status of a specific job
**Expected Response:**
```json
{
  "success": true,
  "job_id": "parse_1695336841",
  "type": "parse",
  "status": "completed",
  "message": "Repository parsing completed successfully",
  "processing_time": 15.5,
  "stats": {
    "files_processed": 42,
    "functions_found": 156,
    "classes_found": 23,
    "total_nodes": 300,
    "total_edges": 450
  }
}
```

---

### 9. 📋 **GET /jobs** - List All Jobs
**URL:** `http://localhost:8002/jobs`
**Method:** GET
**Description:** List all jobs (active and completed)
**Expected Response:**
```json
{
  "total_jobs": 3,
  "active_jobs": 1,
  "completed_jobs": 2,
  "jobs": {
    "parse_1695336841": {
      "type": "parse",
      "status": "completed",
      "start_time": "2025-09-22T00:54:01"
    }
  }
}
```

---

### 10. 🗑️ **DELETE /jobs/{job_id}** - Delete Job
**URL:** `http://localhost:8002/jobs/parse_1695336841`
**Method:** DELETE
**Description:** Delete a specific job
**Expected Response:**
```json
{
  "success": true,
  "message": "Job parse_1695336841 deleted successfully"
}
```

---

## 🧪 **Recommended Testing Order:**

1. **GET /** - Verify service is running
2. **GET /health** - Check health status
3. **POST /parse-and-index** - Full pipeline test with small repo
4. **GET /status/{job_id}** - Monitor the parsing job
5. **POST /search** - Test search once indexing is complete
6. **POST /analyze** - Test full analysis pipeline
7. **GET /jobs** - View all jobs
8. **DELETE /jobs/{job_id}** - Clean up test jobs

## ⚠️ **Important Notes:**

- **Qdrant Required:** Make sure Qdrant is running on `http://localhost:6333`
- **Processing Time:** Parse-and-index jobs can take 30-60 seconds for medium repos
- **Job IDs:** Save job IDs from responses to check status later
- **Collection Names:** Use consistent collection names across requests
- **Error Handling:** All endpoints return detailed error messages on failure

## 🛠️ **Quick Test Repository:**
For testing, you can use a small public repo like:
- `https://github.com/octocat/Hello-World`
- `https://github.com/your-username/small-test-repo`

This ensures quick processing times during testing!