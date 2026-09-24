"""
Concept Extractor for Canvas Visualization

Extracts primary teaching concepts from RAG results and LLM responses
to ensure canvas displays curriculum topics, not raw user queries.

Based on research in AI-powered educational whiteboards (2025-2026).
"""

import re
from typing import List, Dict, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)


class ConceptExtractor:
    """Extracts primary teaching concepts for canvas visualization"""
    
    # Common algorithm and data structure concepts
    KNOWN_CONCEPTS = [
        'binary search', 'linear search', 'depth-first search', 'breadth-first search',
        'merge sort', 'quick sort', 'bubble sort', 'insertion sort', 'heap sort',
        'binary tree', 'binary search tree', 'balanced tree', 'avl tree', 'red-black tree',
        'linked list', 'doubly linked list', 'circular linked list',
        'stack', 'queue', 'priority queue', 'deque',
        'hash table', 'hash map', 'hash set',
        'graph', 'directed graph', 'undirected graph', 'weighted graph',
        'dynamic programming', 'greedy algorithm', 'divide and conquer',
        'recursion', 'backtracking', 'memoization',
        'array', 'string', 'matrix',
        'heap', 'trie', 'segment tree', 'fenwick tree',
        'dijkstra', 'bellman-ford', 'floyd-warshall',
        'kruskal', 'prim', 'topological sort',
        'binary search tree', 'depth-first search', 'breadth-first search'
    ]
    
    # Generic query patterns that need concept extraction
    GENERIC_PATTERNS = [
        r'\bexplain\b', r'\bshow\b', r'\bwhat\b', r'\bhow\b', r'\bwhy\b',
        r'\bconfused\b', r'\bdon\'?t understand\b', r'\bhelp\b',
        r'\bagain\b', r'\brepeat\b', r'\bmore\b', r'\banother\b',
        r'\bexample\b', r'\bclarify\b', r'\btell me\b'
    ]
    
    @classmethod
    def extract_primary_concept(
        cls,
        rag_chunks: List[Any],
        llm_response: str,
        query: str,
        intent: str = "teacher"
    ) -> Tuple[str, float]:
        """
        Extract the primary teaching concept from available context.
        
        Priority:
        1. RAG chunk topic titles (curriculum-aligned)
        2. Concept from LLM response structure
        3. Known concepts from query keywords
        4. Fallback to query (with confidence penalty)
        
        Args:
            rag_chunks: Retrieved knowledge chunks with topic metadata
            llm_response: Structured LLM teaching response
            query: Original user query
            intent: Intent classification result
            
        Returns:
            Tuple of (concept: str, confidence: float)
            confidence ranges from 0.0 (low) to 1.0 (high)
        """
        
        # Strategy 1: Extract from RAG topic titles (highest confidence)
        if rag_chunks and len(rag_chunks) > 0:
            concept = cls._extract_from_rag(rag_chunks)
            if concept:
                logger.info(f"Extracted concept from RAG: '{concept}' (confidence: 0.95)")
                return concept, 0.95
        
        # Strategy 2: Parse LLM response structure (high confidence)
        if llm_response:
            concept = cls._extract_from_llm_response(llm_response)
            if concept:
                logger.info(f"Extracted concept from LLM response: '{concept}' (confidence: 0.85)")
                return concept, 0.85
        
        # Strategy 3: Extract known concepts from query (medium confidence)
        if not cls._is_generic_query(query):
            concept = cls._extract_from_query(query)
            if concept:
                logger.info(f"Extracted concept from query keywords: '{concept}' (confidence: 0.70)")
                return concept, 0.70
        
        # Strategy 4: Try fuzzy matching on query (medium-low confidence)
        fuzzy_concept = cls._fuzzy_match_concept(query)
        if fuzzy_concept:
            logger.info(f"Fuzzy matched concept: '{fuzzy_concept}' (confidence: 0.60)")
            return fuzzy_concept, 0.60
        
        # Strategy 5: Extract capitalized or quoted terms (low-medium confidence)
        extracted_term = cls._extract_important_terms(query)
        if extracted_term and not cls._is_too_generic(extracted_term):
            logger.info(f"Extracted important term: '{extracted_term}' (confidence: 0.50)")
            return extracted_term, 0.50
        
        # Strategy 6: Fallback to cleaned query (low confidence)
        cleaned_query = cls._clean_query(query)
        logger.warning(f"Using query as concept (low confidence): '{cleaned_query}' (confidence: 0.40)")
        return cleaned_query, 0.40
    
    @classmethod
    def _extract_from_rag(cls, rag_chunks: List[Any]) -> Optional[str]:
        """Extract concept from RAG chunk topic titles"""
        try:
            # Use the most relevant chunk's topic
            for chunk in rag_chunks[:3]:  # Check top 3 chunks
                if hasattr(chunk, 'topic') and chunk.topic:
                    if hasattr(chunk.topic, 'title'):
                        title = chunk.topic.title
                        if title and len(title.strip()) > 0:
                            return title.strip()
        except Exception as e:
            logger.error(f"Error extracting from RAG: {e}")
        
        return None
    
    @classmethod
    def _extract_from_llm_response(cls, response: str) -> Optional[str]:
        """Extract concept from structured LLM response"""
        try:
            # Pattern 1: Extract from "Definition:" section
            definition_match = re.search(
                r'(?:Definition|Concept)[:\-]?\s*([^\n]{10,100})',
                response,
                re.IGNORECASE
            )
            
            if definition_match:
                definition = definition_match.group(1).strip()
                
                # Extract known algorithm/DS terms from definition
                for concept in cls.KNOWN_CONCEPTS:
                    if concept in definition.lower():
                        # Return properly capitalized concept
                        return cls._capitalize_concept(concept)
            
            # Pattern 2: Extract from first substantial line
            lines = response.split('\n')
            for line in lines[:5]:  # Check first 5 lines
                line = line.strip()
                if len(line) > 10 and not line.startswith(('1)', '2)', '3)', '-', '*')):
                    for concept in cls.KNOWN_CONCEPTS:
                        if concept in line.lower():
                            return cls._capitalize_concept(concept)
            
        except Exception as e:
            logger.error(f"Error extracting from LLM response: {e}")
        
        return None
    
    @classmethod
    def _extract_from_query(cls, query: str) -> Optional[str]:
        """Extract known concept keywords from query"""
        query_lower = query.lower()
        
        # Sort by length (longer matches first to prefer "binary search tree" over "binary search")
        sorted_concepts = sorted(cls.KNOWN_CONCEPTS, key=len, reverse=True)
        
        for concept in sorted_concepts:
            if concept in query_lower:
                return cls._capitalize_concept(concept)
        
        return None
    
    @classmethod
    def _is_generic_query(cls, query: str) -> bool:
        """Check if query is too generic for direct keyword matching"""
        query_lower = query.lower()
        
        # Check if query matches generic patterns
        for pattern in cls.GENERIC_PATTERNS:
            if re.search(pattern, query_lower):
                # Check if it also contains a specific concept
                if not cls._extract_from_query(query):
                    return True
        
        # Very short queries are likely generic
        if len(query.split()) <= 3:
            return True
        
        return False
    
    @classmethod
    def _clean_query(cls, query: str) -> str:
        """Clean and format query as a fallback concept"""
        # Remove common filler words
        filler_words = ['please', 'can you', 'could you', 'tell me', 'show me', 'explain']
        cleaned = query.lower()
        
        for filler in filler_words:
            cleaned = re.sub(r'\b' + filler + r'\b', '', cleaned, flags=re.IGNORECASE)
        
        # Clean up whitespace
        cleaned = ' '.join(cleaned.split())
        
        # Capitalize properly
        if cleaned:
            return cleaned.title()
        
        return query.title()
    
    @classmethod
    def _capitalize_concept(cls, concept: str) -> str:
        """Properly capitalize concept names"""
        # Special cases
        special_cases = {
            'avl tree': 'AVL Tree',
            'dfs': 'Depth-First Search',
            'bfs': 'Breadth-First Search',
            'bst': 'Binary Search Tree'
        }
        
        if concept.lower() in special_cases:
            return special_cases[concept.lower()]
        
        # Title case by default
        return ' '.join(word.capitalize() for word in concept.split())

    
    @classmethod
    def _fuzzy_match_concept(cls, query: str) -> Optional[str]:
        """
        Fuzzy match query against known concepts.
        Handles typos, abbreviations, and variations.
        """
        query_lower = query.lower()
        
        # First check common abbreviations and variations
        fuzzy_mappings = {
            'bsearch': 'binary search',
            'bin search': 'binary search',
            'linkedlist': 'linked list',
            'hashmap': 'hash map',
            'hashtable': 'hash table',
            'arr': 'array',
            'recurs': 'recursion',
            'iter': 'iteration',
            'dp': 'dynamic programming'
        }
        
        for abbrev, full_concept in fuzzy_mappings.items():
            if abbrev in query_lower:
                return cls._capitalize_concept(full_concept)
        
        # Then try word-based matching
        query_words = set(query_lower.split())
        best_match = None
        best_score = 0
        
        for concept in cls.KNOWN_CONCEPTS:
            concept_words = set(concept.split())
            
            # Count word overlap
            overlap = len(query_words & concept_words)
            score = overlap / len(concept_words) if concept_words else 0
            
            # Also check if concept words appear as substrings
            substring_matches = sum(
                1 for cword in concept_words 
                if any(cword in qword or qword in cword for qword in query_words)
            )
            score += (substring_matches * 0.5) / len(concept_words) if concept_words else 0
            
            if score > best_score and score >= 0.6:  # 60% threshold
                best_score = score
                best_match = concept
        
        if best_match:
            return cls._capitalize_concept(best_match)
        
        return None
    
    @classmethod
    def _extract_important_terms(cls, query: str) -> Optional[str]:
        """
        Extract important terms from query:
        - Quoted terms (in "quotes")
        - Capitalized terms (Binary Tree)
        - Technical terms with numbers/symbols (O(n))
        """
        # Extract quoted terms
        quoted_match = re.search(r'["\']([^"\']+)["\']', query)
        if quoted_match:
            return quoted_match.group(1).strip()
        
        # Extract capitalized multi-word terms
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b', query)
        if capitalized:
            return capitalized[0]
        
        # Extract terms with technical patterns (e.g., "O(n)", "log(n)")
        technical = re.findall(r'\b\w+\([^)]+\)', query)
        if technical:
            return technical[0]
        
        return None
    
    @classmethod
    def _is_too_generic(cls, term: str) -> bool:
        """Check if extracted term is too generic to be useful"""
        generic_terms = [
            'this', 'that', 'something', 'anything', 'everything',
            'help', 'explain', 'show', 'tell', 'understand',
            'question', 'answer', 'problem', 'solution'
        ]
        
        term_lower = term.lower().strip()
        return term_lower in generic_terms or len(term_lower) < 3


def extract_concept_for_visualization(
    rag_chunks: List[Any],
    llm_response: str,
    query: str,
    confidence_threshold: float = 0.60
) -> str:
    """
    Convenience function for extracting concept for canvas visualization.
    
    Args:
        rag_chunks: Retrieved knowledge chunks
        llm_response: LLM teaching response
        query: User's original query
        confidence_threshold: Minimum confidence to use extracted concept
        
    Returns:
        Primary concept string suitable for canvas visualization
    """
    concept, confidence = ConceptExtractor.extract_primary_concept(
        rag_chunks, llm_response, query
    )
    
    # If confidence is too low, try to improve or warn
    if confidence < confidence_threshold:
        logger.warning(
            f"Low confidence concept extraction: '{concept}' ({confidence:.2f}). "
            f"Consider improving RAG retrieval or query understanding."
        )
    
    return concept
