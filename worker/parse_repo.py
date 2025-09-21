# backend/worker/parse_repo.py
import os
import ast
import json
import networkx as nx
from parser.ts_parser import get_ts_parser, parse_with_ast

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
        'java': 'java',
        'cpp': 'cpp',
        'c': 'c',
        'rs': 'rust',
        'go': 'go',
        'html': 'html',
        'css': 'css',
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
        return []
    extension = get_file_extension(file_path)
    language = get_language_from_extension(extension)
    source_code = read_file(file_path)
    source_lines = source_code.splitlines()
    nodes = []
    # Try tree-sitter first
    if language:
        try:
            parser = get_ts_parser(language)
            tree = parser.parse(bytes(source_code, 'utf8'))
            def traverse(node):
                if node.type in ['function_definition', 'function_declaration', 'method_definition']:
                    name_node = next((c for c in node.children if c.type == 'identifier'), None)
                    if name_node:
                        name = source_code[name_node.start_byte:name_node.end_byte]
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1
                        code = '\n'.join(source_lines[start_line-1:end_line])
                        doc = extract_docstring_from_source(source_lines, start_line, end_line)
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
                elif node.type in ['class_definition', 'class_declaration']:
                    name_node = next((c for c in node.children if c.type == 'identifier'), None)
                    if name_node:
                        name = source_code[name_node.start_byte:name_node.end_byte]
                        start_line = node.start_point[0] + 1
                        end_line = node.end_point[0] + 1
                        code = '\n'.join(source_lines[start_line-1:end_line])
                        doc = extract_docstring_from_source(source_lines, start_line, end_line)
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
                for child in node.children:
                    traverse(child)
            traverse(tree.root_node)
            if nodes:
                return nodes
        except Exception:
            pass
    # Fallback to AST for Python
    if extension == 'py':
        try:
            tree = parse_with_ast(source_code)
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    start_line = node.lineno
                    end_line = getattr(node, 'end_lineno', start_line)
                    code = '\n'.join(source_lines[start_line-1:end_line])
                    doc = ast.get_docstring(node) or ""
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
                    end_line = getattr(node, 'end_lineno', start_line)
                    code = '\n'.join(source_lines[start_line-1:end_line])
                    doc = ast.get_docstring(node) or ""
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
        except Exception:
            return []
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
    for root, _, files in os.walk(repo_root):
        for f in files:
            if f.endswith('.py'):
                p = os.path.join(root, f)
                nodes.extend(parse_file(p))
    name_map = {}
    for n in nodes:
        name_map.setdefault(n['name'], []).append(n['id'])
    return nodes, name_map

def extract_edges(nodes, name_map):
    """
    Extract edges between nodes by analyzing function calls and imports.
    
    Args:
        nodes (list): List of parsed nodes
        name_map (dict): Mapping of function/class names to node IDs
    
    Returns:
        list: List of edge dictionaries with from/to/type information
    """
    edges = []
    id_by_name = name_map
    for node in nodes:
        try:
            src = node['code']
            tree = ast.parse(src)
            for n in ast.walk(tree):
                if isinstance(n, ast.Call):
                    if isinstance(n.func, ast.Name):
                        called = n.func.id
                        if called in id_by_name:
                            for target_id in id_by_name[called]:
                                edges.append({"from": node['id'], "to": target_id, "type": "call"})
                    elif isinstance(n.func, ast.Attribute):
                        attr = n.func.attr
                        if attr in id_by_name:
                            for target_id in id_by_name[attr]:
                                edges.append({"from": node['id'], "to": target_id, "type": "call", "ambiguous": True})
                elif isinstance(n, ast.Import):
                    for alias in n.names:
                        edges.append({"from": node['file'], "to": alias.name, "type": "import"})
                elif isinstance(n, ast.ImportFrom):
                    module = n.module or ""
                    for alias in n.names:
                        edges.append({"from": node['file'], "to": f"{module}.{alias.name}", "type": "import"})
        except Exception:
            continue
    return edges

def calculate_cyclomatic_complexity(code):
    """
    Calculate basic cyclomatic complexity heuristic.
    
    Args:
        code (str): Source code to analyze
    
    Returns:
        int: Cyclomatic complexity (number of decision points + 1)
    """
    try:
        tree = ast.parse(code)
        complexity = 1  # Base complexity
        
        for node in ast.walk(tree):
            # Count decision points
            if isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(node, ast.BoolOp):
                # Count additional conditions in boolean operations
                complexity += len(node.values) - 1
            elif isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                # Comprehensions add complexity
                complexity += 1
        
        return complexity
    except Exception:
        return 1  # Default complexity

def annotate_nodes(nodes, edges):
    """
    Annotate nodes with additional metadata including call counts and complexity.
    
    Args:
        nodes (list): List of node dictionaries to annotate
        edges (list): List of edge dictionaries for call counting
    
    Returns:
        None: Modifies nodes in place
    """
    # Count incoming and outgoing calls
    incoming = {}
    outgoing = {}
    
    for e in edges:
        if e.get('type') == 'call':  # Only count call edges, not imports
            from_id = e['from']
            to_id = e['to']
            
            outgoing.setdefault(from_id, 0)
            outgoing[from_id] += 1
            
            incoming.setdefault(to_id, 0)
            incoming[to_id] += 1
    
    # Annotate each node
    for n in nodes:
        node_id = n['id']
        
        # Call counts
        n['num_calls_out'] = int(outgoing.get(node_id, 0))
        n['num_calls_in'] = int(incoming.get(node_id, 0))
        
        # Lines of code
        n['loc'] = int(n['end_line'] - n['start_line'] + 1)
        
        # Cyclomatic complexity
        n['cyclomatic'] = int(calculate_cyclomatic_complexity(n['code']))

def build_graph(nodes, edges):
    """
    Construct a NetworkX DiGraph from nodes and edges.
    
    Args:
        nodes (list): List of node dictionaries
        edges (list): List of edge dictionaries
    
    Returns:
        nx.DiGraph: NetworkX directed graph with node and edge attributes
    """
    G = nx.DiGraph()
    
    # Add nodes with all their attributes
    for node in nodes:
        node_id = node['id']
        # Create a copy of node data for graph attributes
        node_attrs = {k: v for k, v in node.items() if k != 'id'}
        G.add_node(node_id, **node_attrs)
    
    # Add edges with their attributes
    for edge in edges:
        from_id = edge['from']
        to_id = edge['to']
        # Create a copy of edge data for graph attributes
        edge_attrs = {k: v for k, v in edge.items() if k not in ['from', 'to']}
        
        # Only add edge if both nodes exist in the graph
        if from_id in G.nodes and to_id in G.nodes:
            G.add_edge(from_id, to_id, **edge_attrs)
    
    return G

def save_graph_json(nodes, edges, out_path):
    """
    Save graph data in JSON format suitable for frontend consumption.
    
    Args:
        nodes (list): List of annotated node dictionaries
        edges (list): List of edge dictionaries
        out_path (str): Output file path for JSON
    
    Returns:
        None: Writes JSON file to disk
    """
    # Prepare the graph data structure
    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "generated_by": "RepoCanvas parser",
            "schema_version": "1.0"
        }
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    
    # Write JSON file
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(graph_data, f, indent=2, ensure_ascii=False)
    
    print(f"Graph saved to {out_path}")
    print(f"  - Nodes: {len(nodes)}")
    print(f"  - Edges: {len(edges)}")

def build_repository_graph(repo_root, output_path=None):
    """
    Complete pipeline to build and save repository graph.
    
    Args:
        repo_root (str): Root directory of repository to analyze
        output_path (str, optional): Path to save graph.json (default: repo_root/graph.json)
    
    Returns:
        tuple: (nodes, edges, graph) - The complete graph data
    """
    if output_path is None:
        output_path = os.path.join(repo_root, "graph.json")
    
    print(f"Analyzing repository: {repo_root}")
    
    # Step 1: Parse all files and build nodes
    nodes, name_map = build_nodes(repo_root)
    print(f"Found {len(nodes)} nodes")
    
    # Step 2: Extract edges between nodes
    edges = extract_edges(nodes, name_map)
    print(f"Found {len(edges)} edges")
    
    # Step 3: Annotate nodes with metadata
    annotate_nodes(nodes, edges)
    print("Annotated nodes with metadata")
    
    # Step 4: Build NetworkX graph
    graph = build_graph(nodes, edges)
    print(f"Built NetworkX graph: {len(graph.nodes)} nodes, {len(graph.edges)} edges")
    
    # Step 5: Save to JSON
    save_graph_json(nodes, edges, output_path)
    
    return nodes, edges, graph
