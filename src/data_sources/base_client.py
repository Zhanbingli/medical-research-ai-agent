"""
Base abstract class for literature database clients.

Provides a unified interface for different medical literature sources.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class Article:
    """Standardized article data structure."""
    # Required fields
    id: str  # Database-specific ID (PMID, DOI, etc.)
    title: str
    abstract: str

    # Optional fields
    authors: List[str] = None
    journal: str = ""
    pub_date: str = ""
    doi: str = ""
    url: str = ""
    keywords: List[str] = None
    source: str = ""  # Database source (pubmed, semantic_scholar, etc.)

    # Additional metadata
    citation_count: int = 0
    pdf_url: str = ""
    open_access: bool = False

    def __post_init__(self):
        """Initialize default values for optional fields."""
        if self.authors is None:
            self.authors = []
        if self.keywords is None:
            self.keywords = []

    def to_dict(self) -> Dict:
        """Convert to dictionary for compatibility with existing code."""
        return {
            'pmid': self.id,  # For backward compatibility
            'id': self.id,
            'title': self.title,
            'abstract': self.abstract,
            'authors': self.authors,
            'journal': self.journal,
            'pub_date': self.pub_date,
            'doi': self.doi,
            'url': self.url,
            'keywords': self.keywords,
            'source': self.source,
            'citation_count': self.citation_count,
            'pdf_url': self.pdf_url,
            'open_access': self.open_access
        }


class BaseLiteratureClient(ABC):
    """Abstract base class for literature database clients."""

    def __init__(self, enable_cache: bool = True):
        """
        Initialize client.

        Args:
            enable_cache: Enable caching for queries
        """
        self.enable_cache = enable_cache
        self._cache_manager = None

        if self.enable_cache:
            try:
                from src.utils.cache_manager import get_cache_manager
                self._cache_manager = get_cache_manager()
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}")
                self.enable_cache = False

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[str]:
        """
        Search for articles.

        Args:
            query: Search query
            max_results: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            List of article IDs
        """
        pass

    @abstractmethod
    def fetch_details(self, ids: List[str]) -> List[Article]:
        """
        Fetch detailed information for articles.

        Args:
            ids: List of article IDs

        Returns:
            List of Article objects
        """
        pass

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Dict]:
        """
        Search and fetch article details in one call.

        Args:
            query: Search query
            max_results: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            List of article dictionaries
        """
        # Check cache first
        cache_key_params = {
            'query': query,
            'max_results': max_results,
            'source': self.get_source_name(),
            **kwargs
        }

        if self.enable_cache and self._cache_manager:
            cached = self._cache_manager.get_pubmed_query(**cache_key_params)
            if cached:
                logger.info(f"Cache hit for {self.get_source_name()} query: '{query}'")
                return cached

        # Fetch from API
        logger.info(f"Cache miss - fetching from {self.get_source_name()} API")
        ids = self.search(query, max_results, **kwargs)

        if not ids:
            return []

        articles = self.fetch_details(ids)
        results = [article.to_dict() for article in articles]

        # Cache the results
        if self.enable_cache and self._cache_manager and results:
            self._cache_manager.set_pubmed_query(
                results=results,
                **cache_key_params
            )
            logger.info(f"Cached {len(results)} articles from {self.get_source_name()}")

        return results

    @abstractmethod
    def get_source_name(self) -> str:
        """
        Get the name of this data source.

        Returns:
            Source name (e.g., "pubmed", "semantic_scholar")
        """
        pass

    def format_citation(self, article: Dict) -> str:
        """
        Format article as citation string.

        Args:
            article: Article dictionary

        Returns:
            Formatted citation
        """
        authors = article.get("authors", [])
        author_str = ", ".join(authors[:3])
        if len(authors) > 3:
            author_str += " et al."

        title = article.get("title", "")
        journal = article.get("journal", "")
        year = article.get("pub_date", "").split()[0] if article.get("pub_date") else ""

        return f"{author_str}. {title} {journal}. {year}."
