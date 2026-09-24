"""L3 Generation Cache - Topic-clustered LLM output cache

Caches complete LLM responses organized by topic clusters.
Long TTL (7-30 days) for stable content.
"""

import redis
import json
import hashlib
import logging
from typing import Optional, Dict, Any
from datetime import datetime

from .adaptive_ttl import AdaptiveTTL

logger = logging.getLogger(__name__)


class GenerationCache:
    """L3 Cache: Generation Cache (LLM outputs by topic)"""
    
    def __init__(self, redis_client: redis.Redis = None, db: int = 2):
        """
        Initialize Generation Cache
        
        Args:
            redis_client: Redis connection
            db: Redis database number (default: 2 for L3)
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
        
        self.prefix = "l3:gen:"
        self.max_entries = 50000
        
        logger.info(f"GenerationCache initialized (db={db})")
    
    def _get_key(self, query: str, context_hash: Optional[str] = None) -> str:
        """
        Generate cache key from query and context
        
        Args:
            query: User query text
            context_hash: Hash of retrieval context (optional)
            
        Returns:
            Cache key
        """
        # Combine query and context for key
        if context_hash:
            combined = f"{query}:{context_hash}"
        else:
            combined = query
        
        query_hash = hashlib.sha256(combined.encode()).hexdigest()
        return f"{self.prefix}{query_hash}"
    
    def get(self, query: str, context_hash: Optional[str] = None) -> Optional[str]:
        """
        Retrieve cached LLM generation
        
        Args:
            query: User query text
            context_hash: Hash of retrieval context
            
        Returns:
            Cached LLM response text or None
        """
        key = self._get_key(query, context_hash)
        
        try:
            cached = self.redis.get(key)
            if cached:
                data = json.loads(cached)
                logger.info(f"L3 HIT: {query[:50]}...")
                
                # Increment hit count
                self.redis.hincrby(f"{key}:meta", "hits", 1)
                
                return data.get('response')
            
            logger.debug(f"L3 MISS: {query[:50]}...")
            return None
            
        except Exception as e:
            logger.error(f"L3 cache get error: {e}")
            return None
    
    def set(
        self,
        query: str,
        response: str,
        context_hash: Optional[str] = None,
        topic: Optional[str] = None,
        content_type: Optional[str] = None
    ) -> bool:
        """
        Store LLM generation in cache
        
        Args:
            query: User query text
            response: LLM response text
            context_hash: Hash of retrieval context
            topic: Topic classification (e.g., 'algorithms', 'data_structures')
            content_type: Content type for TTL calculation
            
        Returns:
            True if successfully cached
        """
        # Infer content type if not provided
        if content_type is None:
            content_type = AdaptiveTTL.get_content_type_from_query(query)
        
        # Calculate TTL (generations use longer TTL)
        complexity = AdaptiveTTL.get_query_complexity(query)
        ttl = AdaptiveTTL.calculate(
            content_type=content_type,
            access_count=0,  # New entry
            query_complexity=complexity,
            current_time=datetime.now()
        )
        
        # Apply generation-specific multiplier (longer TTL)
        ttl = int(ttl * 1.5)  # 1.5x for LLM outputs
        
        key = self._get_key(query, context_hash)
        
        try:
            # Check current size
            current_size = self.redis.dbsize()
            if current_size >= self.max_entries:
                logger.warning(f"L3 cache full ({current_size} entries)")
            
            # Store response
            cache_data = {
                'query': query,
                'response': response,
                'context_hash': context_hash,
                'topic': topic or 'general',
                'content_type': content_type,
                'created': datetime.now().isoformat()
            }
            
            self.redis.setex(
                key,
                ttl,
                json.dumps(cache_data)
            )
            
            # Store metadata
            self.redis.hset(f"{key}:meta", mapping={
                "query": query[:100],
                "topic": topic or 'general',
                "content_type": content_type,
                "ttl": ttl,
                "hits": 0,
                "created": str(self.redis.time()[0])
            })
            self.redis.expire(f"{key}:meta", ttl)
            
            # Add to topic index
            if topic:
                self.redis.sadd(f"{self.prefix}topic:{topic}", key)
                self.redis.expire(f"{self.prefix}topic:{topic}", ttl)
            
            logger.debug(
                f"L3 SET: query='{query[:50]}...', "
                f"topic={topic}, type={content_type}, TTL={ttl}s"
            )
            return True
            
        except Exception as e:
            logger.error(f"L3 cache set error: {e}")
            return False
    
    def invalidate_topic(self, topic: str) -> int:
        """
        Invalidate all cached generations for a topic
        
        Args:
            topic: Topic name
            
        Returns:
            Number of keys invalidated
        """
        try:
            topic_key = f"{self.prefix}topic:{topic}"
            keys = self.redis.smembers(topic_key)
            
            if not keys:
                return 0
            
            # Delete all keys and their metadata
            all_keys = []
            for key in keys:
                all_keys.append(key)
                all_keys.append(f"{key}:meta")
            
            deleted = self.redis.delete(*all_keys, topic_key)
            logger.info(f"L3 INVALIDATE TOPIC: {topic} ({deleted} keys)")
            return deleted
            
        except Exception as e:
            logger.error(f"L3 invalidate topic error: {e}")
            return 0
    
    def invalidate(self, query: str, context_hash: Optional[str] = None) -> bool:
        """Invalidate specific generation"""
        key = self._get_key(query, context_hash)
        
        try:
            deleted = self.redis.delete(key, f"{key}:meta")
            if deleted:
                logger.info(f"L3 INVALIDATE: {query[:50]}...")
            return deleted > 0
        except Exception as e:
            logger.error(f"L3 invalidate error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear entire L3 cache"""
        try:
            self.redis.flushdb()
            logger.info("L3 cache cleared")
            return True
        except Exception as e:
            logger.error(f"L3 clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.redis.info('stats')
            
            # Get topic distribution
            topic_keys = self.redis.keys(f"{self.prefix}topic:*")
            topics = {}
            for tk in topic_keys:
                topic = tk.split(':')[-1]
                count = self.redis.scard(tk)
                topics[topic] = count
            
            return {
                'level': 'L3',
                'name': 'Generation Cache',
                'size': self.redis.dbsize(),
                'max_entries': self.max_entries,
                'topics': topics,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
        except Exception as e:
            logger.error(f"L3 stats error: {e}")
            return {}
