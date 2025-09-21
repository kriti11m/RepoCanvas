#!/usr/bin/env python3
"""
Example usage of the parse_file and build_nodes functions.

This script demonstrates how to:
1. Parse individual files to extract functions and classes
2. Build a complete node collection for a repository
3. Analyze the results and find patterns
"""

import sys
import os
from pathlib import Path

# Add worker directory to path
worker_dir = Path(__file__).parent / 'worker'
sys.path.append(str(worker_dir))

from parse_repo import parse_file, build_nodes

def demo_parse_single_file():
    """Demonstrate parsing a single file."""
    print("=" * 60)
    print("DEMO: Parsing a Single File")
    print("=" * 60)
    
    # Parse the ts_parser.py file as an example
    file_path = str(worker_dir / 'parser' / 'ts_parser.py')
    
    if os.path.exists(file_path):
        print(f"Parsing: {file_path}")
        nodes = parse_file(file_path)
        
        print(f"\nFound {len(nodes)} nodes:")
        for i, node in enumerate(nodes, 1):
            print(f"\n{i}. {node['name']} ({'Function' if 'function:' in node['id'] else 'Class'})")
            print(f"   Lines: {node['start_line']}-{node['end_line']}")
            print(f"   ID: {node['id']}")
            if node['doc']:
                # Show first line of docstring
                first_line = node['doc'].split('\n')[0].strip()
                print(f"   Doc: {first_line}")
            else:
                print(f"   Doc: (No docstring)")
            
            # Show a snippet of the code
            code_lines = node['code'].split('\n')
            if len(code_lines) > 3:
                print(f"   Code: {code_lines[0]}")
                print(f"         {code_lines[1]}")
                print(f"         ...")
            else:
                print(f"   Code: {node['code']}")
    else:
        print(f"File not found: {file_path}")

def demo_build_repository_nodes():
    """Demonstrate building nodes for an entire repository."""
    print("\n" + "=" * 60)
    print("DEMO: Building Repository Node Collection")
    print("=" * 60)
    
    repo_path = str(worker_dir.parent)
    print(f"Analyzing repository: {repo_path}")
    
    # Build complete node collection
    nodes, name_map = build_nodes(repo_path)
    
    print(f"\n📊 Repository Analysis Results:")
    print(f"   Total nodes found: {len(nodes)}")
    print(f"   Unique names: {len(name_map)}")
    
    # Analyze node types
    functions = [n for n in nodes if 'function:' in n['id']]
    classes = [n for n in nodes if 'class:' in n['id']]
    
    print(f"   Functions: {len(functions)}")
    print(f"   Classes: {len(classes)}")
    
    # Find most common names (potential duplicates/patterns)
    print(f"\n🔍 Name Analysis:")
    common_names = [(name, len(node_ids)) for name, node_ids in name_map.items() if len(node_ids) > 1]
    
    if common_names:
        common_names.sort(key=lambda x: x[1], reverse=True)
        print(f"   Names appearing in multiple places:")
        for name, count in common_names[:5]:
            print(f"     - {name}: {count} occurrences")
            # Show where they appear
            for node_id in name_map[name][:2]:  # Show first 2 occurrences
                # Extract file info from node_id
                parts = node_id.split(':')
                if len(parts) >= 3:
                    file_part = parts[2]
                    line_part = parts[3] if len(parts) > 3 else "?"
                    print(f"       → {file_part}:{line_part}")
    else:
        print(f"   All function/class names are unique")
    
    # Show files with most nodes
    print(f"\n📁 File Analysis:")
    file_counts = {}
    for node in nodes:
        file_path = node['file']
        file_counts[file_path] = file_counts.get(file_path, 0) + 1
    
    top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"   Files with most functions/classes:")
    for file_path, count in top_files:
        print(f"     - {file_path}: {count} nodes")
    
    # Show nodes with longest docstrings
    print(f"\n📝 Documentation Analysis:")
    documented_nodes = [n for n in nodes if n['doc']]
    print(f"   Nodes with docstrings: {len(documented_nodes)}/{len(nodes)} ({len(documented_nodes)/len(nodes)*100:.1f}%)")
    
    if documented_nodes:
        # Sort by docstring length
        documented_nodes.sort(key=lambda x: len(x['doc']), reverse=True)
        print(f"   Best documented functions/classes:")
        for node in documented_nodes[:3]:
            doc_length = len(node['doc'])
            first_line = node['doc'].split('\n')[0].strip()
            print(f"     - {node['name']} ({doc_length} chars): {first_line}")
    
    return nodes, name_map

def demo_search_functionality(nodes, name_map):
    """Demonstrate searching through the parsed nodes."""
    print("\n" + "=" * 60)
    print("DEMO: Searching Parsed Nodes")
    print("=" * 60)
    
    # Search for specific function names
    search_terms = ['parse', 'build', 'get', 'clone']
    
    for term in search_terms:
        matching_names = [name for name in name_map.keys() if term.lower() in name.lower()]
        if matching_names:
            print(f"\n🔍 Names containing '{term}':")
            for name in matching_names[:3]:  # Show first 3 matches
                node_ids = name_map[name]
                print(f"   - {name} ({len(node_ids)} occurrence(s))")
                # Show details for first occurrence
                first_node = next(n for n in nodes if n['id'] == node_ids[0])
                print(f"     → {first_node['file']}:{first_node['start_line']}")
                if first_node['doc']:
                    first_line = first_node['doc'].split('\n')[0].strip()
                    print(f"     → {first_line}")

if __name__ == "__main__":
    print("Repository Code Analysis Demo")
    print("=" * 60)
    
    try:
        # Demo individual file parsing
        demo_parse_single_file()
        
        # Demo repository-wide parsing
        nodes, name_map = demo_build_repository_nodes()
        
        # Demo search functionality
        demo_search_functionality(nodes, name_map)
        
        print("\n" + "=" * 60)
        print("✅ Demo completed successfully!")
        print("=" * 60)
        
        # Provide usage tips
        print("\n💡 Usage Tips:")
        print("   - Use parse_file(path) for individual files")
        print("   - Use build_nodes(repo_root) for entire repositories")
        print("   - Tree-sitter will be used when available, AST as fallback")
        print("   - Node IDs are unique and include file path and line number")
        print("   - Name mapping helps find function/class name collisions")
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
