# backend/worker/indexer/embedder.py
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
from typing import List, Optional
import re

MODEL_NAME = "all-MiniLM-L6-v2"

def chunk_text(text: str, max_length: int = 400, overlap: int = 50) -> List[str]:
    """
    Split long text into overlapping chunks for better embedding quality.
    
    Args:
        text (str): Text to chunk
        max_length (int): Maximum chunk length in characters
        overlap (int): Overlap between chunks in characters
    
    Returns:
        List[str]: List of text chunks
    """
    if len(text) <= max_length:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        # Find end position
        end = start + max_length
        
        # If we're not at the end of the text, try to break at word boundaries
        if end < len(text):
            # Look for word boundary within the last 50 characters
            word_break = text.rfind(' ', start + max_length - 50, end)
            if word_break > start:
                end = word_break
            else:
                # Try to break at line boundaries
                line_break = text.rfind('\n', start, end)
                if line_break > start:
                    end = line_break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start position with overlap
        start = end - overlap
        if start >= len(text):
            break
    
    return chunks

def embed_documents(docs: List[str], model_name: str = MODEL_NAME, batch_size: int = 64) -> np.ndarray:
    """
    Generate embeddings for a list of documents using sentence-transformers.
    Handles long documents by chunking and aggregating embeddings.
    
    Args:
        docs (List[str]): List of documents to embed
        model_name (str): Name of the sentence-transformers model
        batch_size (int): Batch size for processing
    
    Returns:
        np.ndarray: Array of embeddings with shape (len(docs), embedding_dim)
    """
    if not docs:
        return np.array([])
    
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Process documents in chunks if they're too long
    processed_docs = []
    doc_chunk_mapping = []  # Maps chunk index to original doc index
    
    print("Processing documents for embedding...")
    for doc_idx, doc in enumerate(docs):
        # Chunk long documents for better embedding quality
        chunks = chunk_text(doc, max_length=400, overlap=50)
        processed_docs.extend(chunks)
        doc_chunk_mapping.extend([doc_idx] * len(chunks))
    
    print(f"Generating embeddings for {len(processed_docs)} chunks from {len(docs)} documents...")
    
    # Generate embeddings in batches
    all_embeddings = []
    for i in tqdm(range(0, len(processed_docs), batch_size), desc="Embedding"):
        batch = processed_docs[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        all_embeddings.append(batch_embeddings)
    
    # Concatenate all embeddings
    chunk_embeddings = np.vstack(all_embeddings)
    
    # Aggregate chunk embeddings back to document embeddings
    # For multiple chunks per document, we'll use mean pooling
    doc_embeddings = []
    for doc_idx in range(len(docs)):
        # Find all chunks for this document
        chunk_indices = [i for i, mapped_doc_idx in enumerate(doc_chunk_mapping) if mapped_doc_idx == doc_idx]
        
        if len(chunk_indices) == 1:
            # Single chunk - use as is
            doc_embeddings.append(chunk_embeddings[chunk_indices[0]])
        else:
            # Multiple chunks - use mean pooling
            chunk_vecs = chunk_embeddings[chunk_indices]
            doc_embedding = np.mean(chunk_vecs, axis=0)
            doc_embeddings.append(doc_embedding)
    
    embeddings = np.array(doc_embeddings)
    print(f"Generated {embeddings.shape[0]} embeddings with dimension {embeddings.shape[1]}")
    
    return embeddings

def get_embedding_dimension(model_name: str = MODEL_NAME) -> int:
    """
    Get the embedding dimension for a given model.
    
    Args:
        model_name (str): Name of the sentence-transformers model
    
    Returns:
        int: Embedding dimension
    """
    model = SentenceTransformer(model_name)
    return model.get_sentence_embedding_dimension()

def embed_documents_simple(docs: List[str], model_name: str = MODEL_NAME, batch_size: int = 64) -> np.ndarray:
    """
    Simple embedding without chunking - for shorter documents.
    
    Args:
        docs (List[str]): List of documents to embed
        model_name (str): Name of the sentence-transformers model
        batch_size (int): Batch size for processing
    
    Returns:
        np.ndarray: Array of embeddings with shape (len(docs), embedding_dim)
    """
    if not docs:
        return np.array([])
    
    model = SentenceTransformer(model_name)
    
    embeddings = []
    for i in tqdm(range(0, len(docs), batch_size), desc="Embedding"):
        batch = docs[i:i+batch_size]
        vecs = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        embeddings.extend(vecs)
    
    return np.array(embeddings)
