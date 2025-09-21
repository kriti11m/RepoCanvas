# backend/worker/parser/ts_parser.py
from tree_sitter import Language, Parser
import os
import ast

BUILD_LIB = os.path.join(os.path.dirname(__file__), "build", "my-languages.so")

def build_tree_sitter_lib(langs_dirs, output=BUILD_LIB):
    """
    Build a tree-sitter language library from source directories.
    
    Args:
        langs_dirs (list): List of paths to tree-sitter language source directories
        output (str): Output path for the compiled library (default: BUILD_LIB)
    
    Returns:
        str: Path to the built library
    """
    # Example: langs_dirs = ['../../vendor/tree-sitter-python', '../../vendor/tree-sitter-javascript']
    Language.build_library(output, langs_dirs)
    return output

def get_ts_parser(language_name):
    """
    Create a tree-sitter Parser for the specified language.
    
    Args:
        language_name (str): Name of the language (e.g., 'python', 'javascript', 'typescript')
    
    Returns:
        Parser: Configured tree-sitter Parser instance
    
    Raises:
        FileNotFoundError: If the shared library is not found
        Exception: If the language is not available in the library
    """
    if not os.path.exists(BUILD_LIB):
        raise FileNotFoundError(
            f"Tree-sitter shared library not found at '{BUILD_LIB}'. "
            f"Please build the library first using build_tree_sitter_lib() or ensure the file exists. "
            f"You may need to compile tree-sitter languages and place the shared library at this location."
        )
    
    try:
        LANG = Language(BUILD_LIB, language_name)
    except Exception as e:
        available_languages = _get_available_languages()
        raise Exception(
            f"Failed to load language '{language_name}' from '{BUILD_LIB}'. "
            f"Error: {e}. "
            f"Available languages in the library: {available_languages}. "
            f"Please ensure '{language_name}' is compiled into the shared library."
        )
    
    parser = Parser()
    parser.set_language(LANG)
    return parser

def _get_available_languages():
    """
    Attempt to get a list of available languages in the shared library.
    This is a helper function for error reporting.
    
    Returns:
        list: List of language names if available, otherwise a helpful message
    """
    if not os.path.exists(BUILD_LIB):
        return ["Library not found"]
    
    # Common tree-sitter language names
    common_languages = ['python', 'javascript', 'typescript', 'java', 'cpp', 'c', 'rust', 'go', 'html', 'css']
    available = []
    
    for lang in common_languages:
        try:
            Language(BUILD_LIB, lang)
            available.append(lang)
        except:
            continue
    
    return available if available else ["Unable to determine - check library compilation"]

def parse_with_ast(source_code):
    """
    Parse Python source code using the built-in ast module as a fallback.
    
    Args:
        source_code (str): Python source code to parse
    
    Returns:
        ast.AST: Abstract syntax tree node
    
    Raises:
        SyntaxError: If the source code has syntax errors
        Exception: For other parsing errors
    """
    if not isinstance(source_code, str):
        raise TypeError(f"Expected string input, got {type(source_code).__name__}")
    
    try:
        return ast.parse(source_code)
    except SyntaxError as e:
        raise SyntaxError(
            f"Python syntax error in source code at line {e.lineno}, column {e.offset}: {e.msg}"
        )
    except Exception as e:
        raise Exception(f"Failed to parse Python source code with ast module: {e}")
