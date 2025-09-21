# Tree-sitter Build Directory

This directory should contain the compiled tree-sitter language library `my-languages.so`.

## Building the Library

To build the tree-sitter library, you need to:

1. Clone the tree-sitter language repositories you want to support:
   ```bash
   # Example for Python and JavaScript
   git clone https://github.com/tree-sitter/tree-sitter-python
   git clone https://github.com/tree-sitter/tree-sitter-javascript
   ```

2. Use the `build_tree_sitter_lib()` function to compile them:
   ```python
   from parser.ts_parser import build_tree_sitter_lib
   
   # Build library with Python and JavaScript support
   langs_dirs = [
       '/path/to/tree-sitter-python',
       '/path/to/tree-sitter-javascript'
   ]
   build_tree_sitter_lib(langs_dirs)
   ```

3. The compiled library `my-languages.so` will be placed in this directory.

## Supported Languages

Once built, you can use the following languages (depending on what you compiled):
- `python`
- `javascript`
- `typescript`
- `java`
- `cpp`
- `c`
- `rust`
- `go`
- `html`
- `css`

## Usage

```python
from parser.ts_parser import get_ts_parser

# Get a parser for Python
python_parser = get_ts_parser('python')

# Parse some code
source_code = "def hello(): return 'world'"
tree = python_parser.parse(bytes(source_code, 'utf8'))
```
