from typing import List, Dict, Optional
from app.services.parsers.base_parser import BaseParser

try:
    from tree_sitter import Language, Parser
    from tree_sitter_language_pack import get_parser
    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False
    print("⚠️ tree-sitter not available. Install with: pip install tree-sitter tree-sitter-language-pack")


class TreeSitterParser(BaseParser):
    """
    Generic parser using tree-sitter for multiple languages.

    Supports: JavaScript, TypeScript, Go, Java, Rust, C/C++, PHP
    """

    # Register this parser for multiple languages
    SUPPORTED_LANGUAGES = [
        'javascript',
        'typescript',
        'tsx',  # TypeScript + JSX
        'jsx',  # JavaScript + JSX
        'go',
        'java',
        'rust',
        'cpp',
        'c',
        'php'
    ]

    # Language-specific query patterns for extracting functions
    FUNCTION_QUERIES = {
        'javascript': """
            (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params) @function.def

            (arrow_function) @function.def

            (method_definition
                name: (property_identifier) @function.name
                parameters: (formal_parameters) @function.params) @function.def
        """,
        'typescript': """
            (function_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params) @function.def

            (arrow_function) @function.def

            (method_definition
                name: (property_identifier) @function.name
                parameters: (formal_parameters) @function.params) @function.def
        """,
        'go': """
            (function_declaration
                name: (identifier) @function.name
                parameters: (parameter_list) @function.params) @function.def

            (method_declaration
                name: (field_identifier) @function.name
                parameters: (parameter_list) @function.params) @function.def
        """,
        'java': """
            (method_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params) @function.def

            (constructor_declaration
                name: (identifier) @function.name
                parameters: (formal_parameters) @function.params) @function.def
        """,
        'rust': """
            (function_item
                name: (identifier) @function.name
                parameters: (parameters) @function.params) @function.def
        """,
        'cpp': """
            (function_definition
                declarator: (function_declarator
                    declarator: (identifier) @function.name
                    parameters: (parameter_list) @function.params)) @function.def
        """,
        'c': """
            (function_definition
                declarator: (function_declarator
                    declarator: (identifier) @function.name
                    parameters: (parameter_list) @function.params)) @function.def
        """,
        'php': """
            (function_definition
                name: (name) @function.name
                parameters: (formal_parameters) @function.params) @function.def

            (method_declaration
                name: (name) @function.name
                parameters: (formal_parameters) @function.params) @function.def
        """
    }

    # Class query patterns
    CLASS_QUERIES = {
        'javascript': """
            (class_declaration
                name: (identifier) @class.name) @class.def
        """,
        'typescript': """
            (class_declaration
                name: (type_identifier) @class.name) @class.def

            (interface_declaration
                name: (type_identifier) @class.name) @class.def
        """,
        'go': """
            (type_declaration
                (type_spec
                    name: (type_identifier) @class.name)) @class.def
        """,
        'java': """
            (class_declaration
                name: (identifier) @class.name) @class.def

            (interface_declaration
                name: (identifier) @class.name) @class.def
        """,
        'rust': """
            (struct_item
                name: (type_identifier) @class.name) @class.def

            (enum_item
                name: (type_identifier) @class.name) @class.def

            (trait_item
                name: (type_identifier) @class.name) @class.def
        """,
        'cpp': """
            (class_specifier
                name: (type_identifier) @class.name) @class.def

            (struct_specifier
                name: (type_identifier) @class.name) @class.def
        """,
        'c': """
            (struct_specifier
                name: (type_identifier) @class.name) @class.def
        """,
        'php': """
            (class_declaration
                name: (name) @class.name) @class.def

            (interface_declaration
                name: (name) @class.name) @class.def
        """
    }

    # Import query patterns
    IMPORT_QUERIES = {
        'javascript': """
            (import_statement
                source: (string) @import.source)
        """,
        'typescript': """
            (import_statement
                source: (string) @import.source)
        """,
        'go': """
            (import_spec
                path: (interpreted_string_literal) @import.source)
        """,
        'java': """
            (import_declaration
                (scoped_identifier) @import.source)
        """,
        'rust': """
            (use_declaration
                argument: (_) @import.source)
        """,
        'cpp': """
            (preproc_include
                path: (_) @import.source)
        """,
        'c': """
            (preproc_include
                path: (_) @import.source)
        """,
        'php': """
            (use_declaration
                (name) @import.source)
        """
    }

    def __init__(self):
        if not TREE_SITTER_AVAILABLE:
            raise ImportError("tree-sitter is not installed")

    def parse(self, code: str, file_path: str) -> Dict:
        """
        Parse code using tree-sitter.

        Args:
            code: Source code as string
            file_path: File path (for detecting language)

        Returns:
            Dictionary with functions, classes, and imports
        """
        # Detect language from file extension
        language = self._detect_language(file_path)

        if not language:
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "parse_error": "Could not detect language from file path"
            }

        try:
            # Get parser for language
            # Note: get_parser returns a Parser object directly
            parser = get_parser(language)

            # Parse the code
            tree = parser.parse(bytes(code, "utf8"))
            root_node = tree.root_node

            # Extract functions, classes, imports
            functions = self._extract_functions_ts(root_node, code, language)
            classes = self._extract_classes_ts(root_node, code, language)
            imports = self._extract_imports_ts(root_node, code, language)

            return {
                "functions": functions,
                "classes": classes,
                "imports": imports,
                "parse_error": None
            }

        except Exception as e:
            print(f"⚠️ Error parsing {file_path}: {e}")
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "parse_error": str(e)
            }

    def _detect_language(self, file_path: str) -> Optional[str]:
        """Detect language from file extension"""
        if file_path.endswith('.js'):
            return 'javascript'
        elif file_path.endswith('.jsx'):
            return 'javascript'
        elif file_path.endswith('.ts'):
            return 'typescript'
        elif file_path.endswith('.tsx'):
            return 'typescript'
        elif file_path.endswith('.go'):
            return 'go'
        elif file_path.endswith('.java'):
            return 'java'
        elif file_path.endswith('.rs'):
            return 'rust'
        elif file_path.endswith(('.cpp', '.cc', '.cxx', '.hpp', '.h')):
            return 'cpp'
        elif file_path.endswith('.c'):
            return 'c'
        elif file_path.endswith('.php'):
            return 'php'
        return None

    def _extract_functions_ts(self, root_node, code: str, language: str) -> List[Dict]:
        """Extract functions using tree-sitter"""
        functions = []

        # Simple traversal (without query API for now)
        self._traverse_functions(root_node, code, language, functions)

        return functions

    def _traverse_functions(self, node, code: str, language: str, functions: List):
        """Recursively traverse tree to find functions"""
        # Function node types by language
        function_types = {
            'javascript': ['function_declaration', 'method_definition', 'arrow_function'],
            'typescript': ['function_declaration', 'method_definition', 'arrow_function'],
            'go': ['function_declaration', 'method_declaration'],
            'java': ['method_declaration', 'constructor_declaration'],
            'rust': ['function_item'],
            'cpp': ['function_definition'],
            'c': ['function_definition'],
            'php': ['function_definition', 'method_declaration']
        }

        if node.type in function_types.get(language, []):
            func_info = {
                "name": self._extract_node_name(node, code),
                "line_start": node.start_point[0] + 1,
                "line_end": node.end_point[0] + 1,
                "parameters": [],
                "docstring": None
            }
            functions.append(func_info)

        # Recurse into children
        for child in node.children:
            self._traverse_functions(child, code, language, functions)

    def _extract_classes_ts(self, root_node, code: str, language: str) -> List[Dict]:
        """Extract classes using tree-sitter"""
        classes = []
        self._traverse_classes(root_node, code, language, classes)
        return classes

    def _traverse_classes(self, node, code: str, language: str, classes: List):
        """Recursively traverse tree to find classes"""
        class_types = {
            'javascript': ['class_declaration'],
            'typescript': ['class_declaration', 'interface_declaration'],
            'go': ['type_declaration'],
            'java': ['class_declaration', 'interface_declaration'],
            'rust': ['struct_item', 'enum_item', 'trait_item'],
            'cpp': ['class_specifier', 'struct_specifier'],
            'c': ['struct_specifier'],
            'php': ['class_declaration', 'interface_declaration']
        }

        if node.type in class_types.get(language, []):
            class_info = {
                "name": self._extract_node_name(node, code),
                "line_start": node.start_point[0] + 1,
                "line_end": node.end_point[0] + 1,
                "methods": [],
                "docstring": None
            }
            classes.append(class_info)

        for child in node.children:
            self._traverse_classes(child, code, language, classes)

    def _extract_imports_ts(self, root_node, code: str, language: str) -> List[str]:
        """Extract imports using tree-sitter"""
        imports = []
        self._traverse_imports(root_node, code, language, imports)
        return list(set(imports))  # Remove duplicates

    def _traverse_imports(self, node, code: str, language: str, imports: List):
        """Recursively traverse tree to find imports"""
        import_types = {
            'javascript': ['import_statement'],
            'typescript': ['import_statement'],
            'go': ['import_declaration'],
            'java': ['import_declaration'],
            'rust': ['use_declaration'],
            'cpp': ['preproc_include'],
            'c': ['preproc_include'],
            'php': ['namespace_use_declaration']
        }

        if node.type in import_types.get(language, []):
            import_text = code[node.start_byte:node.end_byte]
            # Extract the actual module name from the import statement
            imports.append(import_text.strip())

        for child in node.children:
            self._traverse_imports(child, code, language, imports)

    def _extract_node_name(self, node, code: str) -> str:
        """Extract name from a node"""
        for child in node.children:
            if 'identifier' in child.type or child.type == 'name':
                return code[child.start_byte:child.end_byte]
        return "anonymous"
