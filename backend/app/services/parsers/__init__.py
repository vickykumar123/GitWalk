"""
Parser module for extracting structured data from source code.

Supports multiple programming languages using a registry-based factory pattern.
"""

from app.services.parsers.parser_factory import ParserFactory
from app.services.parsers.base_parser import BaseParser

__all__ = ['ParserFactory', 'BaseParser']
