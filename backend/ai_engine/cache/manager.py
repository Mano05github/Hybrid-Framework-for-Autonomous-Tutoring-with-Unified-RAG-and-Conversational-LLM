"""Multi-Level Cache Manager

Coordinates all 4 cache levels:
- L1: Hot Query Cache (exact matches, 100s)
- L2: Semantic Cache (similarity, adaptive TTL)
- L3: Generation Cache (LLM outputs, 7-30d)
- L4: Chunk Cache (in-memory, 1h)

Cache flow: L1 → L2 → L3 → L4 → Database/RAG
"""

import logging
import os
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

import redis
import numpy as np

from .hot_query_cache import HotQueryCache
from .semantic_cache import SemanticCache
from .generation_cache import GenerationCache
from .chunk_cache import ChunkCache

logger = logging.getLogger(__name__)


def _redis_available(host: str, port: int) -> bool:
    try:
        client = redis.Redis(host=host, port=port, db=0)
        client.ping()
        return True
    except Exception:
        return False


@dataclass
class _InMemoryEntry:
    value: Any
    expires_at: float


class _InMemoryHotCache:
    def __init__(self, ttl_seconds: int = 100):
        self.ttl_seconds = ttl_seconds
        self.store: Dict[str, _InMemoryEntry] = {}

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        entry = self.store.get(query)
        if not entry:
            return None
        if time.time() > entry.expires_at:
            self.store.pop(query, None)
            return None
        return entry.value

    def set(self, query: str, response: Dict[str, Any]) -> bool:
        self.store[query] = _InMemoryEntry(
            value=response,
            expires_at=time.time() + self.ttl_seconds
        )
        return True


class _InMemoryGenerationCache:
    def __init__(self, ttl_days: int = 7):
        self.ttl_seconds = ttl_days * 24 * 60 * 60
        self.store: Dict[str, _InMemoryEntry] = {}

    def _key(self, query: str, context_hash: Optional[str]) -> str:
        return f"{query}:{context_hash}" if context_hash else query

    def get(self, query: str, context_hash: Optional[str] = None) -> Optional[str]:
        key = self._key(query, context_hash)
        entry = self.store.get(key)
        if not entry:
            return None
        if time.time() > entry.expires_at:
            self.store.pop(key, None)
            return None
        return entry.value

    def set(self, query: str, response: str, context_hash: Optional[str] = None, **_kwargs) -> bool:
        key = self._key(query, context_hash)
        self.store[key] = _InMemoryEntry(
            value=response,
            expires_at=time.time() + self.ttl_seconds
        )
        return True


class _InMemorySemanticCache:
    def __init__(self, similarity_threshold: float = 0.92, ttl_hours: int = 24):
        self.similarity_threshold = similarity_threshold
        self.ttl = timedelta(hours=ttl_hours)
        self.entries: List[Dict[str, Any]] = []

    def _encode_query(self, query: str) -> Optional[np.ndarray]:
        # Embedding model removed (RAG rebuild pending). Semantic cache disabled.
        return None

    def get(self, query: str) -> Optional[Dict[str, Any]]:
        query_embedding = self._encode_query(query)
        if query_embedding is None or not self.entries:
            return None

        best_entry = None
        best_similarity = 0.0
        now = datetime.now()

        for entry in list(self.entries):
            if now - entry["timestamp"] > self.ttl:
                self.entries.remove(entry)
                continue

            similarity = self._cosine_similarity(query_embedding, entry["embedding"])
            if similarity > best_similarity:
                best_similarity = similarity
                best_entry = entry

        if best_entry and best_similarity >= self.similarity_threshold:
            return best_entry["response"]

        return None

    def set(self, query: str, response: Dict[str, Any], **_kwargs) -> bool:
        embedding = self._encode_query(query)
        if embedding is None:
            return False

        self.entries.append({
            "query": query,
            "response": response,
            "embedding": embedding,
            "timestamp": datetime.now(),
        })
        return True

    @staticmethod
    def _cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)


class MultiLevelCacheManager:
    """Coordinates multi-level cache system"""
    
    def __init__(self, redis_host: str = 'localhost', redis_port: int = 6379):
        """
        Initialize multi-level cache manager
        
        Args:
            redis_host: Redis server host
            redis_port: Redis server port
        """
        cache_mode = os.getenv("CACHE_MODE", "auto").lower()
        redis_ready = _redis_available(redis_host, redis_port)
        use_redis = cache_mode == "redis" or (cache_mode == "auto" and redis_ready)

        if cache_mode == "disabled":
            self.l1 = None
            self.l2 = None
            self.l3 = None
            self.l4 = ChunkCache(max_entries=10000, ttl=3600)
            logger.info("Cache manager disabled (CACHE_MODE=disabled)")
            return

        if use_redis:
            try:
                self.l1 = HotQueryCache(
                    redis_client=redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        db=0,
                        decode_responses=True
                    ),
                    db=0
                )
                self.l2 = SemanticCache(
                    redis_client=redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        db=1,
                        decode_responses=True
                    ),
                    db=1
                )
                self.l3 = GenerationCache(
                    redis_client=redis.Redis(
                        host=redis_host,
                        port=redis_port,
                        db=2,
                        decode_responses=True
                    ),
                    db=2
                )
                self.l4 = ChunkCache(max_entries=10000, ttl=3600)

                logger.info("MultiLevelCacheManager initialized with Redis")
                return
            except Exception as e:
                logger.error(f"Failed to initialize Redis cache manager: {e}")

        # Fallback: in-memory caches
        self.l1 = _InMemoryHotCache()
        self.l2 = _InMemorySemanticCache()
        self.l3 = _InMemoryGenerationCache()
        self.l4 = ChunkCache(max_entries=10000, ttl=3600)
        logger.info("MultiLevelCacheManager initialized with in-memory caches")
    
    def get_response(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Get cached response, checking all levels in order
        
        Args:
            query: User query text
            
        Returns:
            Cached response or None if not found
        """
        # L1: Hot Query Cache (exact match)
        response = self.l1.get(query) if self.l1 else None
        if response:
            logger.info("Cache hit: L1 (Hot Query)")
            return response
        
        # L2: Semantic Cache (similarity match)
        response = self.l2.get(query) if self.l2 else None
        if response:
            logger.info("Cache hit: L2 (Semantic)")
            # Promote to L1 for faster future access
            if self.l1:
                self.l1.set(query, response)
            return response
        
        # L3: Generation Cache (LLM output)
        # Note: L3 requires context hash, checked separately in generation step
        
        logger.debug(f"Cache miss: All levels for query '{query[:50]}...'")
        return None
    
    def get_generation(
        self,
        query: str,
        context_hash: Optional[str] = None
    ) -> Optional[str]:
        """
        Get cached LLM generation (L3)
        
        Args:
            query: User query text
            context_hash: Hash of retrieval context
            
        Returns:
            Cached LLM response text or None
        """
        response = self.l3.get(query, context_hash) if self.l3 else None
        if response:
            logger.info("Cache hit: L3 (Generation)")
        return response
    
    def get_chunks(self, chunk_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Get cached chunks (L4)
        
        Args:
            chunk_ids: List of chunk IDs
            
        Returns:
            Dict mapping chunk_id to chunk data
        """
        cached_chunks = self.l4.get_batch(chunk_ids)
        
        if cached_chunks:
            logger.info(f"Cache hit: L4 (Chunks) - {len(cached_chunks)}/{len(chunk_ids)}")
        
        return cached_chunks
    
    def set_response(
        self,
        query: str,
        response: Dict[str, Any],
        content_type: Optional[str] = None
    ) -> bool:
        """
        Store response in L1 and L2
        
        Args:
            query: User query text
            response: Response data
            content_type: Content type for adaptive TTL
            
        Returns:
            True if cached successfully
        """
        # Store in both L1 and L2
        l1_success = self.l1.set(query, response) if self.l1 else False
        l2_success = self.l2.set(query, response, content_type=content_type) if self.l2 else False
        
        return l1_success or l2_success
    
    def set_generation(
        self,
        query: str,
        response: str,
        context_hash: Optional[str] = None,
        topic: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Store LLM generation in L3
        
        Args:
            query: User query text
            response: LLM response text
            context_hash: Hash of retrieval context
            topic: Topic classification
            content_type: Content type for TTL
            
        Returns:
            True if cached successfully
        """
        if not self.l3:
            return False
        return self.l3.set(
            query=query,
            response=response,
            context_hash=context_hash,
            topic=topic,
            content_type=content_type
        )
    
    def set_chunks(self, chunks: Dict[str, Dict[str, Any]]) -> int:
        """
        Store chunks in L4
        
        Args:
            chunks: Dict mapping chunk_id to chunk_data
            
        Returns:
            Number of chunks cached
        """
        return self.l4.set_batch(chunks)
    
    def invalidate_query(self, query: str) -> bool:
        """
        Invalidate query from all relevant levels
        
        Args:
            query: Query to invalidate
            
        Returns:
            True if any level invalidated
        """
        l1_invalidated = self.l1.invalidate(query)
        l2_invalidated = self.l2.invalidate(query)
        l3_invalidated = self.l3.invalidate(query)
        
        return l1_invalidated or l2_invalidated or l3_invalidated
    
    def invalidate_topic(self, topic: str) -> int:
        """
        Invalidate all cached generations for a topic
        
        Args:
            topic: Topic name
            
        Returns:
            Number of entries invalidated
        """
        return self.l3.invalidate_topic(topic)
    
    def clear_all(self) -> Dict[str, bool]:
        """
        Clear all cache levels
        
        Returns:
            Dict with clear status for each level
        """
        return {
            'L1': self.l1.clear(),
            'L2': self.l2.clear(),
            'L3': self.l3.clear(),
            'L4': self.l4.clear() > 0
        }
    
    def get_all_stats(self) -> Dict[str, Any]:
        """
        Get statistics from all cache levels
        
        Returns:
            Combined stats dict
        """
        stats = {
            'levels': [
                self.l1.get_stats(),
                self.l2.get_stats(),
                self.l3.get_stats(),
                self.l4.get_stats()
            ]
        }
        
        # Calculate combined metrics
        total_size = sum(level.get('size', 0) for level in stats['levels'])
        stats['total_entries'] = total_size
        
        # Calculate combined hit rate (from L2, L4 which track hits/misses)
        total_hits = 0
        total_misses = 0
        
        for level in stats['levels']:
            if 'keyspace_hits' in level:
                total_hits += level['keyspace_hits']
                total_misses += level['keyspace_misses']
            elif 'hits' in level:
                total_hits += level['hits']
                total_misses += level['misses']
        
        total_requests = total_hits + total_misses
        if total_requests > 0:
            stats['combined_hit_rate'] = f"{(total_hits / total_requests * 100):.1f}%"
        else:
            stats['combined_hit_rate'] = "N/A"
        
        return stats
    
    def cleanup(self):
        """Cleanup expired entries from in-memory cache"""
        removed = self.l4.cleanup_expired()
        if removed > 0:
            logger.info(f"Cleanup: removed {removed} expired L4 entries")
