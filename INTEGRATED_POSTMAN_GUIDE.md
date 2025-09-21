# RepoCanvas Integrated Backend API - Postman Testing Guide

## 🚀 **System Architecture**
```
📱 Postman/Frontend → 🌐 Backend (8000) → 🔧 Worker (8002)
                                       ↘ 🤖 Summarizer (8001)
```

**Backend serves as orchestration layer - you test backend endpoints, they call worker internally!**

---

## 🔧 **Postman Setup**

1. **Base URL**: `http://localhost:8000` (Backend, NOT Worker!)
2. **Content-Type**: `application/json` for all POST requests
3. **Services Running**:
   - ✅ Backend: `http://localhost:8000`
   - ✅ Worker: `http://localhost:8002` 
   - ✅ Summarizer: `http://localhost:8001` (optional)

---

# 📋 **All Integrated Endpoints to Test**

## 🏥 **1. Health & Info Endpoints**

### **Root Endpoint**
```
GET http://localhost:8000/
```
**Response**: API info with service URLs

### **Detailed API Info**
```
GET http://localhost:8000/info
```
**Response**: Complete architecture details

### **Health Check (Critical!)**
```
GET http://localhost:8000/health
```
**Expected Response**:
```json
{
  "status": "healthy",
  "timestamp": 1695123456,
  "services": {
    "qdrant": true,
    "graph": true,
    "worker": true,
    "summarizer": true
  },
  "messages": {
    "worker": "Worker is healthy",
    "summarizer": "Summarizer is healthy"
  }
}
```

---

## 📁 **2. Repository Operations (Backend → Worker)**

### **Parse Repository**
```
POST http://localhost:8000/parse
Content-Type: application/json

{
  "repo_url": "https://github.com/octocat/Hello-World.git",
  "branch": "main"
}
```
**Flow**: Backend `/parse` → Worker `/parse`

### **Parse and Index Repository**
```
POST http://localhost:8000/parse-and-index
Content-Type: application/json

{
  "repo_url": "https://github.com/octocat/Hello-World.git",
  "branch": "main"
}
```
**Flow**: Backend `/parse-and-index` → Worker `/parse-and-index`

### **Index Repository**
```
POST http://localhost:8000/index
Content-Type: application/json

{
  "collection_name": "test_repo",
  "qdrant_url": "http://localhost:6333",
  "graph_path": "data/graph.json",
  "recreate_collection": true
}
```
**Flow**: Backend `/index` → Worker `/index`

---

## 🔍 **3. Search & Analysis (Backend → Worker + Summarizer)**

### **Semantic Search**
```
POST http://localhost:8000/search
Content-Type: application/json

{
  "query": "user authentication function",
  "top_k": 5
}
```
**Flow**: Backend `/search` → Worker `/search` → Fallback if worker fails

### **Complete Analysis (Most Important!)**
```
POST http://localhost:8000/analyze
Content-Type: application/json

{
  "query": "how does authentication work",
  "top_k": 3,
  "include_summary": true
}
```
**Flow**: Backend `/analyze` → Worker `/analyze` → Summarizer `/summarize`

**Expected Response**:
```json
{
  "success": true,
  "query": "how does authentication work",
  "answer_path": ["function:auth:auth.py:10"],
  "path_edges": [],
  "snippets": [
    {
      "node_id": "function:auth:auth.py:10",
      "code": "def authenticate_user(...):",
      "file": "auth.py"
    }
  ],
  "worker_summary": {...},
  "ai_summary": {
    "one_liner": "Authentication system overview",
    "steps": ["1. User login", "2. Token validation"]
  },
  "processing_time": 0.25
}
```

### **Simple Ask Endpoint**
```
POST http://localhost:8000/ask
Content-Type: application/json

{
  "question": "How do I authenticate users?",
  "top_k": 3
}
```
**Flow**: Backend `/ask` → internally calls `analyze` → Worker + Summarizer

---

## 📊 **4. Job Management (Backend → Worker)**

### **Get Job Status**
```
GET http://localhost:8000/status/{job_id}
```
Replace `{job_id}` with actual job ID from parse responses.

### **List All Jobs**
```
GET http://localhost:8000/jobs
```

### **Delete Job**
```
DELETE http://localhost:8000/jobs/{job_id}
```

---

## 🧪 **5. Testing Scenarios**

### **Scenario 1: Complete Pipeline Test**
1. **Health Check**: `GET /health` - Verify all services running
2. **Parse Repo**: `POST /parse-and-index` - Start processing
3. **Check Status**: `GET /status/{job_id}` - Monitor progress  
4. **Search**: `POST /search` - Test semantic search
5. **Analyze**: `POST /analyze` - Full analysis with AI

### **Scenario 2: Service Failure Testing**
1. Stop worker service
2. Test `POST /search` - Should use fallback
3. Test `POST /analyze` - Should handle gracefully

### **Scenario 3: Frontend Integration Test**
1. **Ask Question**: `POST /ask` with user question
2. **Verify Response**: Check snippets and AI summary
3. **Search Follow-up**: `POST /search` with related query

---

## 🚨 **Error Handling**

### **Worker Service Down**
```json
{
  "detail": "Worker service unavailable: Connection refused"
}
```

### **Summarizer Service Down**
```json
{
  "ai_summary": {
    "error": "Summarizer service unavailable",
    "fallback": true,
    "one_liner": "Analysis completed without AI summary"
  }
}
```

---

## 🎯 **Quick Test Collection**

**Import this JSON into Postman:**

```json
{
  "info": {
    "name": "RepoCanvas Integrated Backend",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "backend_url",
      "value": "http://localhost:8000"
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{backend_url}}/health"
      }
    },
    {
      "name": "Analyze Query",
      "request": {
        "method": "POST",
        "url": "{{backend_url}}/analyze",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"query\": \"user authentication\",\n  \"top_k\": 3,\n  \"include_summary\": true\n}"
        }
      }
    },
    {
      "name": "Ask Question",
      "request": {
        "method": "POST",
        "url": "{{backend_url}}/ask",
        "header": [
          {
            "key": "Content-Type",
            "value": "application/json"
          }
        ],
        "body": {
          "mode": "raw",
          "raw": "{\n  \"question\": \"How does authentication work?\"\n}"
        }
      }
    }
  ]
}
```

---

## ✅ **Testing Checklist**

- [ ] Backend health shows all services healthy
- [ ] Parse endpoints return job IDs
- [ ] Search returns relevant results  
- [ ] Analyze includes both worker + AI summaries
- [ ] Ask endpoint works for user questions
- [ ] Error handling works when services down
- [ ] Job management endpoints functional

**🎉 Success Criteria**: All endpoints return 200 OK with expected JSON structure!