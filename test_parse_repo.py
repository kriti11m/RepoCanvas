#!/usr/bin/env python3
"""
Unit tests for parse_file and build_nodes functions.
"""

import sys
import os
import tempfile
import unittest
from pathlib import Path

# Add worker directory to path
worker_dir = Path(__file__).parent / 'worker'
sys.path.append(str(worker_dir))

from parse_repo import parse_file, build_nodes

class TestParseRepo(unittest.TestCase):
    """Test cases for repository parsing functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.test_python_code = '''
def test_function(param1, param2="default"):
    """
    A test function with parameters.
    
    Args:
        param1: First parameter
        param2: Second parameter with default
    
    Returns:
        str: Combined result
    """
    return f"{param1}-{param2}"

class TestClass:
    """A test class for demonstration."""
    
    def __init__(self, name):
        """Initialize with name."""
        self.name = name
    
    def get_name(self):
        """Get the name."""
        return self.name
    
    def set_name(self, name):
        """Set the name."""
        self.name = name

async def async_test():
    """An async test function."""
    return "async"
'''
    
    def test_parse_file_python(self):
        """Test parsing a Python file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(self.test_python_code)
            test_file = f.name
        
        try:
            nodes = parse_file(test_file)
            
            # Should find: test_function, TestClass, __init__, get_name, set_name, async_test
            self.assertEqual(len(nodes), 6)
            
            # Check function node
            func_nodes = [n for n in nodes if n['name'] == 'test_function']
            self.assertEqual(len(func_nodes), 1)
            func_node = func_nodes[0]
            
            self.assertIn('function:', func_node['id'])
            self.assertEqual(func_node['name'], 'test_function')
            self.assertTrue(func_node['start_line'] > 0)
            self.assertTrue(func_node['end_line'] >= func_node['start_line'])
            self.assertIn('def test_function', func_node['code'])
            self.assertIn('A test function', func_node['doc'])
            
            # Check class node
            class_nodes = [n for n in nodes if n['name'] == 'TestClass']
            self.assertEqual(len(class_nodes), 1)
            class_node = class_nodes[0]
            
            self.assertIn('class:', class_node['id'])
            self.assertEqual(class_node['name'], 'TestClass')
            self.assertIn('A test class', class_node['doc'])
            
            # Check async function
            async_nodes = [n for n in nodes if n['name'] == 'async_test']
            self.assertEqual(len(async_nodes), 1)
            async_node = async_nodes[0]
            self.assertIn('function:', async_node['id'])
            self.assertIn('An async test', async_node['doc'])
            
        finally:
            os.unlink(test_file)
    
    def test_parse_file_nonexistent(self):
        """Test parsing a non-existent file."""
        nodes = parse_file('/nonexistent/file.py')
        self.assertEqual(len(nodes), 0)
    
    def test_parse_file_unsupported(self):
        """Test parsing an unsupported file type."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
            f.write('some content')
            test_file = f.name
        
        try:
            nodes = parse_file(test_file)
            self.assertEqual(len(nodes), 0)
        finally:
            os.unlink(test_file)
    
    def test_build_nodes(self):
        """Test building nodes for a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple Python files
            file1_content = '''
def func1():
    """Function 1."""
    pass

class Class1:
    """Class 1."""
    pass
'''
            
            file2_content = '''
def func2():
    """Function 2."""
    pass

def func1():  # Same name as in file1
    """Different function 1."""
    pass
'''
            
            # Write files
            with open(os.path.join(temp_dir, 'file1.py'), 'w') as f:
                f.write(file1_content)
            
            with open(os.path.join(temp_dir, 'file2.py'), 'w') as f:
                f.write(file2_content)
            
            # Create a non-Python file (should be ignored)
            with open(os.path.join(temp_dir, 'readme.txt'), 'w') as f:
                f.write('Not Python')
            
            # Test build_nodes
            nodes, name_map = build_nodes(temp_dir)
            
            # Should find: func1 (x2), Class1, func2
            self.assertEqual(len(nodes), 4)
            self.assertEqual(len(name_map), 3)  # 3 unique names
            
            # Check name mapping
            self.assertIn('func1', name_map)
            self.assertEqual(len(name_map['func1']), 2)  # func1 appears twice
            
            self.assertIn('func2', name_map)
            self.assertEqual(len(name_map['func2']), 1)
            
            self.assertIn('Class1', name_map)
            self.assertEqual(len(name_map['Class1']), 1)
            
            # Verify node structure
            for node in nodes:
                self.assertIn('id', node)
                self.assertIn('name', node)
                self.assertIn('file', node)
                self.assertIn('start_line', node)
                self.assertIn('end_line', node)
                self.assertIn('code', node)
                self.assertIn('doc', node)
                
                # Check types
                self.assertIsInstance(node['id'], str)
                self.assertIsInstance(node['name'], str)
                self.assertIsInstance(node['file'], str)
                self.assertIsInstance(node['start_line'], int)
                self.assertIsInstance(node['end_line'], int)
                self.assertIsInstance(node['code'], str)
                self.assertIsInstance(node['doc'], str)
    
    def test_node_id_uniqueness(self):
        """Test that node IDs are unique."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with same function names in different files
            content = '''
def duplicate_name():
    """A function."""
    pass
'''
            
            with open(os.path.join(temp_dir, 'file1.py'), 'w') as f:
                f.write(content)
            
            with open(os.path.join(temp_dir, 'file2.py'), 'w') as f:
                f.write(content)
            
            nodes, name_map = build_nodes(temp_dir)
            
            # Should have 2 nodes with same name but different IDs
            self.assertEqual(len(nodes), 2)
            self.assertEqual(len(name_map['duplicate_name']), 2)
            
            # IDs should be different
            ids = [node['id'] for node in nodes]
            self.assertEqual(len(set(ids)), 2)  # All IDs unique


if __name__ == '__main__':
    print("Running parse_repo unit tests...")
    unittest.main(verbosity=2)
