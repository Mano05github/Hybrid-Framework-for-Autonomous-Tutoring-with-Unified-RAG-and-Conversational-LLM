"""L4 Chunk Cache - In-memory LRU cache for frequently accessed chunks

Reduces database calls for popular chunks.
Fast in-memory access with 1-hour TTL.
"""

import logging
import time
from typing import Optional, Dict, Any, List
from collections import OrderedDict

logger = logging.getLogger(__name__)


class ChunkCache:
    """L4 Cache: Chunk Cache (In-memory LRU)"""
    
    def __init__(self, max_entries: int = 10000, ttl: int = 3600):
        """
        Initialize Chunk Cache
        
        Args:
            max_entries: Maximum number of chunks to cache
            ttl: Time-to-live in seconds (default: 1 hour)
        """
        self.cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self.max_entries = max_entries
        self.ttl = ttl
        
        # Statistics
        self.hits = 0
        self.misses = 0
        
        logger.info(f"ChunkCache initialized (max_entries={max_entries}, TTL={ttl}s)")
    
    def get(self, chunk_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve chunk by ID
        
        Args:
            chunk_id: Unique chunk identifier
            
        Returns:
            Chunk data or None if not cached/expired
        """
        if chunk_id not in self.cache:
            self.misses += 1
            logger.debug(f"L4 MISS: chunk_id={chunk_id}")
            return None
        
        # Check expiration
        entry = self.cache[chunk_id]
        if time.time() > entry['expires_at']:
            # Expired - remove
            del self.cache[chunk_id]
            self.misses += 1
            logger.debug(f"L4 EXPIRED: chunk_id={chunk_id}")
            return None
        
        # Move to end (most recently used)
        self.cache.move_to_end(chunk_id)
        self.hits += 1
        
        logger.debug(f"L4 HIT: chunk_id={chunk_id}")
        return entry['data']
    
    def get_batch(self, chunk_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve multiple chunks
        
        Args:
            chunk_ids: List of chunk IDs
            
        Returns:
            Dict mapping chunk_id to chunk data (only cached items)
        """
        result = {}
        for chunk_id in chunk_ids:
            chunk_data = self.get(chunk_id)
            if chunk_data is not None:
                result[chunk_id] = chunk_data
        
        logger.debug(f"L4 BATCH: requested={len(chunk_ids)}, cached={len(result)}")
        return result
    
    def set(self, chunk_id: str, chunk_data: Dict[str, Any]) -> bool:
        """
        Store chunk in cache
        
        Args:
            chunk_id: Unique chunk identifier
            chunk_data: Chunk data to cache
            
        Returns:
            True if successfully cached
        """
        try:
            # Check if cache is full
            if len(self.cache) >= self.max_entries and chunk_id not in self.cache:
                # Remove least recently used item
                lru_key = next(iter(self.cache))
                del self.cache[lru_key]
                logger.debug(f"L4 EVICT: {lru_key}")
            
            # Store with expiration
            self.cache[chunk_id] = {
                'data': chunk_data,
                'expires_at': time.time() + self.ttl,
                'cached_at': time.time()
            }
            
            # Move to end (most recently used)
            self.cache.move_to_end(chunk_id)
            
            logger.debug(f"L4 SET: chunk_id={chunk_id}")
            return True
            
        except Exception as e:
            logger.error(f"L4 cache set error: {e}")
            return False
    
    def set_batch(self, chunks: Dict[str, Dict[str, Any]]) -> int:
        """
        Store multiple chunks
        
        Args:
            chunks: Dict mapping chunk_id to chunk_data
            
        Returns:
            Number of chunks successfully cached
        """
        count = 0
        for chunk_id, chunk_data in chunks.items():
            if self.set(chunk_id, chunk_data):
                count += 1
        
        logger.debug(f"L4 BATCH SET: {count}/{len(chunks)} cached")
        return count
    
    def invalidate(self, chunk_id: str) -> bool:
        """
        Invalidate specific chunk
        
        Args:
            chunk_id: Chunk ID to invalidate
            
        Returns:
            True if chunk was cached and removed
        """
        if chunk_id in self.cache:
            del self.cache[chunk_id]
            logger.debug(f"L4 INVALIDATE: {chunk_id}")
            return True
        return False
    
    def clear(self) -> int:
        """
        Clear entire cache
        
        Returns:
            Number of entries cleared
        """
        count = len(self.cache)
        self.cache.clear()
        self.hits = 0
        self.misses = 0
        logger.info(f"L4 cache cleared ({count} entries)")
        return count
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries
        
        Returns:
            Number of entries removed
        """
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time > entry['expires_at']
        ]
        
        for key in expired_keys:
            del self.cache[key]
        
        if expired_keys:
            logger.info(f"L4 CLEANUP: removed {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hits + self.misses
        hit_rate = (self.hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'level': 'L4',
            'name': 'Chunk Cache (In-Memory)',
            'size': len(self.cache),
            'max_entries': self.max_entries,
            'ttl': self.ttl,
            'hits': self.hits,
            'misses': self.misses,
            'hit_rate': f"{hit_rate:.1f}%",
            'total_requests': total_requests
        }
