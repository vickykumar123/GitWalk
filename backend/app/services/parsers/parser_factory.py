from typing import Optional, List
from app.services.parsers.base_parser import BaseParser

# Import all parsers to trigger auto-registration
from app.services.parsers.python_parser import PythonParser
from app.services.parsers.tree_sitter_parser import TreeSitterParser


class ParserFactory:
    """
    Factory for creating language parsers using the Registry Pattern.

    This factory uses the registry in BaseParser to automatically
    discover and create parsers without hardcoded if/elif chains.

    To add a new language parser:
    1. Create a class that inherits from BaseParser
    2. Set SUPPORTED_LANGUAGES = ['your_language']
    3. Implement the parse() method
    4. Import it in this file
    5. Done! The parser auto-registers itself.
    """

    @staticmethod
    def get_parser(language: str) -> Optional[BaseParser]:
        """
        Get parser for a specific language.

        Args:
            language: Language name (e.g., "python", "javascript", "go")

        Returns:
            Parser instance or None if language not supported

        Example:
            parser = ParserFactory.get_parser("python")
            if parser:
                result = parser.parse(code, "file.py")
        """
        return BaseParser.get_parser(language)

    @staticmethod
    def get_supported_languages() -> List[str]:
        """
        Get list of all supported languages.

        Returns:
            List of language names

        Example:
            languages = ParserFactory.get_supported_languages()
            # ['python', 'javascript', 'typescript', 'go', ...]
        """
        return BaseParser.get_supported_languages()

    @staticmethod
    def is_supported(language: str) -> bool:
        """
        Check if a language is supported.

        Args:
            language: Language name

        Returns:
            True if language is supported, False otherwise

        Example:
            if ParserFactory.is_supported("python"):
                print("Python is supported!")
        """
        return BaseParser.is_supported(language)

    @staticmethod
    def parse_file(code: str, file_path: str, language: str) -> dict:
        """
        Parse a file using the appropriate parser.

        This is a convenience method that gets the parser,
        checks if it exists, and parses the code.

        Args:
            code: Source code as string
            file_path: File path (for error reporting)
            language: Programming language

        Returns:
            Parse result dictionary with functions, classes, imports

        Example:
            result = ParserFactory.parse_file(
                code="def hello(): pass",
                file_path="test.py",
                language="python"
            )
            print(result['functions'])  # [{'name': 'hello', ...}]
        """
        parser = ParserFactory.get_parser(language)

        if parser is None:
            return {
                "functions": [],
                "classes": [],
                "imports": [],
                "parse_error": f"Unsupported language: {language}"
            }

        return parser.parse(code, file_path)


# Example usage and testing
if __name__ == "__main__":
    print("=== Parser Factory Test ===\n")

    # Show all supported languages
    print(f"Supported languages: {ParserFactory.get_supported_languages()}\n")

    # Test Python parser
    python_code = """
import os
from pathlib import Path

class FileManager:
    '''Manages file operations'''

    def read_file(self, path: str) -> str:
        '''Read file contents'''
        return Path(path).read_text()

def main():
    '''Main function'''
    fm = FileManager()
    content = fm.read_file('test.txt')
    print(content)
"""

    print("Testing Python parser:")
    result = ParserFactory.parse_file(python_code, "test.py", "python")
    print(f"Functions: {len(result['functions'])}")
    print(f"Classes: {len(result['classes'])}")
    print(f"Imports: {result['imports']}")
    print()

    # Test JavaScript parser
    js_code = """
import { useState } from 'react';
import axios from 'axios';

class UserService {
    async getUser(id) {
        return axios.get(`/api/users/${id}`);
    }
}

function Hello({ name }) {
    const [count, setCount] = useState(0);
    return <div>Hello {name}</div>;
}
"""

    print("Testing JavaScript parser:")
    result = ParserFactory.parse_file(js_code, "test.js", "javascript")
    print(f"Functions: {len(result['functions'])}")
    print(f"Classes: {len(result['classes'])}")
    print(f"Imports: {len(result['imports'])}")
    print()

    # Test unsupported language
    print("Testing unsupported language (kotlin):")
    result = ParserFactory.parse_file("fun main() {}", "test.kt", "kotlin")
    print(f"Error: {result['parse_error']}")
