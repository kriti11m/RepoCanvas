# backend/worker/indexer/embedder.py
from sentence_transformers import SentenceTransformer
import numpy as np
from tqdm import tqdm
from typing import List, Optional, Dict
import re

MODEL_NAME = "all-MiniLM-L6-v2"

# Language-specific context for better embeddings
LANGUAGE_CONTEXTS = {
    'python': {
        'keywords': ['def', 'class', 'import', 'from', 'return', 'if', 'for', 'while'],
        'file_types': ['.py'],
        'comment_style': '#',
        'doc_style': '"""'
    },
    'javascript': {
        'keywords': ['function', 'class', 'import', 'export', 'const', 'let', 'var', 'return'],
        'file_types': ['.js', '.jsx'],
        'comment_style': '//',
        'doc_style': '/**'
    },
    'typescript': {
        'keywords': ['function', 'class', 'interface', 'type', 'import', 'export', 'const', 'let'],
        'file_types': ['.ts', '.tsx'],
        'comment_style': '//',
        'doc_style': '/**'
    },
    'java': {
        'keywords': ['public', 'private', 'class', 'interface', 'method', 'import', 'package'],
        'file_types': ['.java'],
        'comment_style': '//',
        'doc_style': '/**'
    },
    'cpp': {
        'keywords': ['class', 'namespace', 'template', 'public', 'private', 'include'],
        'file_types': ['.cpp', '.cc', '.cxx', '.h', '.hpp'],
        'comment_style': '//',
        'doc_style': '/**'
    },
    'go': {
        'keywords': ['func', 'package', 'import', 'type', 'struct', 'interface'],
        'file_types': ['.go'],
        'comment_style': '//',
        'doc_style': '/**'
    },
    'rust': {
        'keywords': ['fn', 'struct', 'impl', 'trait', 'use', 'mod', 'pub'],
        'file_types': ['.rs'],
        'comment_style': '//',
        'doc_style': '///'
    },
    'c': {
        'keywords': ['struct', 'typedef', 'include', 'static', 'extern'],
        'file_types': ['.c', '.h'],
        'comment_style': '//',
        'doc_style': '/**'
    }
}

def detect_language_from_extension(file_path: str) -> str:
    """Detect programming language from file extension."""
    if not file_path:
        return 'unknown'
    
    extension = '.' + file_path.split('.')[-1].lower()
    
    for lang, context in LANGUAGE_CONTEXTS.items():
        if extension in context['file_types']:
            return lang
    
    return 'unknown'

def enhance_code_document(text: str, language: str, node_metadata: Dict = None) -> str:
    """
    Enhance code document with language-specific context for better embeddings.
    
    Args:
        text (str): Original code document
        language (str): Programming language
        node_metadata (Dict): Additional metadata about the code node
    
    Returns:
        str: Enhanced document with language context
    """
    if language not in LANGUAGE_CONTEXTS:
        return text
    
    lang_context = LANGUAGE_CONTEXTS[language]
    
    # Add language identifier
    enhanced = f"[{language.upper()} CODE]\n"
    
    # Add file type context
    if node_metadata and 'file' in node_metadata:
        file_ext = '.' + node_metadata['file'].split('.')[-1]
        enhanced += f"File type: {file_ext}\n"
    
    # Add function/class type context
    if node_metadata:
        node_id = node_metadata.get('id', '').lower()
        if 'function' in node_id or 'def' in node_id or 'func' in node_id:
            enhanced += f"Code type: Function definition in {language}\n"
        elif 'class' in node_id:
            enhanced += f"Code type: Class definition in {language}\n"
        elif 'import' in node_id:
            enhanced += f"Code type: Import statement in {language}\n"
    
    # Add the original text
    enhanced += text
    
    # Add language-specific keywords context
    code_lines = text.lower().split('\n')
    found_keywords = []
    for line in code_lines[:5]:  # Check first 5 lines
        for keyword in lang_context['keywords']:
            if keyword in line:
                found_keywords.append(keyword)
    
    if found_keywords:
        enhanced += f"\nLanguage patterns: {', '.join(set(found_keywords))}"
    
    return enhanced

def chunk_text(text: str, max_length: int = 400, overlap: int = 50) -> List[str]:
    """
    Split long text into overlapping chunks for better embedding quality.
    Now handles code-specific chunking patterns.
    
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
        
        # If we're not at the end of the text, try to break at code boundaries first
        if end < len(text):
            # For code, prioritize breaking at function/class boundaries
            code_boundaries = [
                text.rfind('\ndef ', start, end),
                text.rfind('\nclass ', start, end),
                text.rfind('\nfunction ', start, end),
                text.rfind('\npublic ', start, end),
                text.rfind('\nprivate ', start, end),
                text.rfind('\nfunc ', start, end),  # Go functions
                text.rfind('\nfn ', start, end),   # Rust functions
            ]
            
            # Find the best boundary
            best_boundary = max([b for b in code_boundaries if b > start], default=-1)
            
            if best_boundary > start:
                end = best_boundary
            else:
                # Fallback to word boundaries
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

def embed_documents(docs: List[str], model_name: str = MODEL_NAME, batch_size: int = 64, 
                   language_contexts: List[str] = None, node_metadata: List[Dict] = None) -> np.ndarray:
    """
    Generate embeddings for a list of documents using sentence-transformers.
    Enhanced for multi-language code documents.
    
    Args:
        docs (List[str]): List of documents to embed
        model_name (str): Name of the sentence-transformers model
        batch_size (int): Batch size for processing
        language_contexts (List[str]): Programming languages for each document
        node_metadata (List[Dict]): Metadata for each code node
    
    Returns:
        np.ndarray: Array of embeddings with shape (len(docs), embedding_dim)
    """
    if not docs:
        return np.array([])
    
    print(f"Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)
    
    # Enhanced document processing with language context
    processed_docs = []
    doc_chunk_mapping = []
    
    print(f"Processing {len(docs)} documents for embedding (multi-language support)...")
    
    for doc_idx, doc in enumerate(docs):
        # Get language context if available
        language = 'unknown'
        metadata = {}
        
        if language_contexts and doc_idx < len(language_contexts):
            language = language_contexts[doc_idx]
        
        if node_metadata and doc_idx < len(node_metadata):
            metadata = node_metadata[doc_idx]
            # Try to detect language from file extension in metadata
            if 'file' in metadata and language == 'unknown':
                language = detect_language_from_extension(metadata['file'])
        
        # Enhance document with language context
        enhanced_doc = enhance_code_document(doc, language, metadata)
        
        # Chunk the enhanced document
        chunks = chunk_text(enhanced_doc, max_length=400, overlap=50)
        processed_docs.extend(chunks)
        doc_chunk_mapping.extend([doc_idx] * len(chunks))
    
    print(f"Enhanced documents with language context. Generating embeddings for {len(processed_docs)} chunks...")
    
    # Generate embeddings in batches
    all_embeddings = []
    for i in tqdm(range(0, len(processed_docs), batch_size), desc="Embedding"):
        batch = processed_docs[i:i + batch_size]
        batch_embeddings = model.encode(batch, convert_to_numpy=True, show_progress_bar=False)
        all_embeddings.append(batch_embeddings)
    
    # Concatenate all embeddings
    chunk_embeddings = np.vstack(all_embeddings)
    
    # Aggregate chunk embeddings back to document embeddings
    doc_embeddings = []
    for doc_idx in range(len(docs)):
        chunk_indices = [i for i, mapped_doc_idx in enumerate(doc_chunk_mapping) if mapped_doc_idx == doc_idx]
        
        if len(chunk_indices) == 1:
            doc_embeddings.append(chunk_embeddings[chunk_indices[0]])
        else:
            # Multiple chunks - use mean pooling
            chunk_vecs = chunk_embeddings[chunk_indices]
            doc_embedding = np.mean(chunk_vecs, axis=0)
            doc_embeddings.append(doc_embedding)
    
    embeddings = np.array(doc_embeddings)
    print(f"Generated {embeddings.shape[0]} embeddings with dimension {embeddings.shape[1]} for multiple programming languages")
    
    return embeddings

def create_multilingual_document(node: Dict) -> str:
    """
    Create an enhanced document from a code node with multi-language awareness.
    
    Args:
        node (Dict): Code node with metadata
    
    Returns:
        str: Enhanced document string
    """
    # Detect language from file extension
    language = detect_language_from_extension(node.get('file', ''))
    
    # Extract function signature if available
    code = node.get('code', '')
    signature = ""
    
    # Language-specific signature extraction
    if language == 'python' and 'def ' in code:
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('def '):
                signature = line.strip()
                break
    elif language in ['javascript', 'typescript'] and 'function' in code:
        lines = code.split('\n')
        for line in lines:
            if 'function' in line or '=>' in line:
                signature = line.strip()
                break
    elif language == 'java' and any(keyword in code for keyword in ['public', 'private', 'protected']):
        lines = code.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['public', 'private', 'protected']) and '(' in line:
                signature = line.strip()
                break
    elif language == 'go' and 'func ' in code:
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('func '):
                signature = line.strip()
                break
    elif language == 'rust' and 'fn ' in code:
        lines = code.split('\n')
        for line in lines:
            if line.strip().startswith('fn '):
                signature = line.strip()
                break
    elif language in ['cpp', 'c'] and any(keyword in code for keyword in ['class', 'struct', 'template']):
        lines = code.split('\n')
        for line in lines:
            if any(keyword in line for keyword in ['class', 'struct', 'template']) and '{' in line:
                signature = line.strip()
                break
    
    # Create comprehensive document
    doc_parts = [
        f"Programming Language: {language}",
        f"Component: {node.get('name', 'unknown')}",
        f"File: {node.get('file', 'unknown')}",
        f"Location: Lines {node.get('start_line', 0)}-{node.get('end_line', 0)}"
    ]
    
    if signature:
        doc_parts.append(f"Signature: {signature}")
    
    if node.get('doc'):
        doc_parts.append(f"Documentation: {node['doc']}")
    
    # Add code with truncation for very long functions
    code_snippet = code[:800] + "..." if len(code) > 800 else code
    doc_parts.append(f"Source Code:\n{code_snippet}")
    
    # Add complexity metrics if available
    if node.get('cyclomatic'):
        doc_parts.append(f"Complexity: {node['cyclomatic']}")
    
    if node.get('num_calls_out') is not None:
        doc_parts.append(f"Function calls: {node['num_calls_out']} outgoing, {node.get('num_calls_in', 0)} incoming")
    
    return '\n'.join(doc_parts)

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
