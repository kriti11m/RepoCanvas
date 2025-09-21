# Postman Testing Guide for RepoCanvas Worker Service

## 🚀 Quick Setup

1. **Import Collection**: Import `RepoCanvas_Worker_API.postman_collection.json` into Postman
2. **Set Base URL**: Collection variable `worker_url` is set to `http://localhost:8002`
3. **Start Services**: Run `./start.sh all` in the worker directory
4. **Test Health**: Start with the Health Check endpoint

---

## 📋 All Endpoints for Postman Testing

### 🏥 **Health & Status Endpoints**

#### 1. **Root Endpoint**
```
GET http://localhost:8002/
```
**Expected Response:**
```json
{
  "service": "RepoCanvas Worker",
  "version": "1.0.0",
  "status": "running",
  "timestamp": "2025-09-21T..."
}
```

#### 2. **Health Check**
```
GET http://localhost:8002/health
```
**Expected Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-09-21T...",
  "active_jobs": 0,
  "environment": {
    "qdrant_url": "http://localhost:6333",
    "model_name": "all-MiniLM-L6-v2"
  }
}
```

---

### 📁 **Repository Operations**

#### 3. **Parse Repository (Git URL)**
```
POST http://localhost:8002/parse
Content-Type: application/json

{
  "repo_url": "https://github.com/octocat/Hello-World.git",
  "branch": "main"
}
```

**Expected Response:**
```json
{
  "success": true,
  "job_id": "parse_1695123456",
  "message": "Repository parsing initiated",
  "status": "processing",
  "estimated_time": "30-120 seconds",
  "check_status_url": "/status/parse_1695123456"
}
```

#### 4. **Parse Repository (Local Path)**
```
POST http://localhost:8002/parse
Content-Type: application/json

{
  "repo_path": "/path/to/local/repository",
  "output_path": "/custom/output/graph.json"
}
```

#### 5. **Index Repository to Qdrant**
```
POST http://localhost:8002/index
Content-Type: application/json

{
  "collection_name": "test_repo",
  "qdrant_url": "http://localhost:6333",
  "model_name": "all-MiniLM-L6-v2",
  "graph_path": "data/graph.json",
  "recreate_collection": true
}
```

**Expected Response:**
```json
{
  "success": true,
  "job_id": "index_1695123456",
  "message": "Repository indexing initiated",
  "status": "processing",
  "collection_name": "test_repo",
  "model_name": "all-MiniLM-L6-v2",
  "estimated_time": "60-300 seconds",
  "check_status_url": "/status/index_1695123456"
}
```

#### 6. **Parse and Index (Complete Pipeline)**
```
POST http://localhost:8002/parse-and-index
Content-Type: application/json

{
  "repo_url": "https://github.com/octocat/Hello-World.git",
  "branch": "main",
  "collection_name": "hello_world_repo",
  "qdrant_url": "http://localhost:6333",
  "model_name": "all-MiniLM-L6-v2",
  "recreate_collection": true
}
```

**Expected Response:**
```json
{
  "success": true,
  "job_id": "parse_index_1695123456",
  "message": "Repository parsing and indexing initiated",
  "status": "processing",
  "pipeline": ["clone/load", "parse", "generate_embeddings", "index_to_qdrant"],
  "estimated_time": "120-600 seconds",
  "check_status_url": "/status/parse_index_1695123456"
}
```

---

### 🔍 **Search & Analysis Endpoints**

#### 7. **Semantic Search**
```
POST http://localhost:8002/search
Content-Type: application/json

{
  "query": "hello world function",
  "top_k": 10,
  "collection_name": "test_repo",
  "qdrant_url": "http://localhost:6333"
}
```

**Expected Response:**
```json
{
  "success": true,
  "results": [
    {
      "node_id": "function:hello_world:hello.py:1",
      "score": 0.8945,
      "snippet": "def hello_world():\n    print('Hello, World!')",
      "file": "hello.py",
      "start_line": 1
    }
  ],
  "query": "hello world function",
  "total_results": 5,
  "collection_name": "test_repo"
}
```

#### 8. **Full Analysis**
```
POST http://localhost:8002/analyze
Content-Type: application/json

{
  "query": "payment processing function",
  "top_k": 10,
  "collection_name": "test_repo",
  "qdrant_url": "http://localhost:6333",
  "include_full_graph": false
}
```

**Expected Response:**
```json
{
  "success": true,
  "answer_path": [
    "function:process_payment:payment.py:10",
    "function:validate_payment:utils.py:5"
  ],
  "path_edges": [
    {
      "source": "function:process_payment:payment.py:10",
      "target": "function:validate_payment:utils.py:5",
      "type": "connection"
    }
  ],
  "snippets": [
    {
      "node_id": "function:process_payment:payment.py:10",
      "code": "def process_payment(amount, method):\n    # Payment logic",
      "file": "payment.py",
      "start_line": 10,
      "end_line": 25,
      "doc": "Process payment with given method"
    }
  ],
  "summary": {
    "one_liner": "Analysis of 2 code components related to: payment processing function",
    "steps": [
      "1. process_payment in payment.py: Process payment with given method",
      "2. validate_payment in utils.py: Validate payment details"
    ],
    "inputs_outputs": [
      "Input: User query - 'payment processing function'",
      "Output: Analysis of 2 relevant code components"
    ],
    "caveats": [
      "Analysis based on static code structure and semantic similarity"
    ],
    "node_refs": [
      {
        "node_id": "function:process_payment:payment.py:10",
        "excerpt_line": "def process_payment(amount, method):"
      }
    ]
  },
  "query": "payment processing function",
  "total_results": 2,
  "processing_time": 0.156
}
```

---

### 📊 **Job Management Endpoints**

#### 9. **Get Job Status**
```
GET http://localhost:8002/status/{job_id}
```
Replace `{job_id}` with actual job ID from parse/index responses.

**Example:**
```
GET http://localhost:8002/status/parse_1695123456
```

**Expected Response (Processing):**
```json
{
  "type": "parse",
  "status": "parsing",
  "start_time": "2025-09-21T...",
  "repo_url": "https://github.com/octocat/Hello-World.git",
  "branch": "main"
}
```

**Expected Response (Completed):**
```json
{
  "success": true,
  "job_id": "parse_1695123456",
  "type": "parse",
  "status": "completed",
  "graph_path": "/path/to/graph.json",
  "nodes": 25,
  "edges": 18,
  "stats": {
    "files_processed": 5,
    "functions_found": 20,
    "classes_found": 5,
    "total_nodes": 25,
    "total_edges": 18
  },
  "completion_time": "2025-09-21T...",
  "processing_time": 45.2
}
```

#### 10. **List All Jobs**
```
GET http://localhost:8002/jobs
```

**Expected Response:**
```json
{
  "total_jobs": 3,
  "active_jobs": 1,
  "completed_jobs": 2,
  "failed_jobs": 0,
  "jobs": {
    "parse_1695123456": {
      "type": "parse",
      "status": "completed",
      "start_time": "2025-09-21T...",
      "completion_time": "2025-09-21T..."
    }
  }
}
```

#### 11. **Cancel/Delete Job**
```
DELETE http://localhost:8002/jobs/{job_id}
```

**Example:**
```
DELETE http://localhost:8002/jobs/parse_1695123456
```

**Expected Response:**
```json
{
  "success": true,
  "message": "Job parse_1695123456 removed from tracking",
  "job_id": "parse_1695123456"
}
```

---

### 🗄️ **Qdrant Management Endpoints**

#### 12. **List Qdrant Collections**
```
GET http://localhost:8002/collections
```

**Expected Response:**
```json
{
  "qdrant_url": "http://localhost:6333",
  "total_collections": 2,
  "collections": [
    {
      "name": "test_repo",
      "status": "green",
      "points_count": 150,
      "vector_size": 384,
      "distance": "Cosine"
    },
    {
      "name": "hello_world_repo",
      "status": "green", 
      "points_count": 25,
      "vector_size": 384,
      "distance": "Cosine"
    }
  ]
}
```

---

## 🧪 **Testing Workflow**

### **Recommended Testing Sequence:**

1. **🏥 Health Check**
   ```
   GET /health
   ```

2. **📁 Parse a Repository**
   ```
   POST /parse
   {
     "repo_url": "https://github.com/octocat/Hello-World.git",
     "branch": "main"
   }
   ```

3. **📊 Monitor Job Status**
   ```
   GET /status/{job_id}
   ```
   (Poll until status = "completed")

4. **🗄️ Index to Qdrant**
   ```
   POST /index
   {
     "collection_name": "test_repo",
     "recreate_collection": true
   }
   ```

5. **📊 Monitor Index Job**
   ```
   GET /status/{index_job_id}
   ```

6. **🔍 Test Search**
   ```
   POST /search
   {
     "query": "hello world",
     "collection_name": "test_repo"
   }
   ```

7. **📈 Test Analysis**
   ```
   POST /analyze
   {
     "query": "main function",
     "collection_name": "test_repo"
   }
   ```

8. **📋 List All Jobs**
   ```
   GET /jobs
   ```

9. **🗄️ Check Collections**
   ```
   GET /collections
   ```

---

## 🔧 **Environment Setup**

### **Variables to Set in Postman:**
- `worker_url`: `http://localhost:8002`
- `job_id`: (automatically set by parse requests)

### **Prerequisites:**
1. Worker service running on port 8002
2. Qdrant running on port 6333
3. Internet connection for Git repositories

### **Start Services:**
```bash
cd worker
./start.sh all
```

---

## ❌ **Common Error Responses**

### **Service Unavailable:**
```json
{
  "detail": "Worker service unavailable: Connection refused"
}
```

### **Invalid Request:**
```json
{
  "detail": [
    {
      "loc": ["body", "repo_url"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### **Job Not Found:**
```json
{
  "detail": "Job parse_1695123456 not found"
}
```

### **Qdrant Connection Error:**
```json
{
  "success": false,
  "error": "Failed to connect to Qdrant: Connection refused",
  "results": [],
  "query": "test query",
  "total_results": 0
}
```

---

## 🎯 **Testing Tips**

1. **Start Small**: Use simple repositories like `octocat/Hello-World` for initial testing
2. **Monitor Jobs**: Always check job status for long-running operations
3. **Check Logs**: Watch terminal output for detailed progress information
4. **Test Search**: Only works after successful indexing
5. **Collection Names**: Use unique collection names to avoid conflicts

The Postman collection is ready to import and test all Worker Service endpoints! 🚀
