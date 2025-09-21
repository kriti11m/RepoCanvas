# RepoCanvas Backend

FastAPI backend service for repository analysis and graph visualization.

## Features

- **Repository Parsing**: Parse repositories and build dependency graphs
- **Semantic Search**: Search code using vector embeddings via Qdrant
- **Graph Analysis**: Find paths between code components using NetworkX
- **AI Summarization**: Generate natural language summaries of code flows
- **REST API**: Clean REST endpoints for frontend integration

## Quick Start

### Prerequisites

- Python 3.10+
- Qdrant (optional, runs in fallback mode without it)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create environment configuration:
```bash
python config.py create-env
```

3. Edit `.env` file with your settings (Qdrant URL, API keys, etc.)

4. Validate configuration:
```bash
python config.py validate
```

5. Run the server:
```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

## Configuration

Key environment variables:

- `QDRANT_URL`: Qdrant vector database URL (default: http://localhost:6333)
- `QDRANT_API_KEY`: Qdrant API key (optional)
- `SUMMARIZER_URL`: AI summarizer service URL (optional)
- `OPENAI_API_KEY`: OpenAI API key for direct integration (optional)
- `DATA_DIR`: Directory for graph data (default: ./data)

## API Endpoints

### Core Endpoints

- `POST /parse` - Parse a repository and create graph
- `GET /graph` - Get the loaded graph
- `POST /search` - Semantic search for code nodes
- `POST /analyze` - Full analysis: search + pathfinding + summarization
- `POST /summarize` - Generate code summary
- `GET /health` - Health check

### Development Endpoints

- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API docs

## Architecture

```
backend/
├── app.py              # Main FastAPI application
├── config.py           # Configuration management
├── schemas.py          # Pydantic models
├── requirements.txt    # Dependencies
├── services/
│   ├── graph.py        # Graph loading and pathfinding
│   ├── search.py       # Qdrant search wrapper
│   └── summarizer_proxy.py  # AI summarizer interface
├── parser/             # Repository parsing (future)
├── indexer/            # Embedding generation (future)
└── data/               # Graph and embedding data
```

## Fallback Modes

The backend is designed to gracefully degrade:

1. **No Qdrant**: Falls back to keyword search or cached embeddings
2. **No Summarizer**: Uses heuristic-based summaries
3. **No Graph**: Returns empty results with appropriate errors

## Development

### Running Tests
```bash
pytest
```

### Development Mode
```bash
uvicorn app:app --reload --log-level debug
```

### Environment Setup
```bash
# Create development environment
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Integration

This backend is designed to work with:

- **Worker**: Repository parsing and graph generation service
- **AI Summarizer**: LLM-based code summarization service  
- **Frontend**: React application with graph visualization

## Example Usage

```python
import requests

# Parse a repository
response = requests.post("http://localhost:8000/parse", json={
    "repo_url": "https://github.com/user/repo",
    "branch": "main"
})

# Search for payment-related code
response = requests.post("http://localhost:8000/search", json={
    "query": "payment processing",
    "top_k": 10
})

# Full analysis with pathfinding and summary
response = requests.post("http://localhost:8000/analyze", json={
    "query": "how does user authentication work?",
    "top_k": 5,
    "include_full_graph": False
})
```

## Deployment

### Docker (Recommended)
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Manual Deployment
1. Install dependencies
2. Set environment variables
3. Run with production server: `uvicorn app:app --host 0.0.0.0 --port 8000`

## Monitoring

Health check endpoint provides service status:
```bash
curl http://localhost:8000/health
```

Returns status of all components (graph, search, summarizer).