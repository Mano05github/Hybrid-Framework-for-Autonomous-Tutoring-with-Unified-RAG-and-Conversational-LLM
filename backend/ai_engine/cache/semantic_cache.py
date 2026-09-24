"""L2 Semantic Cache - Similarity-based query matching

Uses cosine similarity on query embeddings to find similar cached queries.
Adaptive TTL based on content type, frequency, and complexity.
"""

import redis
import json
import hashlib
import numpy as np
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from .adaptive_ttl import AdaptiveTTL

logger = logging.getLogger(__name__)


class SemanticCache:
    """L2 Cache: Semantic Cache (Similarity-based)"""
    
    def __init__(self, redis_client: redis.Redis = None, db: int = 1):
        """
        Initialize Semantic Cache
        
        Args:
            redis_client: Redis connection
            db: Redis database number (default: 1 for L2)
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
        
        self.prefix = "l2:semantic:"
        self.similarity_threshold = 0.92
        self.max_entries = 10000
        self.embedding_model = None  # Will be set by manager
        
        logger.info(f"SemanticCache initialized (db={db}, threshold={self.similarity_threshold})")
    
    def set_embedding_model(self, model):
        """Set embedding model for query encoding"""
        self.embedding_model = model
    
    def _get_key(self, query: str) -> str:
        """Generate cache key from query"""
        query_hash = hashlib.sha256(query.encode()).hexdigest()
        return f"{self.prefix}{query_hash}"
    
    def _encode_query(self, query: str) -> Optional[np.ndarray]:
        """Encode query to embedding vector"""
        if self.embedding_model is None:
            # Embedding model removed (RAG rebuild pending). Semantic cache disabled.
            return None
        
        try:
            embedding = self.embedding_model.encode([query])[0]
            return np.array(embedding)
        except Exception as e:
            logger.error(f"Query encoding error: {e}")
            return None
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached response for similar query
        
        Args:
            query: User query text
            
        Returns:
            Cached response dict or None if no similar query found
        """
        # Encode query
        query_embedding = self._encode_query(query)
        if query_embedding is None:
            return None
        
        # Get all cached queries with embeddings
        try:
            keys = self.redis.keys(f"{self.prefix}*")
            
            if not keys:
                logger.debug("L2 MISS: No cached queries")
                return None
            
            best_match = None
            best_similarity = 0.0
            best_key = None
            
            # Find most similar cached query
            for key in keys:
                if key.endswith(':meta'):
                    continue
                
                cached_data = self.redis.get(key)
                if not cached_data:
                    continue
                
                data = json.loads(cached_data)
                cached_embedding = np.array(data.get('embedding', []))
                
                if len(cached_embedding) == 0:
                    continue
                
                similarity = self._cosine_similarity(query_embedding, cached_embedding)
                
                if similarity > best_similarity:
                    best_similarity = similarity
                    best_match = data
                    best_key = key
            
            # Check if best match exceeds threshold
            if best_similarity >= self.similarity_threshold:
                logger.info(
                    f"L2 HIT: similarity={best_similarity:.3f}, "
                    f"query='{query[:50]}...'"
                )
                
                # Increment hit count
                if best_key:
                    self.redis.hincrby(f"{best_key}:meta", "hits", 1)
                
                return best_match.get('response')
            
            logger.debug(
                f"L2 MISS: best_similarity={best_similarity:.3f} < {self.similarity_threshold}"
            )
            return None
            
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            return None
    
    def set(
        self,
        query: str,
        response: Dict[str, Any],
        content_type: Optional[str] = None,
        access_count: int = 0
    ) -> bool:
        """
        Store response in semantic cache with adaptive TTL
        
        Args:
            query: User query text
            response: Response data to cache
            content_type: Content type for TTL calculation
            access_count: Previous access count
            
        Returns:
            True if successfully cached
        """
        # Encode query
        query_embedding = self._encode_query(query)
        if query_embedding is None:
            return False
        
        # Infer content type if not provided
        if content_type is None:
            content_type = AdaptiveTTL.get_content_type_from_query(query)
        
        # Calculate query complexity
        complexity = AdaptiveTTL.get_query_complexity(query)
        
        # Calculate adaptive TTL
        ttl = AdaptiveTTL.calculate(
            content_type=content_type,
            access_count=access_count,
            query_complexity=complexity,
            current_time=datetime.now()
        )
        
        key = self._get_key(query)
        
        try:
            # Check current size
            current_size = self.redis.dbsize()
            if current_size >= self.max_entries:
                logger.warning(f"L2 cache full ({current_size} entries)")
            
            # Store response with embedding
            cache_data = {
                'query': query,
                'response': response,
                'embedding': query_embedding.tolist(),
                'content_type': content_type,
                'complexity': complexity,
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
                "content_type": content_type,
                "complexity": complexity,
                "ttl": ttl,
                "hits": 0,
                "created": str(self.redis.time()[0])
            })
            self.redis.expire(f"{key}:meta", ttl)
            
            logger.debug(
                f"L2 SET: query='{query[:50]}...', "
                f"type={content_type}, complexity={complexity}, TTL={ttl}s"
            )
            return True
            
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
            return False
    
    def invalidate(self, query: str) -> bool:
        """Invalidate specific query"""
        key = self._get_key(query)
        
        try:
            deleted = self.redis.delete(key, f"{key}:meta")
            if deleted:
                logger.info(f"L2 INVALIDATE: {query[:50]}...")
            return deleted > 0
        except Exception as e:
            logger.error(f"L2 invalidate error: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear entire L2 cache"""
        try:
            self.redis.flushdb()
            logger.info("L2 cache cleared")
            return True
        except Exception as e:
            logger.error(f"L2 clear error: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            info = self.redis.info('stats')
            return {
                'level': 'L2',
                'name': 'Semantic Cache',
                'size': self.redis.dbsize(),
                'max_entries': self.max_entries,
                'similarity_threshold': self.similarity_threshold,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
            }
        except Exception as e:
            logger.error(f"L2 stats error: {e}")
            return {}
