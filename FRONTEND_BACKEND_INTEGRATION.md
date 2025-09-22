# RepoCanvas Frontend-Backend Integration Guide

## 🚀 Integration Overview

This document outlines the complete integration between the RepoCanvas frontend and backend components, enabling repository analysis, chatbot queries with semantic search, and dynamic graph visualization.

## 📋 Key Features Implemented

### 1. Repository Analysis Integration
- **Frontend**: Repository URL input with analyze button
- **Backend**: `/parse-and-index` endpoint with job-based processing
- **Features**:
  - Real-time job status polling
  - Toast notifications for user feedback
  - Automatic graph data loading after analysis completion

### 2. AI Chatbot with Semantic Search
- **Frontend**: Enhanced chatbot component with real-time responses
- **Backend**: `/ask` endpoint with semantic search and NetworkX path finding
- **Features**:
  - Query processing with code snippet retrieval
  - Dynamic graph path highlighting
  - Detailed response formatting with file paths and function names

### 3. Dynamic Graph Visualization
- **Frontend**: Updated GraphCanvas component with answer path highlighting
- **Backend**: NetworkX-based optimal path computation
- **Features**:
  - Green highlighting for answer path nodes and edges
  - Animated edges for path visualization
  - Real-time graph updates from chatbot queries

## 🔧 Technical Implementation

### API Service Layer (`src/services/api.ts`)
```typescript
// Key functions implemented:
- analyzeRepository(request) // Repository parsing
- queryChatbot(request)     // Semantic search queries
- getGraphData()            // Graph data retrieval
- getJobStatus(jobId)       // Job polling
```

### Frontend Components Updated

#### 1. App.tsx
- Added repository analysis with job polling
- Integrated toast notifications
- Graph data state management
- Backend error handling

#### 2. AIChatbot Component
- Real-time API integration
- Code snippet display formatting
- Graph update callbacks
- Error handling and user feedback

#### 3. GraphCanvas Component
- Answer path highlighting (green nodes/edges)
- Dynamic graph data rendering
- NetworkX path visualization

## 🛠 Setup Instructions

### Prerequisites
1. Backend running on `http://localhost:8000`
2. Worker service configured and running
3. Qdrant vector database running
4. Frontend environment configured

### Environment Configuration
```env
# frontend/.env
VITE_API_URL=http://localhost:8000
```

### Running the Integration
1. Start backend services:
   ```bash
   cd backend
   python app.py
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Test integration using the test file:
   ```bash
   # Open test-integration.html in browser
   # Or visit http://localhost:5173
   ```

## 🔄 Complete User Flow

### 1. Repository Analysis
1. User enters repository URL
2. Clicks "ANALYZE" button
3. Frontend calls `/parse-and-index` endpoint
4. Backend starts parsing job
5. Frontend polls job status every 2 seconds
6. Toast notifications show progress
7. Graph data loads automatically on completion

### 2. Chatbot Interaction
1. User clicks chatbot icon
2. Enters query (e.g., "show me authentication functions")
3. Frontend calls `/ask` endpoint
4. Backend performs semantic search
5. NetworkX computes optimal path through relevant functions
6. Response includes:
   - Code snippets with file paths
   - Dependency path nodes and edges
   - Processing time
7. Graph visualizes answer path with green highlighting

### 3. Graph Visualization
1. Graph displays repository structure
2. Answer paths highlighted in green
3. Animated edges show data flow
4. Click nodes for detailed information
5. Real-time updates from chatbot queries

## 📊 API Endpoints Used

### Backend Endpoints
- `GET /health` - Health check
- `POST /parse-and-index` - Start repository analysis
- `GET /status/{job_id}` - Poll job status
- `POST /ask` - Chatbot query with semantic search
- `GET /graph` - Retrieve graph data
- `POST /search` - Direct semantic search

### Request/Response Examples

#### Repository Analysis
```javascript
// Request
POST /parse-and-index
{
  "repo_url": "https://github.com/user/repo",
  "branch": "main",
  "recreate_collection": true
}

// Response
{
  "success": true,
  "job_id": "12345",
  "message": "Analysis started"
}
```

#### Chatbot Query
```javascript
// Request
POST /ask
{
  "question": "show me authentication functions"
}

// Response
{
  "success": true,
  "query": "show me authentication functions",
  "answer_path": [
    {"id": "auth.ts", "label": "Authentication", "type": "file"},
    {"id": "login", "label": "loginUser", "type": "function"}
  ],
  "path_edges": [
    {"source": "auth.ts", "target": "login", "type": "contains"}
  ],
  "snippets": [
    {
      "node_id": "login",
      "file_path": "src/auth.ts",
      "function_name": "loginUser",
      "code": "function loginUser() { ... }",
      "score": 0.92
    }
  ],
  "processing_time": 1.23
}
```

## 🎯 Testing

### Manual Testing
1. Use the provided `test-integration.html` file
2. Test each component individually:
   - Backend health check
   - Repository analysis
   - Chatbot queries
   - Graph data loading

### Frontend Testing
1. Start development server: `npm run dev`
2. Enter test repository URL
3. Test analyze functionality
4. Open chatbot and test queries
5. Verify graph updates and highlighting

## 🐛 Troubleshooting

### Common Issues
1. **Backend Connection Error**
   - Check if backend is running on port 8000
   - Verify CORS settings in backend

2. **Repository Analysis Fails**
   - Ensure valid GitHub URL format
   - Check worker service is running
   - Verify Qdrant connection

3. **Chatbot No Results**
   - Ensure repository has been analyzed first
   - Check Qdrant collection exists
   - Verify embedding service is working

4. **Graph Not Updating**
   - Check graph data API response
   - Verify GraphCanvas component receives updates
   - Check browser console for errors

### Debug Steps
1. Check browser network tab for API calls
2. Verify backend logs for error messages
3. Use test-integration.html for isolated testing
4. Check toast notifications for user-friendly error messages

## 🚀 Next Steps

### Potential Enhancements
1. **Performance Optimization**
   - Add caching for graph data
   - Implement pagination for large repositories
   - Optimize canvas rendering

2. **User Experience**
   - Add analysis progress indicators
   - Implement query suggestions
   - Add graph export functionality

3. **Advanced Features**
   - Multi-repository comparison
   - Advanced search filters
   - Custom path finding algorithms

## 📝 Files Modified/Created

### Frontend Files
- `src/services/api.ts` - API service layer
- `src/App.tsx` - Main application integration
- `src/components/ai-chatbot.tsx` - Enhanced chatbot
- `src/components/graph-canvas.tsx` - Graph visualization
- `.env` - Environment configuration

### Test Files
- `test-integration.html` - Integration testing page

### Backend Files (Pre-existing)
- `app.py` - Main API endpoints
- `worker/app.py` - Repository processing
- Various supporting modules

The integration is now complete and ready for testing! 🎉