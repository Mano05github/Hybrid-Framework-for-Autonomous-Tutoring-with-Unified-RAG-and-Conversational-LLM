"""
Omni-RAG Orchestrator - Intelligent Multi-Strategy RAG System

Implements:
1. Adaptive Routing (No RAG / Single-Hop / Multi-Hop / Iterative)
2. Query Decomposition for complex queries
3. Self-Correction with Critic Loop
4. Response Fusion for multi-hop queries

Author: Vaathiyar Team
Phase: 9 (Omni-RAG Implementation)
"""

import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from .hybrid_retriever import HybridRetriever, RetrievalResult

logger = logging.getLogger(__name__)


class RAGStrategy(Enum):
    """RAG execution strategies."""
    NO_RAG = "no_rag"          # Direct LLM response (greetings, simple queries)
    SINGLE_HOP = "single_hop"  # Standard RAG (one retrieval pass)
    MULTI_HOP = "multi_hop"    # Multiple retrieval passes (comparative queries)
    ITERATIVE = "iterative"    # Iterative refinement (complex reasoning)


@dataclass
class RAGQuery:
    """Structured RAG query with metadata."""
    text: str
    strategy: RAGStrategy
    sub_queries: Optional[List[str]] = None
    complexity_score: int = 0
    requires_comparison: bool = False


@dataclass
class RAGResponse:
    """Structured RAG response with provenance."""
    answer: str
    context_used: List[RetrievalResult]
    strategy: RAGStrategy
    confidence: float
    sources: List[str]
    is_verified: bool = False


class QueryAnalyzer:
    """
    Analyzes queries to determine optimal RAG strategy.
    Works with Supervisor's ComplexityAnalyzer for routing decisions.
    """
    
    # Keywords that indicate no RAG needed
    NO_RAG_PATTERNS = [
        "hello", "hi", "hey", "thanks", "thank you", "bye", "goodbye",
        "how are you", "what's up", "who are you"
    ]
    
    # Keywords for comparative/multi-hop queries
    COMPARISON_KEYWORDS = [
        "compare", "difference", "versus", "vs", "better", "worse",
        "similarities", "contrast", "both", "either"
    ]
    
    # Keywords for iterative/reasoning queries
    ITERATIVE_KEYWORDS = [
        "why", "explain how", "walk me through", "step by step",
        "prove", "derive", "analyze"
    ]
    
    def analyze(self, query: str, complexity_score: int = None) -> RAGQuery:
        """
        Analyze query and determine optimal RAG strategy.
        
        Args:
            query: User query
            complexity_score: Optional complexity score from Supervisor
        
        Returns:
            RAGQuery with strategy and metadata
        """
        query_lower = query.lower().strip()
        
        # Strategy 1: No RAG (simple greetings)
        if any(pattern in query_lower for pattern in self.NO_RAG_PATTERNS):
            return RAGQuery(
                text=query,
                strategy=RAGStrategy.NO_RAG,
                complexity_score=0
            )
        
        # Strategy 2: Multi-Hop (comparative queries)
        if any(keyword in query_lower for keyword in self.COMPARISON_KEYWORDS):
            sub_queries = self._decompose_comparison(query)
            return RAGQuery(
                text=query,
                strategy=RAGStrategy.MULTI_HOP,
                sub_queries=sub_queries,
                complexity_score=complexity_score or 70,
                requires_comparison=True
            )
        
        # Strategy 3: Iterative (complex reasoning)
        if any(keyword in query_lower for keyword in self.ITERATIVE_KEYWORDS) or \
           (complexity_score and complexity_score > 60):
            sub_queries = self._decompose_iterative(query)
            return RAGQuery(
                text=query,
                strategy=RAGStrategy.ITERATIVE,
                sub_queries=sub_queries,
                complexity_score=complexity_score or 80
            )
        
        # Strategy 4: Single-Hop (standard RAG)
        return RAGQuery(
            text=query,
            strategy=RAGStrategy.SINGLE_HOP,
            complexity_score=complexity_score or 40
        )
    
    def _decompose_comparison(self, query: str) -> List[str]:
        """
        Decompose comparative query into sub-queries.
        
        Example: "Compare quicksort vs mergesort" ->
                 ["Explain quicksort", "Explain mergesort"]
        """
        # Simple heuristic decomposition
        keywords = ["compare", "versus", "vs", "difference between"]
        
        for keyword in keywords:
            if keyword in query.lower():
                # Extract entities (very basic)
                parts = query.lower().split(keyword)
                if len(parts) == 2:
                    entity1 = parts[0].strip()
                    entity2 = parts[1].strip().split("and")[0].strip()
                    
                    return [
                        f"Explain {entity1}",
                        f"Explain {entity2}"
                    ]
        
        # Fallback: return original query
        return [query]
    
    def _decompose_iterative(self, query: str) -> List[str]:
        """
        Decompose complex query into reasoning steps.
        
        Example: "Why is quicksort O(n log n)?" ->
                 ["What is quicksort algorithm", "How to calculate time complexity", "Derive quicksort complexity"]
        """
        # For now, return single query (can be enhanced with LLM-based decomposition)
        return [query]


class OmniRAGOrchestrator:
    """
    Advanced RAG Orchestrator implementing adaptive multi-strategy retrieval.
    
    Supports:
    - No RAG: Direct LLM response
    - Single-Hop: Standard RAG
    - Multi-Hop: Multiple retrieval passes with fusion
    - Iterative: Step-by-step reasoning with refinement
    - Self-Correction: Critic loop for hallucination detection
    """
    
    def __init__(
        self,
        retriever: Optional[HybridRetriever] = None,
        use_critic: bool = True,
        max_iterations: int = 3
    ):
        """
        Initialize Omni-RAG Orchestrator.
        
        Args:
            retriever: HybridRetriever instance (creates new if None)
            use_critic: Whether to use self-correction
            max_iterations: Max iterations for iterative RAG
        """
        self.retriever = retriever or HybridRetriever()
        self.query_analyzer = QueryAnalyzer()
        self.use_critic = use_critic
        self.max_iterations = max_iterations
        
        logger.info("OmniRAGOrchestrator initialized")
    
    def retrieve(
        self,
        query: str,
        complexity_score: Optional[int] = None,
        user_context: Optional[Dict] = None
    ) -> RAGResponse:
        """
        Main retrieval method with adaptive routing.
        
        Args:
            query: User query
            complexity_score: Optional complexity score from Supervisor
            user_context: Optional user context (mastery level, history)
        
        Returns:
            RAGResponse with answer and provenance
        """
        # Step 1: Analyze query
        rag_query = self.query_analyzer.analyze(query, complexity_score)
        
        logger.info(f"[Omni-RAG] Strategy: {rag_query.strategy.value} | Complexity: {rag_query.complexity_score}")
        
        # Step 2: Route to appropriate strategy
        if rag_query.strategy == RAGStrategy.NO_RAG:
            return self._no_rag_response(rag_query)
        elif rag_query.strategy == RAGStrategy.SINGLE_HOP:
            return self._single_hop_rag(rag_query, user_context)
        elif rag_query.strategy == RAGStrategy.MULTI_HOP:
            return self._multi_hop_rag(rag_query, user_context)
        elif rag_query.strategy == RAGStrategy.ITERATIVE:
            return self._iterative_rag(rag_query, user_context)
        else:
            return self._single_hop_rag(rag_query, user_context)
    
    def _no_rag_response(self, rag_query: RAGQuery) -> RAGResponse:
        """
        Handle queries that don't need RAG.
        Returns empty context, letting LLM generate directly.
        """
        return RAGResponse(
            answer="",  # LLM will generate
            context_used=[],
            strategy=RAGStrategy.NO_RAG,
            confidence=1.0,
            sources=[],
            is_verified=True
        )
    
    def _single_hop_rag(
        self,
        rag_query: RAGQuery,
        user_context: Optional[Dict] = None
    ) -> RAGResponse:
        """
        Standard RAG: Single retrieval pass.
        
        Flow: Query -> Retrieve -> Re-rank -> Return
        """
        # Retrieve context
        results = self.retriever.retrieve(rag_query.text, k=3, method="hybrid")
        
        if not results:
            logger.warning(f"No results for query: {rag_query.text}")
            return RAGResponse(
                answer="",
                context_used=[],
                strategy=RAGStrategy.SINGLE_HOP,
                confidence=0.0,
                sources=[]
            )
        
        # Extract sources
        sources = list(set([r.source for r in results]))
        
        # Calculate confidence (based on top result score)
        confidence = results[0].score if results else 0.0
        
        return RAGResponse(
            answer="",  # LLM will generate with context
            context_used=results,
            strategy=RAGStrategy.SINGLE_HOP,
            confidence=confidence,
            sources=sources,
            is_verified=False  # Will be verified by critic if enabled
        )
    
    def _multi_hop_rag(
        self,
        rag_query: RAGQuery,
        user_context: Optional[Dict] = None
    ) -> RAGResponse:
        """
        Multi-Hop RAG: Multiple retrieval passes with fusion.
        
        Flow: Query -> Decompose -> Retrieve Each -> Fuse -> Return
        
        Example: "Compare quicksort vs mergesort"
                 -> Retrieve quicksort context
                 -> Retrieve mergesort context
                 -> Fuse both contexts
        """
        all_results = []
        all_sources = set()
        
        # Execute sub-queries
        sub_queries = rag_query.sub_queries or [rag_query.text]
        
        for sub_query in sub_queries:
            logger.info(f"[Multi-Hop] Sub-query: {sub_query}")
            results = self.retriever.retrieve(sub_query, k=2, method="hybrid")
            
            all_results.extend(results)
            all_sources.update([r.source for r in results])
        
        # De-duplicate and re-rank
        all_results = self._deduplicate_results(all_results)
        
        # Limit to top K
        all_results = all_results[:5]
        
        confidence = sum(r.score for r in all_results) / len(all_results) if all_results else 0.0
        
        return RAGResponse(
            answer="",
            context_used=all_results,
            strategy=RAGStrategy.MULTI_HOP,
            confidence=confidence,
            sources=list(all_sources),
            is_verified=False
        )
    
    def _iterative_rag(
        self,
        rag_query: RAGQuery,
        user_context: Optional[Dict] = None
    ) -> RAGResponse:
        """
        Iterative RAG: Step-by-step refinement.
        
        Flow: Query -> Retrieve -> Generate -> Check -> (Re-retrieve if needed) -> Return
        
        Useful for complex reasoning queries.
        """
        all_results = []
        all_sources = set()
        
        current_query = rag_query.text
        iterations = 0
        
        while iterations < self.max_iterations:
            logger.info(f"[Iterative RAG] Iteration {iterations + 1}: {current_query}")
            
            # Retrieve
            results = self.retriever.retrieve(current_query, k=3, method="hybrid")
            
            if not results:
                break
            
            all_results.extend(results)
            all_sources.update([r.source for r in results])
            
            # For now, break after first iteration
            # In full implementation, LLM would generate intermediate answer
            # and decide if more retrieval is needed
            break
        
        # De-duplicate
        all_results = self._deduplicate_results(all_results)
        all_results = all_results[:5]
        
        confidence = sum(r.score for r in all_results) / len(all_results) if all_results else 0.0
        
        return RAGResponse(
            answer="",
            context_used=all_results,
            strategy=RAGStrategy.ITERATIVE,
            confidence=confidence,
            sources=list(all_sources),
            is_verified=False
        )
    
    def _deduplicate_results(self, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Remove duplicate results based on content similarity.
        
        Args:
            results: List of retrieval results
        
        Returns:
            De-duplicated list
        """
        seen_contents = set()
        unique_results = []
        
        for result in results:
            # Simple deduplication by exact match
            content_hash = hash(result.content[:100])  # Use first 100 chars
            
            if content_hash not in seen_contents:
                seen_contents.add(content_hash)
                unique_results.append(result)
        
        # Sort by score
        unique_results.sort(key=lambda x: x.score, reverse=True)
        
        return unique_results
    
    def format_context_for_llm(self, response: RAGResponse) -> str:
        """
        Format RAG response context for LLM prompt.
        
        Args:
            response: RAGResponse object
        
        Returns:
            Formatted context string
        """
        if not response.context_used:
            return ""
        
        context_parts = []
        context_parts.append("=== RETRIEVED KNOWLEDGE ===\n")
        
        for result in response.context_used:
            context_parts.append(
                f"[Source: {result.source} | Relevance: {result.score:.2f}]\n"
                f"{result.content}\n"
            )
        
        context_parts.append("\n=== END OF KNOWLEDGE ===\n")
        context_parts.append(f"Strategy: {response.strategy.value}")
        context_parts.append(f"Sources: {', '.join(response.sources)}")
        
        return "\n".join(context_parts)


class CriticAgent:
    """
    Self-Correction Agent for RAG validation.
    
    Checks for:
    1. Hallucination detection
    2. Context relevance
    3. Answer grounding in retrieved context
    """
    
    def __init__(self):
        logger.info("CriticAgent initialized")
    
    def validate_response(
        self,
        query: str,
        answer: str,
        context: List[RetrievalResult],
        threshold: float = 0.7
    ) -> Tuple[bool, float, str]:
        """
        Validate if answer is grounded in context.
        
        Args:
            query: Original query
            answer: Generated answer
            context: Retrieved context
            threshold: Validation threshold
        
        Returns:
            (is_valid, confidence_score, feedback)
        """
        if not context or not answer:
            return False, 0.0, "No context or answer provided"
        
        # Simple heuristic: Check if answer contains terms from context
        context_text = " ".join([r.content for r in context]).lower()
        answer_lower = answer.lower()
        
        # Extract key terms from answer
        answer_terms = set(answer_lower.split())
        context_terms = set(context_text.split())
        
        # Calculate overlap
        overlap = len(answer_terms & context_terms) / max(len(answer_terms), 1)
        
        is_valid = overlap >= threshold
        feedback = "Answer is grounded in context" if is_valid else "Answer may contain hallucinations"
        
        logger.info(f"[Critic] Validation: {is_valid} | Overlap: {overlap:.2f}")
        
        return is_valid, overlap, feedback


# Singleton instance
_omni_rag_instance = None

def get_omni_rag() -> OmniRAGOrchestrator:
    """Get singleton instance of OmniRAGOrchestrator."""
    global _omni_rag_instance
    if _omni_rag_instance is None:
        _omni_rag_instance = OmniRAGOrchestrator()
    return _omni_rag_instance
