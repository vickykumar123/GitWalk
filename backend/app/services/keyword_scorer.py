"""
Keyword-based scoring for hybrid search.

Implements simplified BM25-style scoring to complement vector search with
lexical matching. This helps catch exact term matches that vector embeddings
might miss.
"""
import re
from typing import List, Dict, Set
from collections import Counter
import math


class KeywordScorer:
    """
    Keyword-based scoring using simplified BM25 algorithm.

    BM25 (Best Matching 25) is a ranking function that scores documents based on
    query term frequency while avoiding over-weighting of common terms.

    Why use this?
    - Vector search understands semantics but may miss exact term matches
    - Keyword search catches literal matches (e.g., "RDB" in "rdb-parser.ts")
    - Hybrid approach combines both strengths
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        """
        Initialize keyword scorer with BM25 parameters.

        Args:
            k1: Term frequency saturation parameter (default: 1.5)
                Higher values = more weight to term frequency
            b: Length normalization parameter (default: 0.75)
                Higher values = more penalty for longer documents
        """
        self.k1 = k1
        self.b = b

    def extract_terms(self, text: str) -> List[str]:
        """
        Extract searchable terms from text.

        Process:
        1. Convert to lowercase
        2. Split on non-alphanumeric characters
        3. Remove stop words and short terms
        4. Keep meaningful programming terms

        Example:
            "How does the RDB parser work?"
            → ["rdb", "parser", "work"]
        """
        if not text:
            return []

        # Convert to lowercase and extract alphanumeric tokens
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())

        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'been', 'be',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those',
            'how', 'what', 'where', 'when', 'why', 'who', 'which'
        }

        # Filter stop words and short terms (< 2 chars)
        terms = [t for t in tokens if t not in stop_words and len(t) >= 2]

        return terms

    def calculate_bm25_score(
        self,
        query_terms: List[str],
        document_terms: List[str],
        avg_doc_length: float = 100.0
    ) -> float:
        """
        Calculate BM25 score for a document given query terms.

        BM25 Formula (simplified):
            score = Σ (IDF × (TF × (k1 + 1)) / (TF + k1 × (1 - b + b × (|D| / avgdl))))

        Where:
            TF = term frequency in document
            IDF = inverse document frequency (simplified as 1.0 here)
            |D| = document length
            avgdl = average document length

        Args:
            query_terms: Terms extracted from user query
            document_terms: Terms extracted from document (file path + summary)
            avg_doc_length: Average document length for normalization

        Returns:
            BM25 score (higher = more relevant)
        """
        if not query_terms or not document_terms:
            return 0.0

        # Convert to sets for faster lookup
        query_set = set(query_terms)
        doc_term_counts = Counter(document_terms)
        doc_length = len(document_terms)

        score = 0.0

        for term in query_set:
            if term not in doc_term_counts:
                continue

            # Term frequency in document
            tf = doc_term_counts[term]

            # Simplified IDF (in real BM25, this considers corpus statistics)
            # For our use case, we assume IDF = 1.0 for simplicity
            idf = 1.0

            # Length normalization factor
            length_norm = 1 - self.b + self.b * (doc_length / avg_doc_length)

            # BM25 scoring formula
            term_score = idf * (tf * (self.k1 + 1)) / (tf + self.k1 * length_norm)
            score += term_score

        # Normalize by query length to get score in [0, 1] range
        if len(query_set) > 0:
            score = score / len(query_set)

        return min(score, 1.0)  # Cap at 1.0

    def score_document(
        self,
        query: str,
        file_path: str,
        summary: str = "",
        code_names: List[str] = None
    ) -> Dict[str, float]:
        """
        Score a document against a query using keyword matching.

        Scoring strategy:
        1. Path matching (highest weight) - exact file names
        2. Summary matching (medium weight) - content description
        3. Code names matching (medium weight) - class/function names

        Args:
            query: User search query
            file_path: File path (e.g., "app/rdb-parser.ts")
            summary: File summary text
            code_names: List of class/function names in file

        Returns:
            Dict with 'keyword_score', 'path_score', 'summary_score'
        """
        query_terms = self.extract_terms(query)

        if not query_terms:
            return {
                'keyword_score': 0.0,
                'path_score': 0.0,
                'summary_score': 0.0,
                'code_names_score': 0.0
            }

        # Score 1: File path matching (most important for exact matches)
        path_terms = self.extract_terms(file_path)
        path_score = self.calculate_bm25_score(query_terms, path_terms, avg_doc_length=10.0)

        # Score 2: Summary text matching
        summary_terms = self.extract_terms(summary or "")
        summary_score = self.calculate_bm25_score(query_terms, summary_terms, avg_doc_length=100.0)

        # Score 3: Code names matching (class/function names)
        code_names_score = 0.0
        if code_names:
            code_names_text = " ".join(code_names)
            code_names_terms = self.extract_terms(code_names_text)
            code_names_score = self.calculate_bm25_score(query_terms, code_names_terms, avg_doc_length=20.0)

        # Combined keyword score (weighted average)
        # Path gets highest weight since it's most reliable
        keyword_score = (
            0.5 * path_score +           # 50% weight on file path
            0.3 * summary_score +         # 30% weight on summary
            0.2 * code_names_score        # 20% weight on code names
        )

        return {
            'keyword_score': keyword_score,
            'path_score': path_score,
            'summary_score': summary_score,
            'code_names_score': code_names_score
        }

    def apply_filename_boost(
        self,
        query: str,
        file_path: str,
        base_score: float,
        boost_factor: float = 1.3
    ) -> float:
        """
        Boost score if query terms appear in filename.

        Why this works:
        - File names are intentionally descriptive (e.g., "rdb-parser.ts")
        - If user searches "RDB parser", file "rdb-parser.ts" is likely relevant
        - Simple but effective heuristic

        Args:
            query: User search query
            file_path: File path
            base_score: Base similarity score to boost
            boost_factor: Multiplier for boost (default: 1.3 = 30% increase)

        Returns:
            Boosted score (capped at 1.0)
        """
        query_terms = set(self.extract_terms(query))
        filename = file_path.split('/')[-1]  # Get just the filename
        filename_terms = set(self.extract_terms(filename))

        # Check if any query terms appear in filename
        matching_terms = query_terms.intersection(filename_terms)

        if matching_terms:
            # Boost proportional to how many terms match
            boost_multiplier = 1 + (len(matching_terms) / len(query_terms)) * (boost_factor - 1)
            boosted_score = base_score * boost_multiplier
            return min(boosted_score, 1.0)  # Cap at 1.0

        return base_score


def hybrid_score(
    vector_score: float,
    keyword_score: float,
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3
) -> float:
    """
    Combine vector and keyword scores into final hybrid score.

    Hybrid search formula:
        final_score = (vector_weight × vector_score) + (keyword_weight × keyword_score)

    Why hybrid search?
    - Vector search: Good for semantic understanding ("parser" ≈ "parsing logic")
    - Keyword search: Good for exact matches ("RDB" in query → "RDB" in filename)
    - Combined: Best of both worlds

    Default weights:
        - 70% vector (semantic understanding is primary)
        - 30% keyword (boost exact matches)

    Args:
        vector_score: Cosine similarity from vector search (0-1)
        keyword_score: BM25-style keyword score (0-1)
        vector_weight: Weight for vector score (default: 0.7)
        keyword_weight: Weight for keyword score (default: 0.3)

    Returns:
        Combined hybrid score (0-1)
    """
    # Normalize weights to sum to 1.0
    total_weight = vector_weight + keyword_weight
    vector_weight = vector_weight / total_weight
    keyword_weight = keyword_weight / total_weight

    return (vector_weight * vector_score) + (keyword_weight * keyword_score)
