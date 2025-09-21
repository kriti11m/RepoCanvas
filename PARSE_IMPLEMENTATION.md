# Repository Parser Implementation

This implementation provides comprehensive code parsing functionality for extracting functions and classes from source files, with support for tree-sitter parsing and Python AST fallback.

## Implementation Summary

### Core Functions

#### `parse_file(file_path)`
Extracts functions and classes from a single file with metadata.

**Features:**
- ✅ Tree-sitter parsing for supported languages (with fallback)
- ✅ Python AST parsing for Python files
- ✅ Automatic language detection from file extensions
- ✅ Docstring extraction
- ✅ Line number tracking
- ✅ Code snippet extraction
- ✅ Unique ID generation

**Returns:** List of node dictionaries with fields:
- `id`: Unique identifier (e.g., "function:name:file:line")
- `name`: Function/class name
- `file`: Relative file path
- `start_line`: Starting line number
- `end_line`: Ending line number
- `code`: Complete code snippet
- `doc`: Extracted docstring

#### `build_nodes(repo_root)`
Builds a complete node collection for an entire repository.

**Features:**
- ✅ Recursive directory traversal
- ✅ Automatic Python file detection
- ✅ Node aggregation across files
- ✅ Name-to-ID mapping for duplicate detection
- ✅ Excludes common directories (`.git`, `__pycache__`, etc.)

**Returns:** Tuple of `(nodes_list, name_to_node_map)`
- `nodes_list`: All parsed nodes from the repository
- `name_to_node_map`: Dict mapping names to lists of node IDs

### Supported Languages

**With Tree-sitter (when library is available):**
- Python, JavaScript, TypeScript, Java, C/C++, Rust, Go, Ruby, PHP, C#, Swift, Kotlin, Scala, HTML, CSS, JSON, YAML, XML

**With AST Fallback:**
- Python (using built-in `ast` module)

### Error Handling

- **Missing files**: Graceful handling with empty result
- **Unsupported file types**: Clear messaging and skipping
- **Tree-sitter unavailable**: Automatic fallback to AST for Python
- **Parse errors**: Detailed error messages with file context
- **Directory traversal**: Continues on individual file failures

## Usage Examples

### Parse Single File
```python
from parse_repo import parse_file

# Parse a Python file
nodes = parse_file('src/utils.py')
for node in nodes:
    print(f"{node['name']} at line {node['start_line']}")
    print(f"Doc: {node['doc']}")
```

### Build Repository Nodes
```python
from parse_repo import build_nodes

# Parse entire repository
nodes, name_map = build_nodes('/path/to/repo')

print(f"Found {len(nodes)} total nodes")
print(f"Found {len(name_map)} unique names")

# Find functions/classes with same names
for name, node_ids in name_map.items():
    if len(node_ids) > 1:
        print(f"'{name}' appears {len(node_ids)} times")
```

### Search Parsed Nodes
```python
# Find all functions containing 'parse' in name
parse_functions = [n for n in nodes if 'parse' in n['name'].lower()]

# Find well-documented functions
documented = [n for n in nodes if len(n['doc']) > 100]

# Find functions by file
file_nodes = [n for n in nodes if 'utils.py' in n['file']]
```

## Testing

Comprehensive unit tests are provided in `test_parse_repo.py`:

```bash
python test_parse_repo.py
```

**Test Coverage:**
- ✅ Single file parsing (Python)
- ✅ Multiple file parsing (repository)
- ✅ Node ID uniqueness
- ✅ Name mapping accuracy
- ✅ Error handling (missing files, unsupported types)
- ✅ AST fallback functionality

## Demo Scripts

### Basic Demo (`worker/demo_example.py`)
Shows basic functionality including repository cloning and parsing utilities.

### Comprehensive Analysis (`demo_parse_analysis.py`)
Provides detailed analysis including:
- File-by-file parsing demonstration
- Repository-wide statistics
- Name collision detection
- Documentation coverage analysis
- Search functionality examples

## File Structure

```
worker/
├── parse_repo.py           # Main implementation
├── parser/
│   ├── ts_parser.py       # Tree-sitter utilities
│   ├── utils.py           # Git cloning utilities
│   └── build/             # Tree-sitter library location
├── demo_example.py        # Basic demo
└── (other modules...)

demo_parse_analysis.py     # Comprehensive demo
test_parse_repo.py        # Unit tests
```

## Performance Notes

- **Memory Efficient**: Streams file content, doesn't load entire repository into memory
- **Selective Parsing**: Only processes relevant file types
- **Error Resilient**: Single file failures don't stop entire repository parsing
- **Caching Ready**: Node IDs are deterministic for caching implementations

## Integration Notes

The parsed nodes are designed to integrate with:
- **Graph databases**: Node IDs work as unique keys
- **Search systems**: Rich metadata for indexing
- **Analysis tools**: Structured data for pattern detection
- **Code navigation**: File paths and line numbers for linking

## Dependencies

- `tree-sitter`: For multi-language parsing (optional)
- `GitPython`: For repository cloning
- `ast`: Built-in Python AST parsing (fallback)

All error handling ensures graceful degradation when optional dependencies are unavailable.
