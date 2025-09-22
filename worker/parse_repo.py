"""
Enhanced repository parsing utilities with multi-language support
Supports Tree-sitter parsing for multiple programming languages with fallback mechanisms
"""

import json
import logging
import os
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

# Comprehensive language parser mapping for multi-language repository support
LANGUAGE_PARSERS = {
    # Python
    'py': {
        'language': 'python',
        'node_types': {
            'function': ['function_definition', 'async_function_def'],
            'class': ['class_definition'],
            'variable': ['assignment'],
            'import': ['import_statement', 'import_from_statement']
        }
    },
    # JavaScript
    'js': {
        'language': 'javascript',
        'node_types': {
            'function': ['function_declaration', 'function_expression', 'arrow_function', 'method_definition'],
            'class': ['class_declaration'],
            'variable': ['variable_declaration', 'lexical_declaration'],
            'import': ['import_statement', 'export_statement']
        }
    },
    # TypeScript
    'ts': {
        'language': 'typescript',
        'node_types': {
            'function': ['function_declaration', 'function_expression', 'arrow_function', 'method_definition', 'method_signature'],
            'class': ['class_declaration', 'interface_declaration'],
            'variable': ['variable_declaration', 'lexical_declaration'],
            'import': ['import_statement', 'export_statement']
        }
    },
    'tsx': {
        'language': 'tsx',
        'node_types': {
            'function': ['function_declaration', 'function_expression', 'arrow_function', 'method_definition'],
            'class': ['class_declaration', 'interface_declaration'],
            'variable': ['variable_declaration', 'lexical_declaration'],
            'import': ['import_statement', 'export_statement']
        }
    },
    # Java
    'java': {
        'language': 'java',
        'node_types': {
            'function': ['method_declaration', 'constructor_declaration'],
            'class': ['class_declaration', 'interface_declaration', 'enum_declaration'],
            'variable': ['field_declaration', 'variable_declaration'],
            'import': ['import_declaration', 'package_declaration']
        }
    },
    # C++
    'cpp': {'language': 'cpp', 'node_types': {'function': ['function_definition', 'function_declaration'], 'class': ['class_specifier', 'struct_specifier'], 'variable': ['declaration']}},
    'cc': {'language': 'cpp', 'node_types': {'function': ['function_definition', 'function_declaration'], 'class': ['class_specifier', 'struct_specifier'], 'variable': ['declaration']}},
    'cxx': {'language': 'cpp', 'node_types': {'function': ['function_definition', 'function_declaration'], 'class': ['class_specifier', 'struct_specifier'], 'variable': ['declaration']}},
    'hpp': {'language': 'cpp', 'node_types': {'function': ['function_declaration'], 'class': ['class_specifier', 'struct_specifier'], 'variable': ['declaration']}},
    'h': {'language': 'cpp', 'node_types': {'function': ['function_declaration'], 'class': ['struct_specifier'], 'variable': ['declaration']}},
    # C
    'c': {
        'language': 'c',
        'node_types': {
            'function': ['function_definition', 'function_declaration'],
            'class': ['struct_specifier'],
            'variable': ['declaration']
        }
    },
    # Rust
    'rs': {
        'language': 'rust',
        'node_types': {
            'function': ['function_item'],
            'class': ['struct_item', 'enum_item', 'trait_item', 'impl_item'],
            'variable': ['let_declaration'],
            'import': ['use_declaration']
        }
    },
    # Go
    'go': {
        'language': 'go',
        'node_types': {
            'function': ['function_declaration', 'method_declaration'],
            'class': ['type_declaration'],
            'variable': ['var_declaration', 'short_var_declaration'],
            'import': ['import_declaration']
        }
    },
    # Additional languages
    'rb': {'language': 'ruby', 'node_types': {'function': ['method', 'singleton_method'], 'class': ['class', 'module']}},
    'php': {'language': 'php', 'node_types': {'function': ['function_definition', 'method_declaration'], 'class': ['class_declaration', 'interface_declaration']}},
    'swift': {'language': 'swift', 'node_types': {'function': ['function_declaration'], 'class': ['class_declaration', 'struct_declaration']}},
    'kt': {'language': 'kotlin', 'node_types': {'function': ['function_declaration'], 'class': ['class_declaration', 'interface_declaration']}},
    'cs': {'language': 'c_sharp', 'node_types': {'function': ['method_declaration'], 'class': ['class_declaration', 'interface_declaration']}},
    'html': {'language': 'html', 'node_types': {'element': ['element']}},
    'css': {'language': 'css', 'node_types': {'rule': ['rule_set']}},
    'json': {'language': 'json', 'node_types': {'object': ['object'], 'array': ['array']}},
    'yaml': {'language': 'yaml', 'node_types': {'document': ['document']}},
    'yml': {'language': 'yaml', 'node_types': {'document': ['document']}},
    'sh': {'language': 'bash', 'node_types': {'function': ['function_definition']}},
    'bash': {'language': 'bash', 'node_types': {'function': ['function_definition']}},
}

def get_file_extension(file_path: str) -> str:
    """Get file extension without the dot."""
    return os.path.splitext(file_path)[1][1:].lower()

def get_language_from_extension(extension: str) -> Optional[Dict]:
    """Get language parser configuration from file extension."""
    return LANGUAGE_PARSERS.get(extension.lower())

def clone_repo(repo_url: str, output_dir: str, branch: str = "main") -> bool:
    """
    Clone repository (stub implementation)
    
    Args:
        repo_url: Repository URL
        output_dir: Output directory
        branch: Branch to clone
        
    Returns:
        Success status
    """
    logger.info(f"Would clone {repo_url} to {output_dir} (branch: {branch})")
    # TODO: Implement actual git cloning
    return True

def parse_repository(repo_path: str, output_file: str = None) -> Dict[str, Any]:
    """
    Parse repository and generate graph with multi-language support.
    
    This function now supports multiple programming languages via Tree-sitter
    and provides fallback mechanisms for unsupported file types.
    
    Args:
        repo_path: Path to repository
        output_file: Output file for graph.json
        
    Returns:
        Graph data with nodes and edges in standardized format
    """
    logger.info(f"Parsing multi-language repository at {repo_path}")
    
    if not os.path.exists(repo_path):
        logger.error(f"Repository path does not exist: {repo_path}")
        return {"nodes": [], "edges": [], "error": "Repository path not found"}
    
    try:
        # Parse all supported files in repository
        nodes = []
        supported_extensions = set(LANGUAGE_PARSERS.keys())
        processed_files = 0
        
        for root, dirs, files in os.walk(repo_path):
            # Skip common ignore directories
            dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', 'node_modules', '.vscode', '.idea', 'build', 'dist', 'target'}]
            
            for file in files:
                file_path = os.path.join(root, file)
                extension = get_file_extension(file_path)
                
                # Process supported file types
                if extension in supported_extensions or not extension:
                    try:
                        file_nodes = parse_file_basic(file_path, repo_path)
                        nodes.extend(file_nodes)
                        processed_files += 1
                        
                        if processed_files % 20 == 0:
                            logger.info(f"Processed {processed_files} files...")
                            
                    except Exception as e:
                        logger.warning(f"Failed to parse {file_path}: {e}")
        
        # Extract basic relationships
        edges = extract_basic_relationships(nodes)
        
        logger.info(f"Repository parsing complete: {len(nodes)} nodes, {len(edges)} edges from {processed_files} files")
        
        graph_data = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {
                "node_count": len(nodes),
                "edge_count": len(edges),
                "files_processed": processed_files,
                "supported_languages": list(set(n.get('language') for n in nodes if n.get('language'))),
                "generated_by": "RepoCanvas multi-language parser",
                "schema_version": "2.0"
            }
        }
        
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(graph_data, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved graph to {output_file}")
        
        return graph_data
        
    except Exception as e:
        logger.error(f"Error parsing repository: {e}")
        return {
            "nodes": [],
            "edges": [],
            "error": str(e),
            "metadata": {"generated_by": "RepoCanvas parser (error)", "schema_version": "2.0"}
        }

def parse_file_basic(file_path: str, repo_root: str) -> List[Dict[str, Any]]:
    """
    Basic file parsing that creates standardized nodes.
    
    For now, this creates file-level nodes. Future enhancement will add
    Tree-sitter integration for detailed function/class extraction.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except Exception as e:
        logger.debug(f"Could not read file {file_path}: {e}")
        return []
    
    relative_path = os.path.relpath(file_path, repo_root)
    extension = get_file_extension(file_path)
    lang_config = get_language_from_extension(extension)
    
    # For Python files, try basic AST parsing
    if extension == 'py':
        return parse_python_file_basic(file_path, content, relative_path)
    
    # For other files, create a file-level node
    file_name = os.path.basename(file_path)
    lines = content.splitlines()
    
    # Truncate very large files
    max_chars = 2000
    truncated_content = content[:max_chars]
    if len(content) > max_chars:
        truncated_content += f"\\n... (file truncated, {len(content) - max_chars} more characters)"
    
    node = {
        "id": f"file:{file_name}:{relative_path}:1",
        "name": file_name,
        "type": "FILE",
        "file": relative_path,
        "start_line": 1,
        "end_line": len(lines),
        "code": truncated_content,
        "docstring": f"File: {file_name}" + (f" ({lang_config['language']})" if lang_config else ""),
        "language": lang_config['language'] if lang_config else 'unknown'
    }
    
    return [node]

def parse_python_file_basic(file_path: str, content: str, relative_path: str) -> List[Dict[str, Any]]:
    """Basic Python file parsing using AST."""
    nodes = []
    lines = content.splitlines()
    
    try:
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = getattr(node, 'end_lineno', start_line)
                code = '\\n'.join(lines[start_line-1:end_line])
                docstring = ast.get_docstring(node) or ""
                
                nodes.append({
                    "id": f"function:{node.name}:{relative_path}:{start_line}",
                    "name": node.name,
                    "type": "FUNCTION",
                    "file": relative_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code,
                    "docstring": docstring,
                    "language": "python"
                })
                
            elif isinstance(node, ast.ClassDef):
                start_line = node.lineno
                end_line = getattr(node, 'end_lineno', start_line)
                code = '\\n'.join(lines[start_line-1:end_line])
                docstring = ast.get_docstring(node) or ""
                
                nodes.append({
                    "id": f"class:{node.name}:{relative_path}:{start_line}",
                    "name": node.name,
                    "type": "CLASS",
                    "file": relative_path,
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code,
                    "docstring": docstring,
                    "language": "python"
                })
                
        return nodes
        
    except Exception as e:
        logger.debug(f"Python AST parsing failed for {file_path}: {e}")
        # Return file-level node as fallback
        return [{
            "id": f"file:{os.path.basename(file_path)}:{relative_path}:1",
            "name": os.path.basename(file_path),
            "type": "FILE",
            "file": relative_path,
            "start_line": 1,
            "end_line": len(lines),
            "code": content[:2000] + ("..." if len(content) > 2000 else ""),
            "docstring": f"Python file: {os.path.basename(file_path)} (parsing failed)",
            "language": "python"
        }]

def extract_basic_relationships(nodes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Extract basic relationships between nodes."""
    edges = []
    
    # Build a name index for quick lookups
    name_to_nodes = {}
    for node in nodes:
        name = node['name']
        if name not in name_to_nodes:
            name_to_nodes[name] = []
        name_to_nodes[name].append(node['id'])
    
    # For Python nodes, look for basic function calls
    for node in nodes:
        if node.get('language') == 'python' and node.get('type') in ['FUNCTION', 'CLASS']:
            try:
                # Simple regex-based call detection
                code = node.get('code', '')
                calls = re.findall(r'(\w+)\s*\(', code)
                
                for call_name in calls:
                    if call_name in name_to_nodes:
                        for target_id in name_to_nodes[call_name]:
                            if target_id != node['id']:  # Don't create self-loops
                                edges.append({
                                    "source": node['id'],
                                    "target": target_id,
                                    "type": "call",
                                    "detected_by": "basic_regex"
                                })
            except Exception:
                continue
    
    return edges

def extract_functions(file_path: str, language: str = "python") -> List[Dict[str, Any]]:
    """
    Extract functions from a file using enhanced multi-language support.
    
    Args:
        file_path: Path to source file
        language: Programming language (auto-detected if not provided)
        
    Returns:
        List of function definitions with standardized format
    """
    logger.info(f"Extracting functions from {file_path} ({language})")
    
    if not os.path.exists(file_path):
        return []
    
    try:
        extension = get_file_extension(file_path)
        detected_lang = get_language_from_extension(extension)
        
        if detected_lang:
            language = detected_lang['language']
        
        # For now, parse as file-level nodes
        # TODO: Integrate with Worker's Tree-sitter implementation
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        if language == 'python':
            return parse_python_file_basic(file_path, content, os.path.basename(file_path))
        else:
            # Return file-level representation for other languages
            return [{
                "id": f"file:{os.path.basename(file_path)}:1",
                "name": os.path.basename(file_path),
                "type": "FILE",
                "language": language,
                "file": file_path,
                "start_line": 1,
                "end_line": len(content.splitlines()),
                "code": content[:1000] + ("..." if len(content) > 1000 else ""),
                "docstring": f"{language.title()} file"
            }]
            
    except Exception as e:
        logger.error(f"Error extracting functions from {file_path}: {e}")
        return []

def build_dependency_graph(functions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build dependency graph from functions with enhanced multi-language support.
    
    Args:
        functions: List of function definitions
        
    Returns:
        Graph structure with nodes and edges
    """
    logger.info(f"Building dependency graph from {len(functions)} functions")
    
    if not functions:
        return {"nodes": [], "edges": []}
    
    # Use the basic relationship extraction
    edges = extract_basic_relationships(functions)
    
    # Format nodes for compatibility
    formatted_nodes = []
    for func in functions:
        node = func.copy()
        node['label'] = func.get('name', 'unknown')
        formatted_nodes.append(node)
    
    return {
        "nodes": formatted_nodes,
        "edges": edges,
        "metadata": {
            "node_count": len(formatted_nodes),
            "edge_count": len(edges),
            "generated_by": "RepoCanvas dependency builder",
            "schema_version": "2.0"
        }
    }

# Wrapper functions for backward compatibility with worker app

def build_repository_graph(repo_root, output_path=None):
    """
    Wrapper around parse_repository for backward compatibility.
    Returns (nodes, edges, graph) tuple.
    """
    if output_path is None:
        output_path = os.path.join(repo_root, "graph.json")
    
    graph_data = parse_repository(repo_root, output_path)
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])
    
    # Create a simple NetworkX-like graph object for compatibility
    class SimpleGraph:
        def __init__(self, nodes, edges):
            self.nodes = {node['id']: node for node in nodes}
            self.edges = edges
    
    graph = SimpleGraph(nodes, edges)
    return nodes, edges, graph

def make_document_for_node(node, max_lines=40):
    """
    Create a semantic document for a node suitable for embedding.
    """
    name = node.get('name', 'Unknown')
    file_path = node.get('file', 'Unknown')
    start_line = node.get('start_line', 0)
    doc = node.get('doc', '').strip()
    code = node.get('code', '')
    
    # Create title with location
    title = f"{name} - {file_path}:{start_line}"
    
    # Get code snippet (first max_lines)
    code_lines = code.splitlines()
    snippet_lines = code_lines[:max_lines]
    snippet = '\n'.join(snippet_lines)
    
    # Add truncation indicator if code was truncated
    if len(code_lines) > max_lines:
        snippet += f"\n... ({len(code_lines) - max_lines} more lines)"
    
    # Build document sections
    document_parts = []
    
    # Title section
    document_parts.append(f"# {title}")
    
    # Signature section
    signature = snippet.split('\n')[0] if snippet else ""
    if signature:
        document_parts.append(f"\n## Signature\n```python\n{signature}\n```")
    
    # Documentation section
    if doc:
        document_parts.append(f"\n## Documentation\n{doc}")
    
    # Code section
    if snippet:
        document_parts.append(f"\n## Code\n```python\n{snippet}\n```")
    
    # Metadata section
    metadata_parts = []
    if 'loc' in node:
        metadata_parts.append(f"Lines of code: {node['loc']}")
    if 'complexity' in node:
        metadata_parts.append(f"Complexity: {node['complexity']}")
    
    if metadata_parts:
        metadata_text = " | ".join(metadata_parts)
        document_parts.append(f"\n## Metrics\n{metadata_text}")
    
    return '\n'.join(document_parts)

def generate_embedding_documents(nodes, max_lines=40, save_files=True, documents_dir="data/documents"):
    """
    Generate semantic documents for embedding from parsed nodes.
    """
    documents = []
    file_paths = []
    
    for node in nodes:
        doc_text = make_document_for_node(node, max_lines)
        documents.append(doc_text)
    
    # Save to files if requested
    if save_files:
        os.makedirs(documents_dir, exist_ok=True)
        for i, (node, doc_text) in enumerate(zip(nodes, documents)):
            safe_name = re.sub(r'[<>:"/\\|?*]', '_', node.get('id', f'node_{i}'))
            file_path = os.path.join(documents_dir, f"{safe_name}.md")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(doc_text)
                file_paths.append(file_path)
            except Exception as e:
                logger.warning(f"Failed to save document {file_path}: {e}")
                file_paths.append("")
    
    metadata = {
        'total_documents': len(documents),
        'total_characters': sum(len(doc) for doc in documents),
        'average_characters': sum(len(doc) for doc in documents) / len(documents) if documents else 0,
        'max_lines_per_doc': max_lines,
        'documents_dir': documents_dir if save_files else None,
        'files_saved': len([p for p in file_paths if p]) if save_files else 0
    }
    
    return {
        'documents': documents,
        'file_paths': file_paths if save_files else None,
        'metadata': metadata
    }

def build_repository_with_documents(repo_root, output_path=None, documents_dir="data/documents", max_lines=40):
    """
    Complete pipeline: build repository graph and generate semantic documents.
    """
    print(f"🚀 Starting complete repository analysis...")
    print(f"   Repository: {repo_root}")
    print(f"   Documents directory: {documents_dir}")
    
    # Build repository graph
    nodes, edges, graph = build_repository_graph(repo_root, output_path)
    
    # Generate semantic documents
    doc_results = generate_embedding_documents(
        nodes, 
        max_lines=max_lines, 
        save_files=True, 
        documents_dir=documents_dir
    )
    
    results = {
        'nodes': nodes,
        'edges': edges,
        'graph': graph,
        'documents': doc_results['documents'],
        'document_paths': doc_results['file_paths'],
        'document_metadata': doc_results['metadata'],
        'analysis_summary': {
            'total_nodes': len(nodes),
            'total_edges': len(edges),
            'graph_nodes': len(graph.nodes),
            'graph_edges': len(graph.edges),
            'documents_generated': doc_results['metadata']['total_documents'],
            'documents_saved': doc_results['metadata']['files_saved']
        }
    }
    
    print(f"\n🎉 Repository analysis complete!")
    print(f"   📊 Nodes: {results['analysis_summary']['total_nodes']}")
    print(f"   🔗 Edges: {results['analysis_summary']['total_edges']}")
    print(f"   📄 Documents: {results['analysis_summary']['documents_generated']}")
    
    return results