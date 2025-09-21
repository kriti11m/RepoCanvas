#!/usr/bin/env python3
"""
Demo script for the complete repository graph building pipeline.

This demonstrates:
1. Building repository graphs with NetworkX
2. Node annotation with metadata (LOC, complexity, call counts)
3. JSON export for frontend consumption
4. Analysis and statistics
"""

import sys
import os
from pathlib import Path

# Add worker directory to path
worker_dir = Path(__file__).parent / 'worker'
sys.path.append(str(worker_dir))

from parse_repo import build_repository_graph, build_nodes, extract_edges, annotate_nodes
import json

def analyze_graph_statistics(nodes, edges):
    """Analyze and display graph statistics."""
    print("=" * 60)
    print("GRAPH STATISTICS")
    print("=" * 60)
    
    # Basic counts
    functions = [n for n in nodes if n['id'].startswith('function:')]
    classes = [n for n in nodes if n['id'].startswith('class:')]
    
    print(f"📊 Node Breakdown:")
    print(f"   Total nodes: {len(nodes)}")
    print(f"   Functions: {len(functions)} ({len(functions)/len(nodes)*100:.1f}%)")
    print(f"   Classes: {len(classes)} ({len(classes)/len(nodes)*100:.1f}%)")
    
    # Edge analysis
    call_edges = [e for e in edges if e.get('type') == 'call']
    import_edges = [e for e in edges if e.get('type') == 'import']
    ambiguous_edges = [e for e in edges if e.get('ambiguous')]
    
    print(f"\n🔗 Edge Analysis:")
    print(f"   Total edges: {len(edges)}")
    print(f"   Function calls: {len(call_edges)} ({len(call_edges)/len(edges)*100:.1f}%)")
    print(f"   Imports: {len(import_edges)} ({len(import_edges)/len(edges)*100:.1f}%)")
    print(f"   Ambiguous: {len(ambiguous_edges)} ({len(ambiguous_edges)/len(edges)*100:.1f}%)")
    
    # Code metrics
    locs = [n['loc'] for n in nodes]
    complexities = [n['cyclomatic'] for n in nodes]
    calls_in = [n['num_calls_in'] for n in nodes]
    calls_out = [n['num_calls_out'] for n in nodes]
    
    print(f"\n📈 Code Metrics:")
    print(f"   Average LOC: {sum(locs)/len(locs):.1f}")
    print(f"   Total LOC: {sum(locs)}")
    print(f"   Average complexity: {sum(complexities)/len(complexities):.1f}")
    print(f"   Max complexity: {max(complexities)}")
    print(f"   Average calls in: {sum(calls_in)/len(calls_in):.1f}")
    print(f"   Average calls out: {sum(calls_out)/len(calls_out):.1f}")

def show_top_nodes(nodes, metric, title, count=5):
    """Show top nodes by a specific metric."""
    print(f"\n🏆 {title} (Top {count}):")
    
    if metric == 'complexity':
        sorted_nodes = sorted(nodes, key=lambda x: x['cyclomatic'], reverse=True)
        for i, node in enumerate(sorted_nodes[:count]):
            print(f"   {i+1}. {node['name']} (complexity: {node['cyclomatic']})")
            print(f"      📁 {node['file']}:{node['start_line']}")
            
    elif metric == 'loc':
        sorted_nodes = sorted(nodes, key=lambda x: x['loc'], reverse=True)
        for i, node in enumerate(sorted_nodes[:count]):
            print(f"   {i+1}. {node['name']} (LOC: {node['loc']})")
            print(f"      📁 {node['file']}:{node['start_line']}")
            
    elif metric == 'calls_in':
        sorted_nodes = sorted(nodes, key=lambda x: x['num_calls_in'], reverse=True)
        for i, node in enumerate(sorted_nodes[:count]):
            print(f"   {i+1}. {node['name']} (called {node['num_calls_in']} times)")
            print(f"      📁 {node['file']}:{node['start_line']}")
            
    elif metric == 'calls_out':
        sorted_nodes = sorted(nodes, key=lambda x: x['num_calls_out'], reverse=True)
        for i, node in enumerate(sorted_nodes[:count]):
            print(f"   {i+1}. {node['name']} (calls {node['num_calls_out']} others)")
            print(f"      📁 {node['file']}:{node['start_line']}")
            
    elif metric == 'connectivity':
        sorted_nodes = sorted(nodes, key=lambda x: x['num_calls_in'] + x['num_calls_out'], reverse=True)
        for i, node in enumerate(sorted_nodes[:count]):
            total = node['num_calls_in'] + node['num_calls_out']
            print(f"   {i+1}. {node['name']} (total connections: {total})")
            print(f"      📁 {node['file']}:{node['start_line']}")
            print(f"      📞 in: {node['num_calls_in']}, out: {node['num_calls_out']}")

def demo_complete_pipeline():
    """Demonstrate the complete graph building pipeline."""
    print("Repository Graph Building Demo")
    print("=" * 60)
    
    # Use the worker directory as our test repository
    repo_path = str(worker_dir)
    output_path = str(Path(__file__).parent / "demo_graph.json")
    
    print(f"📂 Repository: {repo_path}")
    print(f"💾 Output: {output_path}")
    
    try:
        # Build the complete graph
        print(f"\n🔨 Building repository graph...")
        nodes, edges, graph = build_repository_graph(repo_path, output_path)
        
        # Show analysis
        analyze_graph_statistics(nodes, edges)
        
        # Show top nodes by various metrics
        show_top_nodes(nodes, 'complexity', 'Most Complex Functions')
        show_top_nodes(nodes, 'loc', 'Largest Functions (by LOC)')
        show_top_nodes(nodes, 'calls_in', 'Most Called Functions')
        show_top_nodes(nodes, 'connectivity', 'Most Connected Functions')
        
        print(f"\n" + "=" * 60)
        print("JSON EXPORT VERIFICATION")
        print("=" * 60)
        
        # Verify JSON export
        if os.path.exists(output_path):
            with open(output_path, 'r') as f:
                graph_data = json.load(f)
            
            print(f"✅ JSON file created successfully!")
            print(f"   File size: {os.path.getsize(output_path):,} bytes")
            print(f"   Nodes in JSON: {len(graph_data['nodes'])}")
            print(f"   Edges in JSON: {len(graph_data['edges'])}")
            print(f"   Schema version: {graph_data['metadata']['schema_version']}")
            
            # Show sample node structure
            if graph_data['nodes']:
                sample_node = graph_data['nodes'][0]
                print(f"\n📋 Sample node structure:")
                for key, value in sample_node.items():
                    value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                    print(f"   {key}: {value_str}")
        
        print(f"\n" + "=" * 60)
        print("✅ DEMO COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        
        return nodes, edges, graph
        
    except Exception as e:
        print(f"❌ Error during demo: {e}")
        import traceback
        traceback.print_exc()
        return None, None, None

if __name__ == "__main__":
    nodes, edges, graph = demo_complete_pipeline()
    
    if nodes:
        print(f"\n💡 Usage Tips:")
        print(f"   - Use build_repository_graph(repo_path) for complete pipeline")
        print(f"   - Use annotate_nodes(nodes, edges) to add metadata")
        print(f"   - Use save_graph_json(nodes, edges, path) for frontend export")
        print(f"   - NetworkX graph available for advanced analysis")
        print(f"   - All metrics are integers for JSON compatibility")
