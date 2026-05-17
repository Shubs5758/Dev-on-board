"""
AST parsing module for extracting code structure information.
Handles Python AST parsing and regex-based extraction for other languages.
"""

import ast
import re
from typing import Dict, List, Optional


def extract_python_info(file_content: str, file_path: str) -> Dict:
    """
    Extract detailed information from Python files using AST.
    
    Args:
        file_content: Content of the Python file
        file_path: Path to the file (for error reporting)
        
    Returns:
        Dictionary containing functions, classes, imports, and complexity score
    """
    result = {
        'functions': [],
        'classes': [],
        'imports': [],
        'complexity_score': 1,
        'error': None
    }
    
    try:
        tree = ast.parse(file_content)
    except SyntaxError as e:
        result['error'] = f"Syntax error: {str(e)}"
        return result
    except Exception as e:
        result['error'] = f"Parse error: {str(e)}"
        return result
    
    # Extract imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                result['imports'].append({
                    'module': alias.name,
                    'alias': alias.asname,
                    'is_from_import': False
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                result['imports'].append({
                    'module': f"{module}.{alias.name}" if module else alias.name,
                    'alias': alias.asname,
                    'is_from_import': True
                })
    
    # Extract functions and classes
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_info = {
                'name': node.name,
                'args': [arg.arg for arg in node.args.args],
                'line_number': node.lineno,
                'docstring': ast.get_docstring(node),
                'calls_made': []
            }
            
            # Extract function calls within this function
            for child in ast.walk(node):
                if isinstance(child, ast.Call):
                    if isinstance(child.func, ast.Name):
                        func_info['calls_made'].append(child.func.id)
                    elif isinstance(child.func, ast.Attribute):
                        func_info['calls_made'].append(child.func.attr)
            
            result['functions'].append(func_info)
        
        elif isinstance(node, ast.ClassDef):
            methods = []
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    methods.append({
                        'name': item.name,
                        'line_number': item.lineno
                    })
            
            result['classes'].append({
                'name': node.name,
                'methods': methods,
                'line_number': node.lineno,
                'docstring': ast.get_docstring(node)
            })
    
    # Calculate complexity score (1-5)
    complexity = 1
    
    # Factor 1: Number of functions and classes
    total_definitions = len(result['functions']) + len(result['classes'])
    if total_definitions > 20:
        complexity += 2
    elif total_definitions > 10:
        complexity += 1
    
    # Factor 2: Nesting depth (check for nested functions/classes)
    max_depth = _calculate_max_depth(tree)
    if max_depth > 3:
        complexity += 1
    
    # Factor 3: Number of imports
    if len(result['imports']) > 15:
        complexity += 1
    
    result['complexity_score'] = min(complexity, 5)
    
    return result


def _calculate_max_depth(node, current_depth=0):
    """Calculate maximum nesting depth in AST."""
    max_depth = current_depth
    
    for child in ast.iter_child_nodes(node):
        if isinstance(child, (ast.FunctionDef, ast.ClassDef, ast.For, ast.While, ast.If)):
            child_depth = _calculate_max_depth(child, current_depth + 1)
            max_depth = max(max_depth, child_depth)
    
    return max_depth


def extract_imports_regex(file_content: str, language: str) -> List[str]:
    """
    Extract imports from non-Python files using regex patterns.
    
    Args:
        file_content: Content of the file
        language: Programming language
        
    Returns:
        List of imported module names
    """
    imports = []
    
    if language in ['JavaScript', 'TypeScript', 'React JSX', 'React TSX']:
        # ES6 imports: import X from 'module'
        es6_pattern = r"import\s+(?:[\w\s{},*]+\s+from\s+)?['\"]([^'\"]+)['\"]"
        imports.extend(re.findall(es6_pattern, file_content))
        
        # require: const X = require('module')
        require_pattern = r"require\s*\(['\"]([^'\"]+)['\"]\)"
        imports.extend(re.findall(require_pattern, file_content))
    
    elif language == 'Go':
        # import "package" or import ( ... )
        single_import = r'import\s+"([^"]+)"'
        imports.extend(re.findall(single_import, file_content))
        
        multi_import = r'import\s*\((.*?)\)'
        for match in re.findall(multi_import, file_content, re.DOTALL):
            package_pattern = r'"([^"]+)"'
            imports.extend(re.findall(package_pattern, match))
    
    elif language == 'Java':
        # import package.Class;
        java_pattern = r'import\s+([\w.]+);'
        imports.extend(re.findall(java_pattern, file_content))
    
    elif language == 'Rust':
        # use crate::module;
        rust_pattern = r'use\s+([\w:]+);'
        imports.extend(re.findall(rust_pattern, file_content))
    
    elif language in ['C', 'C++']:
        # #include <header> or #include "header"
        include_pattern = r'#include\s+[<"]([^>"]+)[>"]'
        imports.extend(re.findall(include_pattern, file_content))
    
    elif language == 'Ruby':
        # require 'module'
        ruby_pattern = r"require\s+['\"]([^'\"]+)['\"]"
        imports.extend(re.findall(ruby_pattern, file_content))
    
    elif language == 'PHP':
        # require/include 'file.php'
        php_pattern = r"(?:require|include)(?:_once)?\s*['\"]([^'\"]+)['\"]"
        imports.extend(re.findall(php_pattern, file_content))
    
    elif language == 'C#':
        # using Namespace;
        csharp_pattern = r'using\s+([\w.]+);'
        imports.extend(re.findall(csharp_pattern, file_content))
    
    # Remove duplicates and return
    return list(set(imports))


def extract_functions_regex(file_content: str, language: str) -> List[Dict]:
    """
    Extract function definitions using regex for non-Python languages.
    
    Args:
        file_content: Content of the file
        language: Programming language
        
    Returns:
        List of function information dictionaries
    """
    functions = []
    
    if language in ['JavaScript', 'TypeScript', 'React JSX', 'React TSX']:
        # function name() {}
        func_pattern = r'function\s+(\w+)\s*\((.*?)\)'
        for match in re.finditer(func_pattern, file_content):
            functions.append({
                'name': match.group(1),
                'args': [arg.strip() for arg in match.group(2).split(',') if arg.strip()],
                'line_number': file_content[:match.start()].count('\n') + 1
            })
        
        # const name = () => {}
        arrow_pattern = r'(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>'
        for match in re.finditer(arrow_pattern, file_content):
            functions.append({
                'name': match.group(1),
                'args': [arg.strip() for arg in match.group(2).split(',') if arg.strip()],
                'line_number': file_content[:match.start()].count('\n') + 1
            })
    
    elif language == 'Java':
        # public/private/protected type name(args)
        java_pattern = r'(?:public|private|protected)?\s*(?:static)?\s*\w+\s+(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(java_pattern, file_content):
            functions.append({
                'name': match.group(1),
                'args': [arg.strip().split()[-1] for arg in match.group(2).split(',') if arg.strip()],
                'line_number': file_content[:match.start()].count('\n') + 1
            })
    
    elif language == 'Go':
        # func name(args) returnType
        go_pattern = r'func\s+(?:\(\w+\s+\*?\w+\)\s+)?(\w+)\s*\(([^)]*)\)'
        for match in re.finditer(go_pattern, file_content):
            functions.append({
                'name': match.group(1),
                'args': [arg.strip().split()[-1] for arg in match.group(2).split(',') if arg.strip()],
                'line_number': file_content[:match.start()].count('\n') + 1
            })
    
    return functions


def extract_classes_regex(file_content: str, language: str) -> List[Dict]:
    """
    Extract class definitions using regex for non-Python languages.
    
    Args:
        file_content: Content of the file
        language: Programming language
        
    Returns:
        List of class information dictionaries
    """
    classes = []
    
    if language in ['JavaScript', 'TypeScript', 'React JSX', 'React TSX']:
        # class ClassName
        class_pattern = r'class\s+(\w+)(?:\s+extends\s+\w+)?'
        for match in re.finditer(class_pattern, file_content):
            classes.append({
                'name': match.group(1),
                'line_number': file_content[:match.start()].count('\n') + 1,
                'methods': []
            })
    
    elif language == 'Java':
        # public class ClassName
        java_class_pattern = r'(?:public|private)?\s*class\s+(\w+)'
        for match in re.finditer(java_class_pattern, file_content):
            classes.append({
                'name': match.group(1),
                'line_number': file_content[:match.start()].count('\n') + 1,
                'methods': []
            })
    
    elif language == 'C#':
        # public class ClassName
        csharp_class_pattern = r'(?:public|private|internal)?\s*class\s+(\w+)'
        for match in re.finditer(csharp_class_pattern, file_content):
            classes.append({
                'name': match.group(1),
                'line_number': file_content[:match.start()].count('\n') + 1,
                'methods': []
            })
    
    return classes


def calculate_file_complexity(file_content: str, language: str, functions: List, classes: List) -> int:
    """
    Calculate complexity score for a file (1-5).
    
    Args:
        file_content: Content of the file
        language: Programming language
        functions: List of functions
        classes: List of classes
        
    Returns:
        Complexity score from 1 to 5
    """
    complexity = 1
    lines = len(file_content.split('\n'))
    
    # Factor 1: File size
    if lines > 500:
        complexity += 2
    elif lines > 200:
        complexity += 1
    
    # Factor 2: Number of definitions
    total_defs = len(functions) + len(classes)
    if total_defs > 15:
        complexity += 1
    
    # Factor 3: Cyclomatic complexity indicators
    complexity_keywords = ['if', 'else', 'for', 'while', 'switch', 'case', 'catch', 'try']
    keyword_count = sum(len(re.findall(r'\b' + kw + r'\b', file_content)) for kw in complexity_keywords)
    
    if keyword_count > 50:
        complexity += 1
    
    return min(complexity, 5)

# Made with Bob
