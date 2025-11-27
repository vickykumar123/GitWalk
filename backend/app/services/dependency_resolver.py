from typing import Dict, List, Optional, Set, Tuple
import os
import json
import re


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

        # Parse all tsconfig.json/jsconfig.json files for path aliases and baseUrl
        # Maps directory path to config: {"frontend": {"aliases": {"@/": "frontend/src/"}, "base_url": "frontend/src"}}
        self.tsconfig_map = {}
        self._parse_all_tsconfigs()

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

    def _strip_json_comments(self, json_str: str) -> str:
        """
        Remove comments and trailing commas from JSON string.

        tsconfig.json files often contain:
        - Single-line comments: // comment
        - Multi-line comments: /* comment */
        - Trailing commas: {"key": "value",}

        Standard JSON doesn't support these, so we strip them.
        """
        # Remove single-line comments (// ...)
        # But be careful not to remove // inside strings
        result = []
        in_string = False
        i = 0
        while i < len(json_str):
            char = json_str[i]

            # Track if we're inside a string
            if char == '"' and (i == 0 or json_str[i-1] != '\\'):
                in_string = not in_string
                result.append(char)
                i += 1
            # Check for single-line comment
            elif not in_string and char == '/' and i + 1 < len(json_str) and json_str[i+1] == '/':
                # Skip until end of line
                while i < len(json_str) and json_str[i] != '\n':
                    i += 1
            # Check for multi-line comment
            elif not in_string and char == '/' and i + 1 < len(json_str) and json_str[i+1] == '*':
                i += 2  # Skip /*
                while i + 1 < len(json_str) and not (json_str[i] == '*' and json_str[i+1] == '/'):
                    i += 1
                i += 2  # Skip */
            else:
                result.append(char)
                i += 1

        json_str = ''.join(result)

        # Remove trailing commas before } or ]
        json_str = re.sub(r',(\s*[}\]])', r'\1', json_str)

        return json_str

    def _parse_all_tsconfigs(self):
        """
        Find and parse ALL tsconfig.json/jsconfig.json files in the repository.

        Stores parsed aliases and baseUrl keyed by the config file's directory path.
        This allows matching files to their nearest config.
        """
        config_files = ['tsconfig.json', 'jsconfig.json']
        found_configs = []

        # Find all tsconfig.json and jsconfig.json files
        for path in self.file_map.keys():
            filename = path.split('/')[-1]
            if filename in config_files:
                found_configs.append(path)

        if not found_configs:
            print("⚠️ No tsconfig.json or jsconfig.json found in repository")
            return

        print(f"📋 Found {len(found_configs)} config file(s): {found_configs}")

        # Parse each config file
        for config_path in found_configs:
            config_content = self.file_map[config_path].get('content', '')
            if not config_content:
                print(f"  ⚠️ No content found for {config_path} (skipping)")
                continue

            # Get the directory containing the config file
            # e.g., "frontend/tsconfig.json" → "frontend"
            # e.g., "tsconfig.json" → ""
            path_parts = config_path.split('/')
            if len(path_parts) > 1:
                config_dir = '/'.join(path_parts[:-1])
            else:
                config_dir = ''

            try:
                # Strip comments and trailing commas (tsconfig allows these)
                clean_content = self._strip_json_comments(config_content)
                config = json.loads(clean_content)
                compiler_options = config.get('compilerOptions', {})
                paths = compiler_options.get('paths', {})
                base_url = compiler_options.get('baseUrl', '')

                # Build aliases for this config
                aliases = {}

                # Process baseUrl
                # e.g., baseUrl: "." or baseUrl: "src" or baseUrl: "./src"
                resolved_base_url = None
                if base_url:
                    # Clean up baseUrl
                    clean_base_url = base_url.lstrip('./').rstrip('/')

                    # Prepend config directory
                    if config_dir:
                        if clean_base_url:
                            resolved_base_url = f"{config_dir}/{clean_base_url}"
                        else:
                            resolved_base_url = config_dir
                    else:
                        resolved_base_url = clean_base_url if clean_base_url else None

                if paths:
                    # Parse paths configuration
                    # Format: { "@/*": ["./src/*"], "@components/*": ["./src/components/*"] }
                    for alias_pattern, target_paths in paths.items():
                        if not target_paths:
                            continue

                        # Remove trailing /* from alias (e.g., "@/*" → "@/")
                        alias = alias_pattern.rstrip('*')
                        if alias and not alias.endswith('/'):
                            alias = alias + '/'

                        # Get first target path and clean it
                        target = target_paths[0] if isinstance(target_paths, list) else target_paths
                        target = target.lstrip('./').rstrip('*')
                        if target and not target.endswith('/'):
                            target = target + '/'

                        # Paths are relative to baseUrl if set, otherwise to config dir
                        if resolved_base_url:
                            full_target = f"{resolved_base_url}/{target}"
                        elif config_dir:
                            full_target = f"{config_dir}/{target}"
                        else:
                            full_target = target

                        aliases[alias] = full_target

                # Add default aliases if not already defined
                if '@/' not in aliases:
                    if resolved_base_url:
                        aliases['@/'] = f"{resolved_base_url}/"
                    elif config_dir:
                        aliases['@/'] = f"{config_dir}/src/"
                    else:
                        aliases['@/'] = 'src/'

                if '~/' not in aliases:
                    if config_dir:
                        aliases['~/'] = f"{config_dir}/"
                    else:
                        aliases['~/'] = ''

                # Store config (aliases + baseUrl) keyed by config directory
                self.tsconfig_map[config_dir] = {
                    'aliases': aliases,
                    'base_url': resolved_base_url
                }

                print(f"  ✅ Parsed {config_path}:")
                if resolved_base_url:
                    print(f"     baseUrl: '{resolved_base_url}'")
                for alias, target in aliases.items():
                    print(f"     '{alias}' → '{target}'")

            except json.JSONDecodeError as e:
                print(f"  ⚠️ Failed to parse {config_path}: {e}")
            except Exception as e:
                print(f"  ⚠️ Error parsing {config_path}: {e}")

        print(f"✅ Loaded path aliases from {len(self.tsconfig_map)} config(s)")

    def _get_config_for_file(self, file_path: str) -> Dict:
        """
        Get the tsconfig configuration that applies to a specific file.

        Finds the nearest tsconfig.json by walking up the directory tree
        from the file's location.

        Args:
            file_path: Path of the file being processed

        Returns:
            Config dict with 'aliases' and 'base_url' keys
        """
        default_config = {
            'aliases': {'@/': 'src/', '~/': ''},
            'base_url': None
        }

        if not self.tsconfig_map:
            # No configs found, return default
            return default_config

        # Get directory of the file
        path_parts = file_path.split('/')
        if len(path_parts) > 1:
            file_dir = '/'.join(path_parts[:-1])
        else:
            file_dir = ''

        # Walk up the directory tree to find nearest config
        # e.g., for "frontend/src/components/Button.tsx"
        # check: "frontend/src/components" → not found
        # check: "frontend/src" → not found
        # check: "frontend" → found!
        current_dir = file_dir
        while True:
            if current_dir in self.tsconfig_map:
                return self.tsconfig_map[current_dir]

            # Move up one directory
            if '/' in current_dir:
                current_dir = '/'.join(current_dir.split('/')[:-1])
            elif current_dir:
                # Last level before root
                current_dir = ''
            else:
                # Reached root, check for root config
                if '' in self.tsconfig_map:
                    return self.tsconfig_map['']
                break

        # No config found, return default
        return default_config

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
        elif import_statement.startswith('@/') or import_statement.startswith('~/') or import_statement.startswith('@'):
            # Alias import: @/utils/helper, ~/components/Button, @components/Button
            return self._resolve_alias(import_statement, current_file_path, language)
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

            # Check if it's an alias import (starts with @/ or ~/)
            # These are internal, not external
            if import_path.startswith('@/') or import_path.startswith('~/'):
                return False

            # If doesn't start with . or / likely external npm package
            # But @ without / (like @radix-ui/react) is external
            if not import_path.startswith('.') and not import_path.startswith('/'):
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
        For JS/TS, uses baseUrl from tsconfig.json if available.
        """
        # For Python, convert dots to slashes
        if language == 'python':
            import_path = import_path.replace('.', '/')

        # For JS/TS, try resolving with baseUrl first
        if language in ['javascript', 'typescript']:
            config = self._get_config_for_file(current_file)
            base_url = config.get('base_url')

            if base_url:
                # Try resolving relative to baseUrl
                # e.g., baseUrl="frontend/src", import="utils/helper" → "frontend/src/utils/helper"
                base_resolved = f"{base_url}/{import_path}"
                result = self._find_file_with_extension(base_resolved, language)
                if result:
                    return result

        # Try direct match (without baseUrl)
        return self._find_file_with_extension(import_path, language)

    def _resolve_alias(self, import_path: str, current_file_path: str, language: str) -> Optional[str]:
        """
        Resolve alias imports using the nearest tsconfig.json configuration.

        Args:
            import_path: Aliased import path (e.g., "@/components/Button")
            current_file_path: Path of file containing the import
            language: Programming language

        Returns:
            Resolved path or None
        """
        # Get config for the current file (finds nearest tsconfig.json)
        config = self._get_config_for_file(current_file_path)
        aliases = config.get('aliases', {})

        # Sort aliases by length (longest first) to match most specific alias
        sorted_aliases = sorted(aliases.items(), key=lambda x: len(x[0]), reverse=True)

        for alias, replacement in sorted_aliases:
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
