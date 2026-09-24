"""Adaptive TTL Calculator for Multi-Level Cache System

Calculates time-to-live based on:
- Content type (algorithms: 7-30d, frameworks: 12h-3d)
- Access frequency (rare: 0.5x, popular: 2.0x)
- Query complexity (simple: 0.8x, complex: 1.8x)
- Time of day (off-peak: 0.7x, peak: 1.3x)
"""

from datetime import datetime
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)


class AdaptiveTTL:
    """Calculates adaptive TTL for cache entries"""
    
    # Base TTL in seconds for each content type
    CONTENT_TYPE_BASE_TTL = {
        'algorithm': 7 * 24 * 3600,        # 7 days - stable concepts
        'data_structure': 14 * 24 * 3600,  # 14 days - very stable
        'code_example': 3 * 24 * 3600,     # 3 days - version dependent
        'framework': 12 * 3600,             # 12 hours - frequently changing
        'personalized': 1 * 3600,           # 1 hour - session-specific
        'general': 2 * 24 * 3600,          # 2 days - default
    }
    
    # Min/Max TTL boundaries (seconds)
    TTL_BOUNDS = {
        'algorithm': (1 * 24 * 3600, 30 * 24 * 3600),       # 1d-30d
        'data_structure': (3 * 24 * 3600, 90 * 24 * 3600),  # 3d-90d
        'code_example': (12 * 3600, 14 * 24 * 3600),        # 12h-14d
        'framework': (2 * 3600, 3 * 24 * 3600),             # 2h-3d
        'personalized': (5 * 60, 6 * 3600),                 # 5min-6h
        'general': (6 * 3600, 7 * 24 * 3600),               # 6h-7d
    }
    
    @staticmethod
    def calculate(
        content_type: str = 'general',
        access_count: int = 0,
        query_complexity: str = 'medium',
        current_time: Optional[datetime] = None
    ) -> int:
        """
        Calculate adaptive TTL based on multiple factors
        
        Args:
            content_type: Type of content (algorithm, framework, etc.)
            access_count: Number of times this query was accessed
            query_complexity: Query complexity (simple, medium, high)
            current_time: Current datetime (defaults to now)
            
        Returns:
            TTL in seconds
        """
        # Get base TTL
        base_ttl = AdaptiveTTL.CONTENT_TYPE_BASE_TTL.get(
            content_type, 
            AdaptiveTTL.CONTENT_TYPE_BASE_TTL['general']
        )
        
        # Apply frequency multiplier
        freq_multiplier = AdaptiveTTL._get_frequency_multiplier(access_count)
        
        # Apply complexity multiplier
        complexity_multiplier = AdaptiveTTL._get_complexity_multiplier(query_complexity)
        
        # Apply time-of-day multiplier
        time_multiplier = AdaptiveTTL._get_time_multiplier(current_time or datetime.now())
        
        # Calculate final TTL
        calculated_ttl = base_ttl * freq_multiplier * complexity_multiplier * time_multiplier
        
        # Clamp to bounds
        min_ttl, max_ttl = AdaptiveTTL.TTL_BOUNDS.get(
            content_type,
            AdaptiveTTL.TTL_BOUNDS['general']
        )
        final_ttl = max(min_ttl, min(max_ttl, calculated_ttl))
        
        logger.debug(
            f"TTL calculation: type={content_type}, base={base_ttl}s, "
            f"freq={freq_multiplier:.2f}x, complexity={complexity_multiplier:.2f}x, "
            f"time={time_multiplier:.2f}x, final={final_ttl:.0f}s"
        )
        
        return int(final_ttl)
    
    @staticmethod
    def _get_frequency_multiplier(access_count: int) -> float:
        """Calculate multiplier based on access frequency"""
        if access_count >= 100:
            return 2.0  # Very popular
        elif access_count >= 50:
            return 1.5  # Popular
        elif access_count >= 10:
            return 1.0  # Moderate
        else:
            return 0.5  # Rare
    
    @staticmethod
    def _get_complexity_multiplier(complexity: str) -> float:
        """Calculate multiplier based on query complexity"""
        complexity_map = {
            'simple': 0.8,   # Lookup queries
            'medium': 1.2,   # Single-hop reasoning
            'high': 1.8,     # Multi-hop reasoning
        }
        return complexity_map.get(complexity, 1.0)
    
    @staticmethod
    def _get_time_multiplier(current_time: datetime) -> float:
        """Calculate multiplier based on time of day"""
        hour = current_time.hour
        
        # Peak hours: 9 AM - 10 PM (21:00)
        if 9 <= hour < 22:
            return 1.3
        # Off-peak: 10 PM - 9 AM
        else:
            return 0.7
    
    @staticmethod
    def get_content_type_from_query(query: str) -> str:
        """
        Infer content type from query text
        
        Args:
            query: User query text
            
        Returns:
            Content type string
        """
        query_lower = query.lower()
        
        # Algorithm detection
        algorithm_keywords = [
            'algorithm', 'sort', 'search', 'bfs', 'dfs', 'dijkstra',
            'dynamic programming', 'dp', 'greedy', 'backtrack'
        ]
        if any(kw in query_lower for kw in algorithm_keywords):
            return 'algorithm'
        
        # Data structure detection
        ds_keywords = [
            'tree', 'graph', 'heap', 'stack', 'queue', 'linked list',
            'hash', 'array', 'binary tree', 'avl', 'red-black'
        ]
        if any(kw in query_lower for kw in ds_keywords):
            return 'data_structure'
        
        # Code example detection
        code_keywords = ['example', 'code', 'implement', 'write', 'program']
        if any(kw in query_lower for kw in code_keywords):
            return 'code_example'
        
        # Framework detection
        framework_keywords = [
            'react', 'angular', 'vue', 'django', 'flask', 'spring',
            'express', 'fastapi', 'next.js'
        ]
        if any(kw in query_lower for kw in framework_keywords):
            return 'framework'
        
        # Personalized detection
        personal_keywords = ['my', 'i am', 'help me', 'can you', 'explain to me']
        if any(kw in query_lower for kw in personal_keywords):
            return 'personalized'
        
        return 'general'
    
    @staticmethod
    def get_query_complexity(query: str) -> str:
        """
        Estimate query complexity from text
        
        Args:
            query: User query text
            
        Returns:
            Complexity level: 'simple', 'medium', or 'high'
        """
        query_lower = query.lower()
        
        # High complexity indicators
        high_indicators = [
            'how', 'why', 'explain', 'compare', 'difference between',
            'relationship', 'analyze', 'multiple'
        ]
        if any(ind in query_lower for ind in high_indicators):
            # Multiple indicators = very complex
            if sum(ind in query_lower for ind in high_indicators) >= 2:
                return 'high'
        
        # Simple complexity indicators
        simple_indicators = ['what is', 'define', 'meaning of']
        if any(ind in query_lower for ind in simple_indicators):
            return 'simple'
        
        # Word count heuristic
        word_count = len(query.split())
        if word_count <= 5:
            return 'simple'
        elif word_count >= 15:
            return 'high'
        
        return 'medium'
