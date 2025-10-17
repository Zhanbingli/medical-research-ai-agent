"""
Unified search interface for multiple literature databases.

Allows searching across PubMed, Semantic Scholar, and Europe PMC simultaneously.
"""
from typing import List, Dict, Optional
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from .pubmed_client import PubMedClient
from .semantic_scholar_client import SemanticScholarClient
from .europe_pmc_client import EuropePMCClient

logger = logging.getLogger(__name__)


class UnifiedSearchClient:
    """Unified client for searching across multiple literature databases."""

    def __init__(
        self,
        pubmed_email: Optional[str] = None,
        semantic_scholar_api_key: Optional[str] = None,
        europe_pmc_email: Optional[str] = None,
        enable_cache: bool = True
    ):
        """
        Initialize unified search client.

        Args:
            pubmed_email: Email for PubMed API
            semantic_scholar_api_key: API key for Semantic Scholar
            europe_pmc_email: Email for Europe PMC
            enable_cache: Enable caching for all clients
        """
        self.clients = {}

        # Initialize available clients
        try:
            self.clients['pubmed'] = PubMedClient(
                email=pubmed_email,
                enable_cache=enable_cache
            )
            logger.info("✓ PubMed client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize PubMed: {e}")

        try:
            self.clients['semantic_scholar'] = SemanticScholarClient(
                api_key=semantic_scholar_api_key,
                enable_cache=enable_cache
            )
            logger.info("✓ Semantic Scholar client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Semantic Scholar: {e}")

        try:
            self.clients['europe_pmc'] = EuropePMCClient(
                email=europe_pmc_email,
                enable_cache=enable_cache
            )
            logger.info("✓ Europe PMC client initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize Europe PMC: {e}")

        if not self.clients:
            raise ValueError("No literature database clients available")

        logger.info(f"Unified search ready with {len(self.clients)} sources")

    def get_available_sources(self) -> List[str]:
        """
        Get list of available data sources.

        Returns:
            List of source names
        """
        return list(self.clients.keys())

    def search_single_source(
        self,
        source: str,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Dict]:
        """
        Search a single data source.

        Args:
            source: Source name (pubmed, semantic_scholar, europe_pmc)
            query: Search query
            max_results: Maximum number of results per source
            **kwargs: Additional source-specific parameters

        Returns:
            List of article dictionaries
        """
        if source not in self.clients:
            logger.error(f"Source '{source}' not available")
            return []

        try:
            client = self.clients[source]
            articles = client.search_and_fetch(query, max_results, **kwargs)
            logger.info(f"Retrieved {len(articles)} articles from {source}")
            return articles

        except Exception as e:
            logger.error(f"Search failed for {source}: {e}")
            return []

    def search_all_sources(
        self,
        query: str,
        max_results_per_source: int = 10,
        parallel: bool = True,
        **kwargs
    ) -> Dict[str, List[Dict]]:
        """
        Search all available data sources.

        Args:
            query: Search query
            max_results_per_source: Maximum results per source
            parallel: Execute searches in parallel
            **kwargs: Additional source-specific parameters

        Returns:
            Dictionary mapping source names to article lists
        """
        results = {}

        if parallel:
            # Parallel execution for faster results
            with ThreadPoolExecutor(max_workers=len(self.clients)) as executor:
                future_to_source = {
                    executor.submit(
                        self.search_single_source,
                        source,
                        query,
                        max_results_per_source,
                        **kwargs
                    ): source
                    for source in self.clients.keys()
                }

                for future in as_completed(future_to_source):
                    source = future_to_source[future]
                    try:
                        results[source] = future.result()
                    except Exception as e:
                        logger.error(f"Parallel search failed for {source}: {e}")
                        results[source] = []

        else:
            # Sequential execution
            for source in self.clients.keys():
                results[source] = self.search_single_source(
                    source, query, max_results_per_source, **kwargs
                )

        return results

    def search_and_merge(
        self,
        query: str,
        max_results_per_source: int = 10,
        total_max_results: Optional[int] = None,
        deduplicate: bool = True,
        sort_by: str = "citation_count",  # citation_count, pub_date, relevance
        **kwargs
    ) -> List[Dict]:
        """
        Search all sources and merge results.

        Args:
            query: Search query
            max_results_per_source: Maximum results per source
            total_max_results: Maximum total results after merging
            deduplicate: Remove duplicate articles (by DOI and title)
            sort_by: Sort merged results by field
            **kwargs: Additional parameters

        Returns:
            Merged and sorted list of articles
        """
        # Search all sources
        all_results = self.search_all_sources(
            query, max_results_per_source, parallel=True, **kwargs
        )

        # Merge results
        merged = []
        for source, articles in all_results.items():
            merged.extend(articles)

        logger.info(f"Total articles before processing: {len(merged)}")

        # Deduplicate
        if deduplicate:
            merged = self._deduplicate_articles(merged)
            logger.info(f"Articles after deduplication: {len(merged)}")

        # Sort
        merged = self._sort_articles(merged, sort_by)

        # Limit total results
        if total_max_results:
            merged = merged[:total_max_results]

        logger.info(f"Final article count: {len(merged)}")
        return merged

    def _deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """
        Remove duplicate articles based on DOI and title similarity.

        Args:
            articles: List of article dictionaries

        Returns:
            Deduplicated list
        """
        seen_dois = set()
        seen_titles = set()
        unique_articles = []

        for article in articles:
            # Check DOI
            doi = article.get('doi', '').lower()
            if doi and doi in seen_dois:
                continue

            # Check title (normalize and compare)
            title = article.get('title', '').lower().strip()
            title_normalized = ''.join(c for c in title if c.isalnum() or c.isspace())

            if title_normalized and title_normalized in seen_titles:
                continue

            # Add to unique set
            if doi:
                seen_dois.add(doi)
            if title_normalized:
                seen_titles.add(title_normalized)

            unique_articles.append(article)

        return unique_articles

    def _sort_articles(self, articles: List[Dict], sort_by: str) -> List[Dict]:
        """
        Sort articles by specified field.

        Args:
            articles: List of article dictionaries
            sort_by: Field to sort by

        Returns:
            Sorted list
        """
        try:
            if sort_by == "citation_count":
                return sorted(
                    articles,
                    key=lambda x: x.get('citation_count', 0),
                    reverse=True
                )
            elif sort_by == "pub_date":
                return sorted(
                    articles,
                    key=lambda x: x.get('pub_date', ''),
                    reverse=True
                )
            else:
                # Default: keep original order (relevance from each source)
                return articles

        except Exception as e:
            logger.warning(f"Sorting failed: {e}")
            return articles

    def get_statistics(self, results: Dict[str, List[Dict]]) -> Dict:
        """
        Get statistics about search results.

        Args:
            results: Results from search_all_sources()

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_articles': 0,
            'by_source': {},
            'open_access_count': 0,
            'with_pdf_count': 0,
            'avg_citation_count': 0
        }

        total_citations = 0

        for source, articles in results.items():
            count = len(articles)
            stats['by_source'][source] = count
            stats['total_articles'] += count

            for article in articles:
                if article.get('open_access'):
                    stats['open_access_count'] += 1
                if article.get('pdf_url'):
                    stats['with_pdf_count'] += 1
                total_citations += article.get('citation_count', 0)

        if stats['total_articles'] > 0:
            stats['avg_citation_count'] = total_citations / stats['total_articles']

        return stats


# Example usage
if __name__ == "__main__":
    # Initialize unified client
    client = UnifiedSearchClient(
        pubmed_email="your@email.com"
    )

    print(f"Available sources: {client.get_available_sources()}\n")

    # Search all sources
    query = "COVID-19 vaccine"
    results = client.search_all_sources(query, max_results_per_source=3)

    # Display results by source
    for source, articles in results.items():
        print(f"\n{'='*60}")
        print(f"{source.upper()}: {len(articles)} articles")
        print('='*60)

        for article in articles[:2]:
            print(f"\nTitle: {article['title']}")
            print(f"Source: {article['source']}")
            print(f"Citations: {article.get('citation_count', 0)}")
            print(f"Open Access: {article.get('open_access', False)}")

    # Get statistics
    stats = client.get_statistics(results)
    print(f"\n{'='*60}")
    print("STATISTICS")
    print('='*60)
    print(f"Total articles: {stats['total_articles']}")
    print(f"Open access: {stats['open_access_count']}")
    print(f"With PDF: {stats['with_pdf_count']}")
    print(f"Avg citations: {stats['avg_citation_count']:.1f}")

    # Search and merge
    print(f"\n{'='*60}")
    print("MERGED AND SORTED RESULTS")
    print('='*60)
    merged = client.search_and_merge(
        query,
        max_results_per_source=5,
        total_max_results=10,
        sort_by="citation_count"
    )

    for i, article in enumerate(merged[:5], 1):
        print(f"\n{i}. {article['title']}")
        print(f"   Source: {article['source']}")
        print(f"   Citations: {article.get('citation_count', 0)}")
