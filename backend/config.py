"""
Configuration management for RepoCanvas Backend
"""

import os
from typing import List, Optional
from pathlib import Path
import logging

class Settings:
    """Application settings loaded from environment variables"""
    
    def __init__(self):
        # Server settings
        self.HOST: str = os.getenv("HOST", "0.0.0.0")
        self.PORT: int = int(os.getenv("PORT", "8000"))
        self.DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
        
        # CORS settings
        self.ALLOWED_ORIGINS: List[str] = self._parse_list(
            os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5173")
        )
        
        # Qdrant settings
        self.QDRANT_URL: str = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.QDRANT_API_KEY: Optional[str] = os.getenv("QDRANT_API_KEY")
        self.QDRANT_COLLECTION_NAME: str = os.getenv("QDRANT_COLLECTION_NAME", "repocanvas")
        self.QDRANT_TIMEOUT: int = int(os.getenv("QDRANT_TIMEOUT", "30"))
        
        # Embedding settings
        self.EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        
        # Worker service settings
        self.WORKER_URL: str = os.getenv("WORKER_URL", "http://localhost:8002")
        self.WORKER_TIMEOUT: int = int(os.getenv("WORKER_TIMEOUT", "1800"))  # 30 minutes for large repos
        
        # Summarizer settings
        self.SUMMARIZER_URL: str = os.getenv("SUMMARIZER_URL", "http://localhost:8001")
        self.SUMMARIZER_TIMEOUT: int = int(os.getenv("SUMMARIZER_TIMEOUT", "30"))
        
        # OpenAI settings (if using direct OpenAI integration)
        self.OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
        self.OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        
        # Data directories
        self.DATA_DIR: str = os.getenv("DATA_DIR", str(Path(__file__).parent.parent / "data"))
        self.DEFAULT_GRAPH_PATH: str = os.getenv(
            "DEFAULT_GRAPH_PATH", 
            str(Path(self.DATA_DIR) / "graph.json")
        )
        
        # Logging
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO" if not self.DEBUG else "DEBUG")
        
        # Performance settings
        self.MAX_WORKERS: int = int(os.getenv("MAX_WORKERS", "4"))
        self.CACHE_SIZE: int = int(os.getenv("CACHE_SIZE", "1000"))
        
        # Create data directory if it doesn't exist
        Path(self.DATA_DIR).mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
    
    def _parse_list(self, value: str) -> List[str]:
        """Parse comma-separated string into list"""
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]
    
    def _setup_logging(self):
        """Configure logging"""
        logging.basicConfig(
            level=getattr(logging, self.LOG_LEVEL.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of warnings/errors"""
        warnings = []
        
        # Check critical settings
        if not self.QDRANT_URL:
            warnings.append("QDRANT_URL not set - search will use fallback mode")
        
        if not self.SUMMARIZER_URL and not self.OPENAI_API_KEY:
            warnings.append("No summarizer configured - will use fallback summaries")
        
        # Check data directory
        if not os.path.exists(self.DATA_DIR):
            warnings.append(f"Data directory does not exist: {self.DATA_DIR}")
        
        # Check graph file
        if not os.path.exists(self.DEFAULT_GRAPH_PATH):
            warnings.append(f"Default graph file not found: {self.DEFAULT_GRAPH_PATH}")
        
        return warnings
    
    def get_summary(self) -> dict:
        """Get configuration summary"""
        return {
            "server": {
                "host": self.HOST,
                "port": self.PORT,
                "debug": self.DEBUG
            },
            "qdrant": {
                "url": self.QDRANT_URL,
                "collection": self.QDRANT_COLLECTION_NAME,
                "configured": bool(self.QDRANT_URL)
            },
            "worker": {
                "url": self.WORKER_URL,
                "configured": bool(self.WORKER_URL)
            },
            "summarizer": {
                "url": self.SUMMARIZER_URL,
                "openai_configured": bool(self.OPENAI_API_KEY),
                "configured": bool(self.SUMMARIZER_URL or self.OPENAI_API_KEY)
            },
            "data": {
                "data_dir": self.DATA_DIR,
                "graph_path": self.DEFAULT_GRAPH_PATH,
                "graph_exists": os.path.exists(self.DEFAULT_GRAPH_PATH)
            }
        }

# Global settings instance
settings = Settings()

# Environment template for .env file
ENV_TEMPLATE = """# RepoCanvas Backend Configuration

# Server Settings
HOST=0.0.0.0
PORT=8000
DEBUG=false

# CORS Settings (comma-separated)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=
QDRANT_COLLECTION_NAME=repocanvas
QDRANT_TIMEOUT=30

# Embedding Model
EMBEDDING_MODEL=all-MiniLM-L6-v2

# Worker Service (Repository Analysis)
WORKER_URL=http://localhost:8002
WORKER_TIMEOUT=60

# AI Summarizer Service
SUMMARIZER_URL=http://localhost:8001
SUMMARIZER_TIMEOUT=30

# OpenAI (alternative to summarizer service)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# Data Paths
DATA_DIR=./data
DEFAULT_GRAPH_PATH=./data/graph.json

# Logging
LOG_LEVEL=INFO

# Performance
MAX_WORKERS=4
CACHE_SIZE=1000
"""

def create_env_file(path: str = ".env") -> None:
    """Create a .env file with default configuration"""
    if not os.path.exists(path):
        with open(path, 'w', encoding='utf-8') as f:
            f.write(ENV_TEMPLATE)
        print(f"Created {path} with default configuration")
    else:
        print(f"{path} already exists")

def validate_environment() -> None:
    """Validate current environment and print warnings"""
    warnings = settings.validate()
    
    if warnings:
        print("Configuration Warnings:")
        for warning in warnings:
            print(f"  ⚠️  {warning}")
    else:
        print("✅ Configuration validated successfully")
    
    print(f"\nConfiguration Summary:")
    summary = settings.get_summary()
    for category, values in summary.items():
        print(f"  {category.title()}:")
        for key, value in values.items():
            print(f"    {key}: {value}")

if __name__ == "__main__":
    # Command line usage for configuration management
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "create-env":
            create_env_file()
        elif sys.argv[1] == "validate":
            validate_environment()
        else:
            print("Usage: python config.py [create-env|validate]")
    else:
        validate_environment()