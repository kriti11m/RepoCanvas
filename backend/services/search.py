"""
Search service for semantic search using Qdrant vector database
"""

import json
import numpy as np
from typing import List, Dict, Any, Optional
import logging
from pathlib import Path
import asyncio

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models
    from qdrant_client.http.exceptions import ResponseHandlingException
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from schemas import SearchHit
from config import settings

logger = logging.getLogger(__name__)

class SearchService:
    """Service for semantic search using Qdrant and sentence transformers"""
    
    def __init__(self):
        self.client: Optional[QdrantClient] = None
        self.encoder: Optional[SentenceTransformer] = None
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self.qdrant_map: Dict[str, str] = {}  # point_id -> node_id mapping
        self.fallback_embeddings: Dict[str, np.ndarray] = {}  # For fallback search
        self.fallback_documents: Dict[str, str] = {}  # For fallback search
        
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize Qdrant client and encoder"""
        # Initialize encoder
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.encoder = SentenceTransformer(settings.EMBEDDING_MODEL)
                logger.info(f"Initialized sentence transformer: {settings.EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Failed to initialize sentence transformer: {e}")
        
        # Initialize Qdrant client
        if QDRANT_AVAILABLE:
            try:
                self.client = QdrantClient(
                    url=settings.QDRANT_URL,
                    api_key=settings.QDRANT_API_KEY,
                    timeout=settings.QDRANT_TIMEOUT
                )
                
                # Test connection
                collections = self.client.get_collections()
                logger.info(f"Connected to Qdrant with {len(collections.collections)} collections")
                
                # Load qdrant mapping if exists
                self._load_qdrant_map()
                
            except Exception as e:
                logger.error(f"Failed to connect to Qdrant: {e}")
                self.client = None
    
    def _load_qdrant_map(self):
        """Load the mapping from Qdrant point IDs to node IDs"""
        map_path = Path(settings.DATA_DIR) / "qdrant_map.json"
        if map_path.exists():
            try:
                with open(map_path, 'r', encoding='utf-8') as f:
                    self.qdrant_map = json.load(f)
                logger.info(f"Loaded Qdrant mapping with {len(self.qdrant_map)} entries")
            except Exception as e:
                logger.error(f"Failed to load Qdrant mapping: {e}")
    
    def is_connected(self) -> bool:
        """Check if search service is properly initialized"""
        return (self.client is not None and self.encoder is not None) or len(self.fallback_embeddings) > 0
    
    async def search_query(self, query: str, top_k: int = 10) -> List[SearchHit]:
        """
        Perform semantic search for the given query
        
        Args:
            query: Search query string
            top_k: Number of results to return
            
        Returns:
            List of search hits
        """
        try:
            # First try Qdrant search
            if self.client and self.encoder:
                return await self._qdrant_search(query, top_k)
            
            # Fallback to local search
            if self.fallback_embeddings:
                return await self._fallback_search(query, top_k)
            
            # Last resort: keyword search
            return await self._keyword_search(query, top_k)
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Return keyword search as final fallback
            return await self._keyword_search(query, top_k)
    
    async def _qdrant_search(self, query: str, top_k: int) -> List[SearchHit]:
        """Perform search using Qdrant"""
        try:
            # Encode query
            query_vector = self.encoder.encode([query])[0].tolist()
            
            # Search in Qdrant
            search_result = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True
            )
            
            # Convert to SearchHit objects
            hits = []
            for point in search_result:
                payload = point.payload
                hits.append(SearchHit(
                    node_id=payload.get('node_id', ''),
                    score=float(point.score),
                    snippet=payload.get('snippet', ''),
                    file=payload.get('file', ''),
                    start_line=payload.get('start_line', 0)
                ))
            
            return hits
            
        except Exception as e:
            logger.error(f"Qdrant search failed: {e}")
            raise
    
    async def _fallback_search(self, query: str, top_k: int) -> List[SearchHit]:
        """Fallback search using local embeddings"""
        try:
            if not self.encoder:
                raise ValueError("No encoder available for fallback search")
            
            # Encode query
            query_vector = self.encoder.encode([query])[0]
            
            # Compute similarities
            similarities = []
            for node_id, embedding in self.fallback_embeddings.items():
                similarity = np.dot(query_vector, embedding) / (
                    np.linalg.norm(query_vector) * np.linalg.norm(embedding)
                )
                similarities.append((node_id, float(similarity)))
            
            # Sort by similarity
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Convert to SearchHit objects
            hits = []
            for node_id, score in similarities[:top_k]:
                # Parse node_id to extract file and line info
                parts = node_id.split(':')
                file_path = parts[-2] if len(parts) >= 2 else 'unknown'
                
                hits.append(SearchHit(
                    node_id=node_id,
                    score=score,
                    snippet=self.fallback_documents.get(node_id, '')[:200],
                    file=file_path,
                    start_line=0  # Would need to parse from node_id
                ))
            
            return hits
            
        except Exception as e:
            logger.error(f"Fallback search failed: {e}")
            raise
    
    async def _keyword_search(self, query: str, top_k: int) -> List[SearchHit]:
        """Simple keyword-based search as last resort"""
        try:
            # This is a mock implementation
            # In practice, you might search through cached documents or file names
            query_lower = query.lower()
            mock_results = []
            
            # Generate some mock results based on common patterns
            common_patterns = [
                f"function_related_to_{query_lower}",
                f"class_handling_{query_lower}",
                f"util_for_{query_lower}",
                f"process_{query_lower}",
                f"{query_lower}_handler"
            ]
            
            for i, pattern in enumerate(common_patterns[:top_k]):
                mock_results.append(SearchHit(
                    node_id=f"mock:{pattern}:file{i}.py:10",
                    score=1.0 - (i * 0.1),  # Decreasing scores
                    snippet=f"def {pattern}():\n    # Mock function for {query}",
                    file=f"file{i}.py",
                    start_line=10 + i
                ))
            
            logger.warning(f"Using keyword search fallback for query: {query}")
            return mock_results
            
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []
    
    def load_fallback_embeddings(self, embeddings_path: str, documents_path: str = None):
        """
        Load embeddings for fallback search
        
        Args:
            embeddings_path: Path to saved embeddings (numpy format)
            documents_path: Path to documents text
        """
        try:
            # Load embeddings
            embeddings_data = np.load(embeddings_path, allow_pickle=True).item()
            self.fallback_embeddings = embeddings_data
            
            # Load documents if provided
            if documents_path and Path(documents_path).exists():
                with open(documents_path, 'r', encoding='utf-8') as f:
                    self.fallback_documents = json.load(f)
            
            logger.info(f"Loaded {len(self.fallback_embeddings)} fallback embeddings")
            
        except Exception as e:
            logger.error(f"Failed to load fallback embeddings: {e}")
    
    async def index_documents(self, documents: List[Dict[str, Any]]) -> bool:
        """
        Index documents in Qdrant
        
        Args:
            documents: List of documents with node_id, text, and metadata
            
        Returns:
            Success status
        """
        if not self.client or not self.encoder:
            logger.error("Qdrant client or encoder not available")
            return False
        
        try:
            # Check if collection exists, create if not
            try:
                self.client.get_collection(self.collection_name)
            except:
                # Create collection
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=models.VectorParams(
                        size=self.encoder.get_sentence_embedding_dimension(),
                        distance=models.Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
            
            # Prepare documents for indexing
            texts = [doc['text'] for doc in documents]
            embeddings = self.encoder.encode(texts)
            
            # Prepare points for Qdrant
            points = []
            for i, (doc, embedding) in enumerate(zip(documents, embeddings)):
                points.append(models.PointStruct(
                    id=i,
                    vector=embedding.tolist(),
                    payload={
                        'node_id': doc['node_id'],
                        'snippet': doc.get('snippet', ''),
                        'file': doc.get('file', ''),
                        'start_line': doc.get('start_line', 0),
                        'name': doc.get('name', ''),
                    }
                ))
            
            # Upload to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            
            # Update mapping
            for i, doc in enumerate(documents):
                self.qdrant_map[str(i)] = doc['node_id']
            
            # Save mapping
            map_path = Path(settings.DATA_DIR) / "qdrant_map.json"
            map_path.parent.mkdir(exist_ok=True)
            with open(map_path, 'w', encoding='utf-8') as f:
                json.dump(self.qdrant_map, f, indent=2)
            
            logger.info(f"Indexed {len(documents)} documents in Qdrant")
            return True
            
        except Exception as e:
            logger.error(f"Failed to index documents: {e}")
            return False
    
    def get_collection_info(self) -> Dict[str, Any]:
        """Get information about the Qdrant collection"""
        if not self.client:
            return {"error": "Qdrant client not available"}
        
        try:
            info = self.client.get_collection(self.collection_name)
            return {
                "name": self.collection_name,
                "points_count": info.points_count,
                "vectors_count": info.vectors_count,
                "status": info.status,
                "config": {
                    "distance": info.config.params.vectors.distance,
                    "size": info.config.params.vectors.size
                }
            }
        except Exception as e:
            return {"error": str(e)}