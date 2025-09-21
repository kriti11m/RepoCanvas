# RepoCanvas Worker Service

The Worker Service provides HTTP endpoints for repository parsing and embedding indexing functionality. It acts as the parsing and indexing backend for the RepoCanvas system.

## Overview

The Worker Service exposes the following main capabilities:
- **Repository Parsing**: Analyze repository structure and create comprehensive graphs
- **Embedding Generation**: Create semantic embeddings for code components
- **Qdrant Indexing**: Store embeddings in Qdrant vector database for fast retrieval
- **Background Processing**: Handle long-running tasks asynchronously

## API Endpoints

### Health Check
- `GET /` - Root endpoint with service info
- `GET /health` - Health check and service status

### Repository Operations
- `POST /parse` - Parse repository and create graph.json
- `POST /index` - Index existing graph data to Qdrant
- `POST /parse-and-index` - Complete pipeline: parse + index

### Job Management
- `GET /status/{job_id}` - Get job status and results
- `GET /jobs` - List all jobs (active and completed)
- `DELETE /jobs/{job_id}` - Cancel/remove job from tracking

### Qdrant Management
- `GET /collections` - List Qdrant collections and their status

## Quick Start

### 1. Setup
```bash
# Run the setup script
./start.sh setup

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start Services
```bash
# Start Qdrant database
./start.sh qdrant

# Start worker service
./start.sh worker

# Or start both at once
./start.sh all
```

### 3. Test the API
```bash
# Run comprehensive tests
./start.sh test

# Or manually test endpoints
curl http://localhost:8002/health
```

## Usage Examples

### Parse a Repository
```bash
curl -X POST "http://localhost:8002/parse" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/repo.git",
    "branch": "main"
  }'
```

### Index to Qdrant
```bash
curl -X POST "http://localhost:8002/index" \
  -H "Content-Type: application/json" \
  -d '{
    "collection_name": "my_repo",
    "graph_path": "/path/to/graph.json"
  }'
```

### Complete Pipeline
```bash
curl -X POST "http://localhost:8002/parse-and-index" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/user/repo.git",
    "collection_name": "my_repo",
    "model_name": "all-MiniLM-L6-v2"
  }'
```

### Check Job Status
```bash
curl "http://localhost:8002/status/parse_1234567890"
```

## Configuration

### Environment Variables
Create a `.env` file (see `.env.example`):

```bash
# Worker Service Settings
WORKER_HOST=0.0.0.0
WORKER_PORT=8002

# Qdrant Settings
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION_NAME=repocanvas

# Model Settings
MODEL_NAME=all-MiniLM-L6-v2
```

### Docker Deployment
```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or build and run manually
docker build -t repocanvas-worker .
docker run -p 8002:8002 -e QDRANT_URL=http://host.docker.internal:6333 repocanvas-worker
```

## API Reference

### Parse Request
```json
{
  "repo_url": "https://github.com/user/repo.git",  // Optional: Git URL
  "repo_path": "/path/to/local/repo",              // Optional: Local path
  "branch": "main",                                // Git branch (default: main)
  "output_path": "/custom/graph.json"              // Optional: Custom output path
}
```

### Index Request
```json
{
  "collection_name": "my_collection",              // Qdrant collection name
  "qdrant_url": "http://localhost:6333",          // Optional: Qdrant URL
  "model_name": "all-MiniLM-L6-v2",               // Embedding model
  "graph_path": "/path/to/graph.json",            // Optional: Graph file path
  "recreate_collection": true                      // Whether to recreate collection
}
```

### Parse-and-Index Request
```json
{
  "repo_url": "https://github.com/user/repo.git", // Git URL or local path
  "branch": "main",                               // Git branch
  "collection_name": "my_collection",             // Qdrant collection
  "model_name": "all-MiniLM-L6-v2",              // Embedding model
  "recreate_collection": true                     // Recreate collection
}
```

## Supported Languages

The parser supports the following programming languages:
- **Python** (.py) - Full AST parsing with docstrings
- **JavaScript** (.js) - Function and class extraction
- **TypeScript** (.ts) - Enhanced JS parsing with types
- **Java** (.java) - Class and method parsing
- **C++** (.cpp, .c) - Function and class parsing
- **Rust** (.rs) - Function and struct parsing
- **Go** (.go) - Function and struct parsing
- **HTML** (.html) - Element structure parsing
- **CSS** (.css) - Rule and selector parsing

## Backend Integration

The backend service can call these endpoints:

### Parse Integration
```python
# In backend/app.py, update the /parse endpoint:
@app.post("/parse")
async def parse_repository(request: dict):
    worker_url = os.getenv("WORKER_URL", "http://localhost:8002")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(f"{worker_url}/parse", json=request) as response:
            return await response.json()
```

### Search Integration
The Worker service populates Qdrant with embeddings that the backend can query:

```python
# Backend can search the populated Qdrant collection
search_results = qdrant_client.search(
    collection_name="repocanvas",
    query_vector=query_embedding,
    limit=10
)
```

## Performance Considerations

### Repository Size
- **Small repos** (< 100 files): ~30-60 seconds
- **Medium repos** (100-1000 files): ~2-5 minutes  
- **Large repos** (1000+ files): ~5-15 minutes

### Memory Usage
- Base: ~200MB for the service
- Per job: ~50-200MB depending on repository size
- Embeddings: ~4MB per 1000 code nodes

### Embedding Models
- `all-MiniLM-L6-v2`: Fast, 384 dimensions, good quality
- `all-mpnet-base-v2`: Slower, 768 dimensions, better quality
- Custom models supported via sentence-transformers

## Error Handling

The service provides comprehensive error handling:
- **Repository cloning errors**: Invalid URLs, network issues
- **Parsing errors**: Unsupported file types, syntax errors
- **Qdrant errors**: Connection issues, collection problems
- **Memory errors**: Large repository handling

Check job status for detailed error information:
```bash
curl "http://localhost:8002/status/{job_id}"
```

## Monitoring

### Health Checks
```bash
# Service health
curl http://localhost:8002/health

# Qdrant collections
curl http://localhost:8002/collections

# Active jobs
curl http://localhost:8002/jobs
```

### Logs
The service uses structured logging. Check logs for detailed operation info:
```bash
# If running with Docker
docker logs repocanvas_worker

# If running directly
# Logs output to stdout
```

## Troubleshooting

### Common Issues

1. **Qdrant Connection Failed**
   ```bash
   # Check if Qdrant is running
   curl http://localhost:6333/health
   
   # Start Qdrant
   ./start.sh qdrant
   ```

2. **Repository Clone Failed**
   - Check Git URL is accessible
   - Verify branch exists
   - Check network connectivity

3. **Out of Memory**
   - Reduce batch size in embedder
   - Use smaller embedding model
   - Process repositories in chunks

4. **Parsing Errors**
   - Check supported file types
   - Review error logs for syntax issues
   - Verify repository structure

### Getting Help

1. Check the logs for detailed error messages
2. Verify all dependencies are installed
3. Test with a small, simple repository first
4. Check Qdrant connectivity and status

## Development

### Project Structure
```
worker/
├── app.py                 # FastAPI application
├── parse_repo.py         # Core parsing logic
├── requirements.txt      # Python dependencies
├── Dockerfile           # Container configuration
├── docker-compose.yml   # Multi-service setup
├── start.sh            # Setup and startup script
├── test_worker_api.py  # API test suite
├── parser/             # Parsing modules
│   ├── ts_parser.py    # Tree-sitter integration
│   └── utils.py        # Utilities (git, etc.)
└── indexer/            # Embedding modules
    ├── embedder.py     # Sentence transformers
    └── qdrant_client.py # Qdrant integration
```

### Contributing

1. Follow the existing code structure
2. Add comprehensive error handling
3. Include tests for new functionality
4. Update documentation for API changes
5. Use type hints for better maintainability

### Testing

```bash
# Run full test suite
./start.sh test

# Run specific tests
python test_worker_api.py

# Test individual endpoints
pytest tests/ -v
```
