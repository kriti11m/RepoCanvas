# backend/worker/parse_repo.py
import os
import ast
import hashlib
from parser.ts_parser import get_ts_parser, parse_with_ast
from parser.utils import clone_repo

def read_file(file_path):
    """Read file contents as string."""
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        return f.read()

def get_file_extension(file_path):
    """Get file extension without the dot."""
    return os.path.splitext(file_path)[1][1:].lower()

def get_language_from_extension(extension):
    """Map file extensions to tree-sitter language names."""
    extension_map = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'jsx': 'javascript',
        'tsx': 'typescript',
        'java': 'java',
        'cpp': 'cpp',
        'cc': 'cpp',
        'cxx': 'cpp',
        'c': 'c',
        'h': 'c',
        'hpp': 'cpp',
        'rs': 'rust',
        'go': 'go',
        'rb': 'ruby',
        'php': 'php',
        'cs': 'c_sharp',
        'swift': 'swift',
        'kt': 'kotlin',
        'scala': 'scala',
        'html': 'html',
        'css': 'css',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml',
        'xml': 'xml'
    }
    return extension_map.get(extension)

def extract_docstring_from_source(source_lines, start_line, end_line):
    """Extract docstring from source code lines for tree-sitter parsed nodes."""
    # Look for docstring in the first few lines after the definition
    for i in range(start_line, min(start_line + 5, end_line, len(source_lines))):
        line = source_lines[i].strip()
        if line.startswith('"""') or line.startswith("'''"):
            # Found start of docstring
            quote_type = '"""' if line.startswith('"""') else "'''"
            docstring_lines = []
            
            # Check if it's a single-line docstring
            if line.count(quote_type) >= 2:
                return line.strip(quote_type).strip()
            
            # Multi-line docstring
            docstring_lines.append(line[3:])  # Remove opening quotes
            for j in range(i + 1, min(end_line, len(source_lines))):
                doc_line = source_lines[j]
                if quote_type in doc_line:
                    # Found closing quotes
                    docstring_lines.append(doc_line[:doc_line.find(quote_type)])
                    return '\n'.join(docstring_lines).strip()
                docstring_lines.append(doc_line.rstrip())
    return ""

def parse_with_tree_sitter(file_path, language):
    """Parse file using tree-sitter for the given language."""
    try:
        parser = get_ts_parser(language)
        source_code = read_file(file_path)
        tree = parser.parse(bytes(source_code, 'utf8'))
        source_lines = source_code.splitlines()
        
        nodes = []
        
        def traverse_node(node):
            # Check for function definitions
            if node.type in ['function_definition', 'function_declaration', 'method_definition']:
                name_node = None
                for child in node.children:
                    if child.type == 'identifier' or child.type == 'function_declarator':
                        name_node = child
                        break
                
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte]
                    start_line = node.start_point[0] + 1  # tree-sitter uses 0-based indexing
                    end_line = node.end_point[0] + 1
                    
                    # Extract code snippet
                    code_lines = source_lines[start_line-1:end_line]
                    code = '\n'.join(code_lines)
                    
                    # Extract docstring
                    doc = extract_docstring_from_source(source_lines, start_line, end_line)
                    
                    # Generate unique ID
                    node_id = f"function:{name}:{os.path.relpath(file_path)}:{start_line}"
                    
                    nodes.append({
                        "id": node_id,
                        "name": name,
                        "file": os.path.relpath(file_path),
                        "start_line": start_line,
                        "end_line": end_line,
                        "code": code,
                        "doc": doc
                    })
            
            # Check for class definitions
            elif node.type in ['class_definition', 'class_declaration']:
                name_node = None
                for child in node.children:
                    if child.type == 'identifier':
                        name_node = child
                        break
                
                if name_node:
                    name = source_code[name_node.start_byte:name_node.end_byte]
                    start_line = node.start_point[0] + 1
                    end_line = node.end_point[0] + 1
                    
                    # Extract code snippet
                    code_lines = source_lines[start_line-1:end_line]
                    code = '\n'.join(code_lines)
                    
                    # Extract docstring
                    doc = extract_docstring_from_source(source_lines, start_line, end_line)
                    
                    # Generate unique ID
                    node_id = f"class:{name}:{os.path.relpath(file_path)}:{start_line}"
                    
                    nodes.append({
                        "id": node_id,
                        "name": name,
                        "file": os.path.relpath(file_path),
                        "start_line": start_line,
                        "end_line": end_line,
                        "code": code,
                        "doc": doc
                    })
            
            # Recursively traverse children
            for child in node.children:
                traverse_node(child)
        
        traverse_node(tree.root_node)
        return nodes
        
    except Exception as e:
        print(f"Tree-sitter parsing failed for {file_path}: {e}")
        return None

def parse_file_with_ast(file_path):
    """Parse Python file using AST as fallback."""
    try:
        source_code = read_file(file_path)
        tree = parse_with_ast(source_code)
        source_lines = source_code.splitlines()
        
        nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else start_line
                
                # If end_line is not available, estimate from the last statement in body
                if end_line == start_line and node.body:
                    last_stmt = node.body[-1]
                    end_line = last_stmt.end_lineno if hasattr(last_stmt, 'end_lineno') and last_stmt.end_lineno else last_stmt.lineno
                
                # Extract code snippet
                code_lines = source_lines[start_line-1:end_line]
                code = '\n'.join(code_lines)
                
                # Extract docstring
                doc = ast.get_docstring(node) or ""
                
                # Generate unique ID
                node_id = f"function:{node.name}:{os.path.relpath(file_path)}:{start_line}"
                
                nodes.append({
                    "id": node_id,
                    "name": node.name,
                    "file": os.path.relpath(file_path),
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code,
                    "doc": doc
                })
            
            elif isinstance(node, ast.ClassDef):
                start_line = node.lineno
                end_line = node.end_lineno if hasattr(node, 'end_lineno') and node.end_lineno else start_line
                
                # If end_line is not available, estimate from the last statement in body
                if end_line == start_line and node.body:
                    last_stmt = node.body[-1]
                    end_line = last_stmt.end_lineno if hasattr(last_stmt, 'end_lineno') and last_stmt.end_lineno else last_stmt.lineno
                
                # Extract code snippet
                code_lines = source_lines[start_line-1:end_line]
                code = '\n'.join(code_lines)
                
                # Extract docstring
                doc = ast.get_docstring(node) or ""
                
                # Generate unique ID
                node_id = f"class:{node.name}:{os.path.relpath(file_path)}:{start_line}"
                
                nodes.append({
                    "id": node_id,
                    "name": node.name,
                    "file": os.path.relpath(file_path),
                    "start_line": start_line,
                    "end_line": end_line,
                    "code": code,
                    "doc": doc
                })
        
        return nodes
        
    except Exception as e:
        print(f"AST parsing failed for {file_path}: {e}")
        return []

def parse_file(file_path):
    """
    Parse a file to extract functions and classes with metadata.
    
    Args:
        file_path (str): Path to the file to parse
    
    Returns:
        list: List of node dictionaries with keys:
            - id: Unique identifier for the node
            - name: Function/class name
            - file: Relative file path
            - start_line: Starting line number
            - end_line: Ending line number
            - code: Code snippet
            - doc: Docstring if present
    """
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return []
    
    extension = get_file_extension(file_path)
    language = get_language_from_extension(extension)
    
    # Try tree-sitter first if language is supported
    if language:
        nodes = parse_with_tree_sitter(file_path, language)
        if nodes is not None:
            return nodes
    
    # Fallback to AST for Python files
    if extension == 'py':
        return parse_file_with_ast(file_path)
    
    # For unsupported file types
    print(f"Unsupported file type: {file_path}")
    return []

def build_nodes(repo_root):
    """
    Walk through repository and parse all Python files to build node collection.
    
    Args:
        repo_root (str): Root directory of the repository
    
    Returns:
        tuple: (nodes_list, name_to_node_map)
            - nodes_list: List of all parsed nodes
            - name_to_node_map: Dict mapping function/class names to list of node IDs
    """
    nodes = []
    name_map = {}
    
    # Walk through all files in the repository
    for root, dirs, files in os.walk(repo_root):
        # Skip common directories that shouldn't be parsed
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'node_modules', 'build', 'dist']]
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Parse Python files (can be extended to other languages)
            if file.endswith('.py'):
                try:
                    file_nodes = parse_file(file_path)
                    nodes.extend(file_nodes)
                    
                    # Build name mapping
                    for node in file_nodes:
                        name = node['name']
                        if name not in name_map:
                            name_map[name] = []
                        name_map[name].append(node['id'])
                        
                except Exception as e:
                    print(f"Error parsing {file_path}: {e}")
                    continue
    
    print(f"Parsed {len(nodes)} nodes from {repo_root}")
    return nodes, name_map
