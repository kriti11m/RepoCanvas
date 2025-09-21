"""
Repository parser configuration
"""

import os
from pathlib import Path

# Parser settings
DEFAULT_LANGUAGES = ['python', 'javascript', 'typescript']
MAX_FILE_SIZE = 1024 * 1024  # 1MB
EXCLUDED_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'venv'}
EXCLUDED_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.so', '.dylib'}

# Tree-sitter settings
TREE_SITTER_LANGUAGES = {
    'python': 'tree-sitter-python',
    'javascript': 'tree-sitter-javascript', 
    'typescript': 'tree-sitter-typescript'
}

# Output settings
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / 'data'
DEFAULT_GRAPH_FILE = DEFAULT_OUTPUT_DIR / 'graph.json'