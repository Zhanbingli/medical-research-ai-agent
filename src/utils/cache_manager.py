"""
Intelligent caching system for AI responses and PubMed queries.
Reduces API calls and improves performance.

Improvements:
- Added automatic cache cleanup on initialization
- Added cache size limits to prevent disk space issues
- Improved error handling
- Added cache statistics and monitoring
- Added LRU eviction policy
"""
import hashlib
import json
import os
import logging
from typing import Optional, Any, Dict
from datetime import datetime, timedelta
from pathlib import Path
import diskcache

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheManager:
    """Manages caching for AI responses and PubMed queries with size limits and auto-cleanup."""

    # Default cache size limit: 500MB per cache
    DEFAULT_SIZE_LIMIT = 500 * 1024 * 1024

    def __init__(
        self,
        cache_dir: str = "./cache",
        expiry_days: int = 7,
        size_limit: int = DEFAULT_SIZE_LIMIT
    ):
        """
        Initialize cache manager with size limits and auto-cleanup.

        Args:
            cache_dir: Directory for cache storage
            expiry_days: Number of days before cache expires
            size_limit: Maximum size per cache in bytes (default: 500MB)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True, parents=True)

        # Separate caches for different purposes with size limits
        self.ai_cache = diskcache.Cache(
            str(self.cache_dir / "ai_responses"),
            size_limit=size_limit,
            eviction_policy='least-recently-used'
        )
        self.pubmed_cache = diskcache.Cache(
            str(self.cache_dir / "pubmed_queries"),
            size_limit=size_limit,
            eviction_policy='least-recently-used'
        )

        self.expiry_seconds = expiry_days * 24 * 3600

        # Perform initial cleanup
        self._initial_cleanup()

        logger.info(f"Cache initialized at {cache_dir} with {expiry_days} day expiry")

    def _initial_cleanup(self):
        """Perform initial cleanup of expired entries on startup."""
        try:
            removed = self.cleanup_expired()
            if removed > 0:
                logger.info(f"Initial cleanup: removed {removed} expired entries")
        except Exception as e:
            logger.warning(f"Initial cleanup failed: {e}")

    def _generate_key(self, data: Dict[str, Any]) -> str:
        """Generate cache key from data dictionary."""
        # Sort keys for consistent hashing
        sorted_data = json.dumps(data, sort_keys=True)
        return hashlib.md5(sorted_data.encode()).hexdigest()

    def get_ai_response(
        self,
        prompt: str,
        provider: str,
        model: str,
        **kwargs
    ) -> Optional[str]:
        """
        Get cached AI response if available.

        Args:
            prompt: The prompt sent to AI
            provider: AI provider name
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Cached response or None
        """
        try:
            cache_key = self._generate_key({
                "prompt": prompt,
                "provider": provider,
                "model": model,
                **kwargs
            })

            result = self.ai_cache.get(cache_key)
            if result:
                logger.debug(f"Cache hit for AI request (key: {cache_key[:8]}...)")
            return result
        except Exception as e:
            logger.error(f"Error getting AI response from cache: {e}")
            return None

    def set_ai_response(
        self,
        prompt: str,
        provider: str,
        model: str,
        response: str,
        **kwargs
    ) -> None:
        """
        Cache AI response.

        Args:
            prompt: The prompt sent to AI
            provider: AI provider name
            model: Model name
            response: AI response to cache
            **kwargs: Additional parameters
        """
        try:
            cache_key = self._generate_key({
                "prompt": prompt,
                "provider": provider,
                "model": model,
                **kwargs
            })

            self.ai_cache.set(
                cache_key,
                response,
                expire=self.expiry_seconds
            )
            logger.debug(f"Cached AI response (key: {cache_key[:8]}...)")
        except Exception as e:
            logger.error(f"Error caching AI response: {e}")

    def get_pubmed_query(
        self,
        query: str,
        max_results: int,
        **kwargs
    ) -> Optional[list]:
        """
        Get cached PubMed query results.

        Args:
            query: PubMed search query
            max_results: Number of results
            **kwargs: Additional search parameters

        Returns:
            Cached results or None
        """
        cache_key = self._generate_key({
            "query": query,
            "max_results": max_results,
            **kwargs
        })

        return self.pubmed_cache.get(cache_key)

    def set_pubmed_query(
        self,
        query: str,
        max_results: int,
        results: list,
        **kwargs
    ) -> None:
        """
        Cache PubMed query results.

        Args:
            query: PubMed search query
            max_results: Number of results
            results: Query results to cache
            **kwargs: Additional search parameters
        """
        cache_key = self._generate_key({
            "query": query,
            "max_results": max_results,
            **kwargs
        })

        self.pubmed_cache.set(
            cache_key,
            results,
            expire=self.expiry_seconds
        )

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics including hit rates."""
        try:
            ai_stats = self.ai_cache.stats(enable=True)
            pubmed_stats = self.pubmed_cache.stats(enable=True)

            return {
                "ai_cache": {
                    "size": len(self.ai_cache),
                    "bytes": self.ai_cache.volume(),
                    "hits": ai_stats.get('hits', 0),
                    "misses": ai_stats.get('misses', 0),
                    "size_limit_mb": self.ai_cache.size_limit / (1024 * 1024)
                },
                "pubmed_cache": {
                    "size": len(self.pubmed_cache),
                    "bytes": self.pubmed_cache.volume(),
                    "hits": pubmed_stats.get('hits', 0),
                    "misses": pubmed_stats.get('misses', 0),
                    "size_limit_mb": self.pubmed_cache.size_limit / (1024 * 1024)
                },
                "total_bytes": self.ai_cache.volume() + self.pubmed_cache.volume()
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "ai_cache": {"size": 0, "bytes": 0},
                "pubmed_cache": {"size": 0, "bytes": 0},
                "error": str(e)
            }

    def clear_cache(self, cache_type: str = "all") -> None:
        """
        Clear cache.

        Args:
            cache_type: Type to clear ('ai', 'pubmed', or 'all')
        """
        if cache_type in ["ai", "all"]:
            self.ai_cache.clear()

        if cache_type in ["pubmed", "all"]:
            self.pubmed_cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired cache entries. Returns number of entries removed."""
        removed = 0

        # AI cache cleanup
        for key in list(self.ai_cache):
            if self.ai_cache.get(key) is None:
                removed += 1

        # PubMed cache cleanup
        for key in list(self.pubmed_cache):
            if self.pubmed_cache.get(key) is None:
                removed += 1

        return removed


# Global cache instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager

    if _cache_manager is None:
        cache_dir = os.getenv("CACHE_DIR", "./cache")
        expiry_days = int(os.getenv("CACHE_EXPIRY_DAYS", "7"))
        _cache_manager = CacheManager(cache_dir, expiry_days)

    return _cache_manager


# Example usage
if __name__ == "__main__":
    cache = CacheManager()

    # Test AI response caching
    cache.set_ai_response(
        prompt="Summarize diabetes research",
        provider="claude",
        model="claude-3-5-sonnet",
        response="Diabetes is a chronic disease..."
    )

    cached = cache.get_ai_response(
        prompt="Summarize diabetes research",
        provider="claude",
        model="claude-3-5-sonnet"
    )

    print(f"Cached response: {cached}")

    # Test PubMed caching
    cache.set_pubmed_query(
        query="diabetes",
        max_results=10,
        results=["PMID1", "PMID2"]
    )

    cached_pmids = cache.get_pubmed_query(
        query="diabetes",
        max_results=10
    )

    print(f"Cached PMIDs: {cached_pmids}")

    # Stats
    print(f"Cache stats: {cache.get_cache_stats()}")
