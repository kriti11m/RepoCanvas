#!/usr/bin/env python3
"""
Example script demonstrating the clone_repo and tree-sitter utilities.

This script shows how to:
1. Clone a repository using clone_repo()
2. Build tree-sitter libraries
3. Parse code with tree-sitter
4. Fall back to Python AST parsing
"""

import os
import sys
import tempfile
from pathlib import Path

# Add the worker directory to the path
worker_dir = Path(__file__).parent.parent
sys.path.append(str(worker_dir))

from parser.utils import clone_repo
from parser.ts_parser import build_tree_sitter_lib, get_ts_parser, parse_with_ast


def demo_clone_repo():
    """Demonstrate repository cloning functionality."""
    print("=" * 50)
    print("DEMO: Repository Cloning")
    print("=" * 50)
    
    try:
        # Use a temporary directory for the demo
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = os.path.join(temp_dir, "demo_repo")
            
            print(f"Cloning repository to: {repo_path}")
            result = clone_repo(
                "https://github.com/octocat/Hello-World.git",
                repo_path,
                branch="master",  # This repo uses 'master' branch
                depth=1
            )
            
            print(f"✓ Successfully cloned to: {result}")
            print(f"✓ Directory exists: {os.path.exists(result)}")
            
            # List repository contents
            files = os.listdir(result)
            print(f"✓ Repository contents: {files}")
            
    except Exception as e:
        print(f"✗ Error during repository cloning: {e}")


def demo_ast_parsing():
    """Demonstrate Python AST parsing functionality."""
    print("\n" + "=" * 50)
    print("DEMO: Python AST Parsing")
    print("=" * 50)
    
    # Test with valid Python code
    valid_code = '''
def fibonacci(n):
    """Calculate the nth Fibonacci number."""
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)

# Calculate Fibonacci of 10
result = fibonacci(10)
print(f"Fibonacci(10) = {result}")
'''
    
    try:
        print("Parsing valid Python code...")
        ast_tree = parse_with_ast(valid_code)
        print(f"✓ AST parsing successful!")
        print(f"✓ Root node type: {type(ast_tree).__name__}")
        print(f"✓ Number of top-level statements: {len(ast_tree.body)}")
        
        # Print the first statement details
        if ast_tree.body:
            first_stmt = ast_tree.body[0]
            print(f"✓ First statement type: {type(first_stmt).__name__}")
            if hasattr(first_stmt, 'name'):
                print(f"✓ Function name: {first_stmt.name}")
                
    except Exception as e:
        print(f"✗ Error parsing valid code: {e}")
    
    # Test with invalid Python code
    invalid_code = "def broken_function(\n    # missing closing parenthesis and colon"
    
    try:
        print("\nTesting with invalid Python code...")
        parse_with_ast(invalid_code)
        print("✗ Unexpected: parsing succeeded for invalid code")
    except SyntaxError as e:
        print(f"✓ Expected SyntaxError caught: {e}")
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def demo_tree_sitter():
    """Demonstrate tree-sitter functionality (will show expected error without library)."""
    print("\n" + "=" * 50)
    print("DEMO: Tree-sitter Parsing")
    print("=" * 50)
    
    try:
        print("Attempting to get Python parser...")
        parser = get_ts_parser('python')
        print("✓ Tree-sitter parser created successfully!")
        
        # If we reach here, the library exists and we can test parsing
        test_code = "def hello(): return 'world'"
        tree = parser.parse(bytes(test_code, 'utf8'))
        print(f"✓ Parsing successful! Root node: {tree.root_node}")
        
    except FileNotFoundError as e:
        print(f"⚠ Expected: Tree-sitter library not found")
        print(f"  Message: {e}")
        print("  To build the library, see worker/parser/build/README.md")
        
    except Exception as e:
        print(f"✗ Unexpected error: {e}")


def demo_build_instructions():
    """Show instructions for building tree-sitter library."""
    print("\n" + "=" * 50)
    print("DEMO: Building Tree-sitter Library")
    print("=" * 50)
    
    print("To build a tree-sitter library with language support:")
    print("\n1. Clone language repositories:")
    print("   git clone https://github.com/tree-sitter/tree-sitter-python")
    print("   git clone https://github.com/tree-sitter/tree-sitter-javascript")
    print("\n2. Build the library in Python:")
    print("   from parser.ts_parser import build_tree_sitter_lib")
    print("   langs_dirs = ['path/to/tree-sitter-python', 'path/to/tree-sitter-javascript']")
    print("   build_tree_sitter_lib(langs_dirs)")
    print("\n3. Use the parser:")
    print("   from parser.ts_parser import get_ts_parser")
    print("   parser = get_ts_parser('python')")


if __name__ == "__main__":
    print("Repository and Parsing Utilities Demo")
    print("=====================================")
    
    # Run all demos
    demo_clone_repo()
    demo_ast_parsing()
    demo_tree_sitter()
    demo_build_instructions()
    
    print("\n" + "=" * 50)
    print("Demo completed!")
    print("=" * 50)
