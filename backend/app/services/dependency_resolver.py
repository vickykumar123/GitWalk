from typing import Dict, List, Optional, Set, Tuple
import os


class DependencyResolver:
    """
    Resolves import statements to actual file paths within a repository.

    Handles:
    - Relative imports (./file, ../folder/file)
    - Absolute imports (app/parser, src/utils/helper)
    - Module aliases (@/, ~/)
    - External packages (axios, pandas, etc.)
    - Multiple programming languages (JS, TS, Python, Go, etc.)
    """

    def __init__(self, repo_id: str, files: List[Dict]):
        """
        Initialize resolver with repository files.

        Args:
            repo_id: Repository ID
            files: List of file documents from MongoDB
        """
        self.repo_id = repo_id
        self.files = files

        # Build file map: {path: file_data}
        self.file_map = {f['path']: f for f in files}

        # Build lookup indices for fast resolution
        self._build_indices()

        # Language-specific extension mappings
        self.extension_map = {
            'javascript': ['.js', '.jsx', '.mjs', '.cjs'],
            'typescript': ['.ts', '.tsx', '.mts', '.cts'],
            'python': ['.py'],
            'go': ['.go'],
            'java': ['.java'],
            'rust': ['.rs'],
            'php': ['.php'],
            'cpp': ['.cpp', '.cc', '.cxx', '.hpp', '.h'],
            'c': ['.c', '.h']
        }

    def _build_indices(self):
        """Build fast lookup indices for file resolution"""
        # Index by filename (without extension)
        self.filename_index = {}

        for path in self.file_map.keys():
            filename = path.split('/')[-1]
            base_name = filename.rsplit('.', 1)[0]  # Remove extension

            if base_name not in self.filename_index:
                self.filename_index[base_name] = []
            self.filename_index[base_name].append(path)

        print(f"📚 Indexed {len(self.file_map)} files for dependency resolution")

    def resolve_all_dependencies(self) -> Dict[str, Dict]:
        """
        Resolve dependencies for all files in the repository.

        Returns:
            Dictionary mapping file paths to their resolved dependencies
        """
        print(f"\n🔗 Starting dependency resolution for {len(self.files)} files...")

        dependencies = {}

        # First pass: Resolve imports for each file
        for file_data in self.files:
            path = file_data['path']
            language = file_data.get('language', '').lower()
            imports = file_data.get('imports', [])

            if not imports:
                dependencies[path] = {
                    'imports': [],
                    'imported_by': [],
                    'external_imports': []
                }
                continue

            # Resolve each import
            resolved_imports = []
            external_imports = []

            for import_stmt in imports:
                resolved = self.resolve_import(import_stmt, path, language)

                if resolved:
                    resolved_imports.append(resolved)
                else:
                    external_imports.append(import_stmt)

            dependencies[path] = {
                'imports': list(set(resolved_imports)),  # Remove duplicates
                'imported_by': [],  # Will populate in second pass
                'external_imports': list(set(external_imports))
            }

        # Second pass: Build reverse dependencies (imported_by)
        for path, deps in dependencies.items():
            for imported_file in deps['imports']:
                if imported_file in dependencies:
                    dependencies[imported_file]['imported_by'].append(path)

        print(f"✅ Dependency resolution complete!")
        return dependencies

    def resolve_import(
        self,
        import_statement: str,
        current_file_path: str,
        language: str
    ) -> Optional[str]:
        """
        Resolve a single import statement to actual file path.

        Args:
            import_statement: Import string (e.g., "./parser", "axios")
            current_file_path: Path of file containing the import
            language: Programming language

        Returns:
            Resolved file path or None if external/not found
        """
        # Check if external package
        if self._is_external_package(import_statement, language):
            return None

        # Determine resolution strategy
        if import_statement.startswith('.'):
            # Relative import: ./parser, ../config/server
            return self._resolve_relative(import_statement, current_file_path, language)
        elif import_statement.startswith('@/') or import_statement.startswith('~/'):
            # Alias import: @/utils/helper, ~/components/Button
            return self._resolve_alias(import_statement, language)
        else:
            # Absolute import: app/parser, src/utils/helper
            return self._resolve_absolute(import_statement, current_file_path, language)

    def _is_external_package(self, import_path: str, language: str) -> bool:
        """
        Check if import is an external package (not a local file).

        Args:
            import_path: Import statement
            language: Programming language

        Returns:
            True if external package, False if local file
        """
        # Common external package indicators
        if language in ['javascript', 'typescript']:
            # Node.js built-ins
            node_builtins = {
                'fs', 'path', 'http', 'https', 'crypto', 'buffer', 'stream',
                'url', 'util', 'events', 'os', 'net', 'tls', 'child_process'
            }

            base_package = import_path.split('/')[0]

            # Check if it's a built-in
            if base_package in node_builtins:
                return True

            # If doesn't start with . or / or @/, likely external
            if not import_path.startswith('.') and not import_path.startswith('/') and not import_path.startswith('@/'):
                return True

        elif language == 'python':
            # Python standard library (common ones)
            python_stdlib = {
                'os', 'sys', 'json', 're', 'datetime', 'asyncio', 'typing',
                'pathlib', 'collections', 'itertools', 'functools', 'unittest',
                'pytest', 'flask', 'django', 'pandas', 'numpy', 'requests'
            }

            base_module = import_path.split('.')[0]

            if base_module in python_stdlib:
                return True

            # If doesn't start with ., likely external
            if not import_path.startswith('.'):
                # Check if it exists as absolute path in repo
                if not self._find_file_with_extension(import_path.replace('.', '/'), language):
                    return True

        elif language == 'go':
            # Go external packages start with domain (github.com, etc)
            if not import_path.startswith('.') and '.' in import_path.split('/')[0]:
                return True

        return False

    def _resolve_relative(
        self,
        import_path: str,
        current_file: str,
        language: str
    ) -> Optional[str]:
        """
        Resolve relative import (./file, ../folder/file).

        Args:
            import_path: Relative import path
            current_file: Current file path
            language: Programming language

        Returns:
            Resolved absolute path or None
        """
        # Get directory of current file
        current_dir = '/'.join(current_file.split('/')[:-1])

        # Remove leading ./
        clean_path = import_path
        if clean_path.startswith('./'):
            clean_path = clean_path[2:]

        # Process path parts
        parts = clean_path.split('/')
        path_parts = current_dir.split('/') if current_dir else []

        for part in parts:
            if part == '..':
                # Go up one directory
                if path_parts:
                    path_parts.pop()
            elif part and part != '.':
                path_parts.append(part)

        # Construct resolved path
        resolved_base = '/'.join(path_parts)

        # Try to find file with extensions
        return self._find_file_with_extension(resolved_base, language)

    def _resolve_absolute(
        self,
        import_path: str,
        current_file: str,
        language: str
    ) -> Optional[str]:
        """
        Resolve absolute import (app/parser, src/utils/helper).

        For Python, also handles package imports (app.parser → app/parser.py).
        """
        # For Python, convert dots to slashes
        if language == 'python':
            import_path = import_path.replace('.', '/')

        # Try direct match
        return self._find_file_with_extension(import_path, language)

    def _resolve_alias(self, import_path: str, language: str) -> Optional[str]:
        """
        Resolve alias imports (@/ → src/, ~/ → root).

        Args:
            import_path: Aliased import path
            language: Programming language

        Returns:
            Resolved path or None
        """
        # Common alias mappings
        aliases = {
            '@/': 'src/',
            '~/': '',
            '@': 'src'
        }

        for alias, replacement in aliases.items():
            if import_path.startswith(alias):
                resolved = import_path.replace(alias, replacement, 1)
                return self._find_file_with_extension(resolved, language)

        return None

    def _find_file_with_extension(
        self,
        base_path: str,
        language: str
    ) -> Optional[str]:
        """
        Try to find file with various extensions.

        Tries:
        1. Exact path
        2. Path + language extensions (.ts, .js, etc.)
        3. Path + /index + extensions

        Args:
            base_path: Base path without extension
            language: Programming language

        Returns:
            Found file path or None
        """
        # Try exact match first
        if base_path in self.file_map:
            return base_path

        # Get possible extensions for language
        extensions = self.extension_map.get(language, [])

        # Try with each extension
        for ext in extensions:
            candidate = f"{base_path}{ext}"
            if candidate in self.file_map:
                return candidate

        # Try index files (for directory imports)
        index_names = ['index', '__init__']
        for index_name in index_names:
            for ext in extensions:
                candidate = f"{base_path}/{index_name}{ext}"
                if candidate in self.file_map:
                    return candidate

        return None

    def get_dependency_stats(self, dependencies: Dict[str, Dict]) -> Dict:
        """
        Calculate dependency statistics.

        Args:
            dependencies: Resolved dependencies map

        Returns:
            Statistics dictionary
        """
        total_files = len(dependencies)
        total_internal_deps = sum(len(deps['imports']) for deps in dependencies.values())
        total_external_deps = sum(len(deps['external_imports']) for deps in dependencies.values())

        # Find most imported files
        import_counts = {}
        for path, deps in dependencies.items():
            import_counts[path] = len(deps['imported_by'])

        most_imported = sorted(
            import_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # Find files with most dependencies
        dependency_counts = {}
        for path, deps in dependencies.items():
            dependency_counts[path] = len(deps['imports'])

        most_dependencies = sorted(
            dependency_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        return {
            'total_files': total_files,
            'total_internal_dependencies': total_internal_deps,
            'total_external_dependencies': total_external_deps,
            'average_dependencies_per_file': total_internal_deps / total_files if total_files > 0 else 0,
            'most_imported_files': [
                {'path': path, 'imported_by_count': count}
                for path, count in most_imported
            ],
            'files_with_most_dependencies': [
                {'path': path, 'dependency_count': count}
                for path, count in most_dependencies
            ]
        }
