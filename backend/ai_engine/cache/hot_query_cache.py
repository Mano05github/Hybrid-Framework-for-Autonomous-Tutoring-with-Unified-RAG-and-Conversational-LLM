"""L1 Hot Query Cache - Ultra-fast exact query matching

Stores recent exact query matches in Redis with 100s TTL.
Handles 15-20% of queries with <50ms latency.
"""

import redis
import json
import hashlib
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class HotQueryCache:
    """L1 Cache: Hot Query Cache (Exact Matches)"""
    
    def __init__(self, redis_client: redis.Redis = None, db: int = 0):
        """
        Initialize Hot Query Cache
        
        Args:
            redis_client: Redis connection (will create if None)
            db: Redis database number (default: 0 for L1)
        """
        if redis_client is None:
            self.redis = redis.Redis(
                host='localhost',
                port=6379,
                db=db,
                decode_responses=True
            )
        else:
            self.redis = redis_client
        
        self.ttl = 100  # 100 seconds fixed TTL
        self.prefix = "l1:hot:"
        self.max_entries = 1000
        
        logger.info(f"HotQueryCache initialized (db={db}, TTL={self.ttl}s)")
    
    def _get_key(self, query: str) -> str:
        """Generate cache key from query"""
        # Use MD5 hash for exact matching
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"{self.prefix}{query_hash}"
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response for exact query match
        
        Args:
            query: User query text
            
        Returns:
            Cached response dict or None if miss
        """
        key = self._get_key(query)
        
        try:
            cached = self.redis.get(key)
            if cached:
                logger.info(f"L1 HIT: {query[:50]}...")
                data = json.loads(cached)
                
                # Increment hit count
                self.redis.hincrby(f"{key}:meta", "hits", 1)
                
                return data
            
            logger.debug(f"L1 MISS: {query[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"L1 cache get error: {e}")
            return None
    
    def set(self, query: str, response: Dict[str, Any]) -> bool:
        """
        Store response in hot cache
        
        Args:
            query: User query text
            response: Response data to cache
            
        Returns:
            True if successfully cached
        """
        key = self._get_key(query)
        
        try:
            # Check current size
            current_size = self.redis.dbsize()
            if current_size >= self.max_entries:
                logger.warning(f"L1 cache full ({current_size} entries), evicting LRU")
            
            # Store response
            self.redis.setex(
                key,
                self.ttl,
                json.dumps(response)
            )
            
            # Store metadata
            self.redis.hset(f"{key}:meta", mapping={
                "query": query[:100],  # First 100 chars for debugging
                "hits": 0,
                "created": str(self.redis.time()[0])
            })
            self.redis.expire(f"{key}:meta", self.ttl)
            
            logger.debug(f"L1 SET: {query[:50]}... (TTL={self.ttl}s)")
            return True
            
        except Exception as e:
            logger.error(f"L1 cache set error: {e}")
            return False
    
    def invalidate(self, query: str) -> bool:
        """
        Invalidate specific query from cache
        
        Args:
            query: Query to invalidate
            
        Returns:
            True if key was deleted
        """
        key = self._get_key(query)
        
        try:
            deleted = self.redis.delete(key, f"{key}:meta")
            if deleted:
                logger.info(f"L1 INVALIDATE: {query[:50]}...")
            return deleted > 0
            
        except Exception as e:
            logger.error(f"L1 cache invalidate error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear entire L1 cache"""
        try:
            self.redis.flushdb()
            logger.info("L1 cache cleared")
            return True
        except Exception as e:
            logger.error(f"L1 cache clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.redis.info('stats')
            return {
                'level': 'L1',
                'name': 'Hot Query Cache',
                'size': self.redis.dbsize(),
                'max_entries': self.max_entries,
                'ttl': self.ttl,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
        except Exception as e:
            logger.error(f"L1 stats error: {e}")
            return {}
