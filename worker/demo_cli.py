#!/usr/bin/env python3
"""
Demo script showing how to use the parse_repo.py CLI functionality.
"""

import os
import subprocess
import sys

def run_command(cmd, description):
    """Run a command and display its output."""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    """Demonstrate CLI functionality."""
    
    # Get the Python executable path
    python_exe = "/Users/kritimaheshwari/Desktop/RepoCanvas/.venv/bin/python"
    
    # Define commands to demonstrate
    demos = [
        {
            "cmd": [python_exe, "parse_repo.py", "--help"],
            "desc": "Show CLI help"
        },
        {
            "cmd": [python_exe, "parse_repo.py", 
                   "--repo", "/Users/kritimaheshwari/Desktop/RepoCanvas/worker", 
                   "--out", "data/demo_graph.json", 
                   "--verbose"],
            "desc": "Parse local repository and save graph"
        },
        {
            "cmd": [python_exe, "-c", """
import json
import os

# Check the generated files
if os.path.exists('data/demo_graph.json'):
    with open('data/demo_graph.json', 'r') as f:
        data = json.load(f)
    print(f"✅ Graph file created successfully")
    print(f"   📊 Nodes: {len(data['nodes'])}")
    print(f"   🔗 Edges: {len(data['edges'])}")
    print(f"   📄 Metadata: {data.get('metadata', {})}")
    
    # Show sample node
    if data['nodes']:
        sample_node = data['nodes'][0]
        print(f"\\n🔍 Sample node:")
        print(f"   ID: {sample_node.get('id', 'N/A')}")
        print(f"   Name: {sample_node.get('name', 'N/A')}")
        print(f"   File: {sample_node.get('file', 'N/A')}")
        print(f"   Lines: {sample_node.get('start_line', 'N/A')}-{sample_node.get('end_line', 'N/A')}")
        print(f"   LOC: {sample_node.get('loc', 'N/A')}")
        print(f"   Complexity: {sample_node.get('cyclomatic', 'N/A')}")
else:
    print("❌ Graph file not found")
"""],
            "desc": "Verify generated graph file"
        }
    ]
    
    print("🚀 RepoCanvas CLI Demo")
    print("=" * 60)
    
    success_count = 0
    
    for demo in demos:
        if run_command(demo["cmd"], demo["desc"]):
            success_count += 1
    
    print(f"\n{'='*60}")
    print(f"📊 Demo Summary: {success_count}/{len(demos)} commands successful")
    print(f"{'='*60}")
    
    # Show the persistence functionality
    print(f"\n🔍 Persistence Functionality Demo:")
    print("The parse_repo.py CLI now includes:")
    print("  ✅ --index flag for Qdrant indexing")
    print("  ✅ Automatic saving of qdrant_map.json (point_id → node_id)")
    print("  ✅ Automatic saving of index_status.json (metadata)")
    print("  ✅ Comprehensive logging and error handling")
    print("  ✅ Support for both local repos and git URLs")
    
    print(f"\n📝 Example full indexing command:")
    print(f"  {python_exe} parse_repo.py \\")
    print(f"    --repo https://github.com/user/repo.git \\")
    print(f"    --index \\")
    print(f"    --collection my_repo \\")
    print(f"    --qdrant-url http://localhost:6333 \\")
    print(f"    --verbose")
    
    if os.path.exists("data/demo_graph.json"):
        print(f"\n🧹 Cleaning up demo files...")
        os.remove("data/demo_graph.json")
        print("✅ Cleanup complete")

if __name__ == "__main__":
    main()
