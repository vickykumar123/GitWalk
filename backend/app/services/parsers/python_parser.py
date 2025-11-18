import ast
from typing import List, Dict, Optional
from app.services.parsers.base_parser import BaseParser

class PythonParser(BaseParser):
    """
    Parser for Python files using AST (Abstract Syntax Tree).

    Extracts function definitions, class definitions, and import statements.
    """

    # Register this parser for Python language
    SUPPORTED_LANGUAGES = ['python']

    def parse(self, code: str, file_path) -> Dict:
        """Parse Python code and extract functions, classes, and imports.

        Args:
            code: The Python source code as a string.
            file_path: The path of the file being parsed.
        Returns:
            A dictionary with lists of functions, classes, and imports.
        """
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            print(f"Syntax error in file {file_path}: {e}")
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "parse_error": str(e)
            }
        functions = self._extract_functions(tree)
        classes = self._extract_classes(tree)
        imports = self._extract_imports(tree)

        return {
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "parse_error": None
        }
        
    def _extract_functions(self, tree: ast.AST) -> List[Dict]:
        """
          Extract all function definitions from AST.

          Returns list of function objects with:
          - name: Function name
          - line_start: Starting line number
          - line_end: Ending line number
          - parameters: List of parameter names
          - return_type: Return type annotation (if any)
          - docstring: Function docstring
          - is_async: Whether function is async
          """
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                func_info = {
                    "name": node.name,
                    "line_start": node.lineno,
                    "line_end": node.lineno,
                    "parameters": self._extract_parameters(node),
                    "return_type": self._extract_return_type(node),
                    "docstring": ast.get_docstring(node),
                    "is_async": isinstance(node, ast.AsyncFunctionDef)
                }
                functions.append(func_info)
        return functions
    
    def _extract_classes(self, tree: ast.AST) -> List[Dict]:
        """
          Extract all class definitions from AST.

          Returns list of class objects with:
          - name: Class name
            - line_start: Starting line number
            - line_end: Ending line number
            - docstring: Class docstring
            - methods: List of method names
            - base_classes: List of parent classes
        """
        classes = []
        for node in ast.walk(tree):
              if isinstance(node, ast.ClassDef):
                  # Extract method names
                  methods = []
                  for item in node.body:
                      if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                          methods.append(item.name)

                  # Extract base classes (inheritance)
                  base_classes = []
                  for base in node.bases:
                      if isinstance(base, ast.Name):
                          base_classes.append(base.id)
                      elif isinstance(base, ast.Attribute):
                          base_classes.append(self._get_full_name(base))

                  class_info = {
                      "name": node.name,
                      "line_start": node.lineno,
                      "line_end": node.end_lineno,
                      "methods": methods,
                      "docstring": ast.get_docstring(node),
                      "base_classes": base_classes
                  }
                  classes.append(class_info)

        return classes
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
          """
          Extract all import statements.

          Returns list of imported module names:
          - "import os" → ["os"]
          - "from pathlib import Path" → ["pathlib"]
          - "from app.services import github_service" → ["app.services.github_service"]
          """
          imports = []

          for node in ast.walk(tree):
              if isinstance(node, ast.Import):
                  # Handle: import os, sys
                  for alias in node.names:
                      imports.append(alias.name)

              elif isinstance(node, ast.ImportFrom):
                  # Handle: from pathlib import Path
                  module = node.module or ''

                  # If it's "from . import X", we need to handle relative imports
                  if node.level > 0:
                      # Relative import (e.g., from ..utils import helper)
                      # We'll store this as-is for now
                      prefix = '.' * node.level
                      imports.append(f"{prefix}{module}" if module else prefix)
                  else:
                      # Absolute import
                      imports.append(module)

          # Remove duplicates and empty strings
          imports = list(set(filter(None, imports)))

          return imports

    def _extract_parameters(self, node: ast.FunctionDef) -> List[str]:
          """Extract parameter names from function definition"""
          params = []

          # Regular arguments
          for arg in node.args.args:
              params.append(arg.arg)

          # *args
          if node.args.vararg:
              params.append(f"*{node.args.vararg.arg}")

          # **kwargs
          if node.args.kwarg:
              params.append(f"**{node.args.kwarg.arg}")

          return params

    def _extract_return_type(self, node: ast.FunctionDef) -> Optional[str]:
          """Extract return type annotation if present"""
          if node.returns:
              return ast.unparse(node.returns)
          return None

    def _is_top_level(self, node: ast.FunctionDef, tree: ast.AST) -> bool:
          """
          Check if function is defined at module level (not nested inside class/function).

          For simplicity, we consider a function top-level if it's directly in the module body.
          """
          # Find module node
          module = None
          for n in ast.walk(tree):
              if isinstance(n, ast.Module):
                  module = n
                  break

          if module and node in module.body:
              return True
          return False

    def _get_full_name(self, node: ast.Attribute) -> str:
          """
          Get full name from attribute node.

          Example: ast.FunctionDef → "ast.FunctionDef"
          """
          try:
              return ast.unparse(node)
          except:
              return "Unknown"