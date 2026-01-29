"""
Query Complexity Analyzer - Detect complex queries requiring decomposition
Target: Score 0-100, identify multi-intent queries
"""
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass

import spacy


@dataclass
class ComplexityMetrics:
    """Comprehensive complexity analysis result."""
    score: int  # 0-100 (0=simple, 100=highly complex)
    word_count: int
    clause_count: int
    question_count: int
    technical_terms: int
    is_multi_intent: bool
    sub_queries: List[str]
    reasoning: str


class ComplexityAnalyzer:
    """
    Analyzes query complexity to determine routing strategy.
    
    Complexity Factors:
    1. Length: More words = more complex
    2. Clauses: Multiple clauses = multi-part question
    3. Questions: Multiple questions = decomposition needed
    4. Technical density: More CS terms = higher expertise
    5. Multi-intent: Different intent verbs = parallel routing
    
    Scoring:
    - 0-30: Simple (single agent, direct response)
    - 31-60: Moderate (may need context retrieval)
    - 61-100: Complex (decompose into sub-queries)
    """
    
    # Technical CS terms (for domain complexity)
    TECHNICAL_TERMS = {
        # Data structures
        'array', 'linked list', 'stack', 'queue', 'tree', 'graph', 'hash table',
        'heap', 'trie', 'binary tree', 'bst', 'avl', 'red-black', 'b-tree',
        # Algorithms
        'sorting', 'searching', 'traversal', 'recursion', 'iteration',
        'dynamic programming', 'greedy', 'backtracking', 'divide and conquer',
        'dfs', 'bfs', 'dijkstra', 'bellman-ford', 'floyd-warshall',
        'quicksort', 'mergesort', 'heapsort', 'binary search',
        # Complexity
        'time complexity', 'space complexity', 'big o', 'omega', 'theta',
        'logarithmic', 'linear', 'quadratic', 'exponential', 'polynomial',
        # Concepts
        'pointer', 'reference', 'memory', 'cache', 'optimization',
        'memoization', 'amortized', 'worst case', 'average case', 'best case'
    }
    
    # Intent indicator verbs (for multi-intent detection)
    INTENT_VERBS = {
        'teacher': ['explain', 'teach', 'describe', 'what', 'how', 'why', 'define'],
        'coder': ['debug', 'fix', 'implement', 'code', 'write', 'create', 'build'],
        'examiner': ['test', 'quiz', 'question', 'assess', 'evaluate', 'check knowledge'],
        'visionary': ['analyze', 'verify', 'validate', 'check diagram', 'visualize'],
        'empath': ['stuck', 'frustrated', 'confused', 'help', 'difficult', 'hard']
    }
    
    def __init__(self):
        """Initialize analyzer with spaCy NLP pipeline."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy model (one-time setup)...")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"])
            self.nlp = spacy.load("en_core_web_sm")
    
    def analyze(self, query: str) -> ComplexityMetrics:
        """
        Analyze query complexity with detailed breakdown.
        
        Args:
            query: User query string
        
        Returns:
            ComplexityMetrics with score and decomposition
        """
        # Tokenize with spaCy
        doc = self.nlp(query.lower())
        
        # 1. Word count (weighted 20%)
        word_count = len([token for token in doc if not token.is_punct])
        word_score = min(word_count * 2, 20)  # Cap at 20 points
        
        # 2. Clause count (weighted 25%)
        clause_count = self._count_clauses(query)
        clause_score = min(clause_count * 8, 25)
        
        # 3. Question count (weighted 20%)
        question_count = query.count('?')
        question_score = min(question_count * 10, 20)
        
        # 4. Technical density (weighted 20%)
        technical_count = self._count_technical_terms(doc)
        technical_score = min(technical_count * 4, 20)
        
        # 5. Multi-intent detection (weighted 15%)
        intent_indicators = self._detect_intents(doc)
        is_multi_intent = len(intent_indicators) > 1
        multi_intent_score = 15 if is_multi_intent else 0
        
        # Calculate total score
        total_score = int(
            word_score + clause_score + question_score + 
            technical_score + multi_intent_score
        )
        
        # Decompose if complex
        sub_queries = []
        if total_score > 60 or question_count > 1 or is_multi_intent:
            sub_queries = self._decompose_query(query, doc)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            total_score, word_count, clause_count, 
            question_count, technical_count, is_multi_intent
        )
        
        return ComplexityMetrics(
            score=total_score,
            word_count=word_count,
            clause_count=clause_count,
            question_count=question_count,
            technical_terms=technical_count,
            is_multi_intent=is_multi_intent,
            sub_queries=sub_queries,
            reasoning=reasoning
        )
    
    def _count_clauses(self, query: str) -> int:
        """
        Count grammatical clauses in query.
        
        Indicators: conjunctions (and, but, or), semicolons, relative pronouns
        """
        clause_indicators = [' and ', ' but ', ' or ', ';', ' which ', ' that ', ' where ']
        count = 1  # Start with 1 (main clause)
        
        for indicator in clause_indicators:
            count += query.lower().count(indicator)
        
        return count
    
    def _count_technical_terms(self, doc: spacy.tokens.Doc) -> int:
        """Count technical CS terms in query."""
        count = 0
        query_text = doc.text
        
        for term in self.TECHNICAL_TERMS:
            if term in query_text:
                count += 1
        
        return count
    
    def _detect_intents(self, doc: spacy.tokens.Doc) -> List[str]:
        """
        Detect multiple intents in query based on verb indicators.
        
        Returns:
            List of detected intents
        """
        detected = set()
        query_text = doc.text
        
        for intent, verbs in self.INTENT_VERBS.items():
            for verb in verbs:
                if verb in query_text:
                    detected.add(intent)
                    break
        
        return list(detected)
    
    def _decompose_query(self, query: str, doc: spacy.tokens.Doc) -> List[str]:
        """
        Decompose complex query into atomic sub-queries.
        
        Strategy:
        1. Split on sentence boundaries
        2. Split on conjunctions ('and', 'but')
        3. Split on multiple question marks
        """
        sub_queries = []
        
        # Strategy 1: Split by sentences
        sentences = [sent.text.strip() for sent in doc.sents]
        
        if len(sentences) > 1:
            return sentences
        
        # Strategy 2: Split by coordinating conjunctions
        main_text = query
        
        # Split on "and" between questions
        if ' and ' in main_text and '?' in main_text:
            parts = re.split(r'\s+and\s+', main_text)
            if len(parts) > 1:
                # Ensure each part is a complete question
                for i, part in enumerate(parts):
                    if not part.strip().endswith('?'):
                        part += '?'
                    sub_queries.append(part.strip())
                return sub_queries
        
        # Strategy 3: Split multiple questions
        questions = re.findall(r'[^.!?]+\?', main_text)
        if len(questions) > 1:
            return [q.strip() + '?' for q in questions]
        
        # If no decomposition possible, return original
        return [query]
    
    def _generate_reasoning(
        self, score: int, words: int, clauses: int,
        questions: int, technical: int, multi_intent: bool
    ) -> str:
        """Generate human-readable complexity reasoning."""
        complexity_level = "simple" if score < 31 else "moderate" if score < 61 else "complex"
        
        factors = []
        if words > 15:
            factors.append(f"{words} words")
        if clauses > 1:
            factors.append(f"{clauses} clauses")
        if questions > 1:
            factors.append(f"{questions} questions")
        if technical > 2:
            factors.append(f"{technical} technical terms")
        if multi_intent:
            factors.append("multiple intents")
        
        if not factors:
            return f"Simple query (score: {score})"
        
        factors_str = ", ".join(factors)
        return f"{complexity_level.capitalize()} query with {factors_str} (score: {score})"


def test_complexity_analyzer():
    """Test analyzer with diverse queries."""
    analyzer = ComplexityAnalyzer()
    
    test_cases = [
        "What is binary search?",
        "Explain how merge sort works and what is its time complexity?",
        "Debug my code and also explain why quicksort is O(n log n) on average",
        "I'm stuck on this problem. Can you explain recursion and help me implement a factorial function?",
        "Explain dynamic programming, give me practice problems, and check if my diagram is correct",
    ]
    
    print("=" * 80)
    print("Query Complexity Analyzer - Test Results")
    print("=" * 80)
    
    for query in test_cases:
        print(f"\nQuery: \"{query}\"")
        print("-" * 80)
        
        metrics = analyzer.analyze(query)
        
        print(f"Score:          {metrics.score}/100")
        print(f"Classification: ", end="")
        if metrics.score < 31:
            print("SIMPLE (direct response)")
        elif metrics.score < 61:
            print("MODERATE (may need context)")
        else:
            print("COMPLEX (decomposition needed)")
        
        print(f"Words:          {metrics.word_count}")
        print(f"Clauses:        {metrics.clause_count}")
        print(f"Questions:      {metrics.question_count}")
        print(f"Technical:      {metrics.technical_terms}")
        print(f"Multi-intent:   {metrics.is_multi_intent}")
        print(f"Reasoning:      {metrics.reasoning}")
        
        if metrics.sub_queries and len(metrics.sub_queries) > 1:
            print("\nDecomposed Sub-queries:")
            for i, sub in enumerate(metrics.sub_queries, 1):
                print(f"  {i}. {sub}")


if __name__ == "__main__":
    test_complexity_analyzer()
