"""Multi-Level Cache System for RAG Pipeline

This module implements a 4-tier cache architecture:
- L1: Hot Query Cache (exact matches, 100s TTL)
- L2: Semantic Cache (similarity-based, adaptive TTL)
- L3: Generation Cache (topic-clustered LLM outputs)
- L4: Chunk Cache (frequently accessed chunks)
"""

from .manager import MultiLevelCacheManager
from .adaptive_ttl import AdaptiveTTL

__all__ = ['MultiLevelCacheManager', 'AdaptiveTTL']
