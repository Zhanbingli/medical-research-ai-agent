"""
PubMed API client for searching and fetching medical literature.
Uses Bio.Entrez from Biopython for NCBI E-utilities access.

Improvements:
- Added integrated caching support
- Enhanced error handling with retries
- Added request rate limiting
- Improved logging
- Added batch fetching optimization
"""
from typing import List, Dict, Optional
from Bio import Entrez, Medline
import os
import logging
import time
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedClient:
    """Client for interacting with PubMed/NCBI databases with caching and rate limiting."""

    # NCBI recommends max 3 requests per second without API key
    REQUEST_DELAY = 0.34  # ~3 requests per second

    def __init__(self, email: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize PubMed client with caching support.

        Args:
            email: Email address for NCBI (recommended for better rate limits)
            enable_cache: Enable caching for queries (default: True)
        """
        self.email = email or os.getenv("PUBMED_EMAIL", "user@example.com")
        Entrez.email = self.email
        # Set tool name for NCBI tracking
        Entrez.tool = "MedPaperAgent"

        self.enable_cache = enable_cache
        self._cache_manager = None
        self._last_request_time = 0

        # Initialize cache if enabled
        if self.enable_cache:
            try:
                from src.utils.cache_manager import get_cache_manager
                self._cache_manager = get_cache_manager()
                logger.info("PubMed caching enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize cache: {e}")
                self.enable_cache = False

    def _rate_limit(self):
        """Enforce rate limiting for NCBI API."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
        min_date: Optional[str] = None,
        max_date: Optional[str] = None,
        retries: int = 3
    ) -> List[str]:
        """
        Search PubMed for articles matching query with retry logic.

        Args:
            query: Search query (supports PubMed syntax)
            max_results: Maximum number of results to return
            sort: Sort order ('relevance', 'pub_date', 'first_author')
            min_date: Minimum publication date (YYYY/MM/DD)
            max_date: Maximum publication date (YYYY/MM/DD)
            retries: Number of retry attempts on failure

        Returns:
            List of PubMed IDs (PMIDs)
        """
        last_error = None

        for attempt in range(retries):
            try:
                self._rate_limit()

                logger.info(f"Searching PubMed: '{query}' (max_results={max_results})")

                handle = Entrez.esearch(
                    db="pubmed",
                    term=query,
                    retmax=max_results,
                    sort=sort,
                    mindate=min_date,
                    maxdate=max_date,
                    datetype="pdat"  # publication date
                )
                record = Entrez.read(handle)
                handle.close()

                pmids = record["IdList"]
                logger.info(f"Found {len(pmids)} articles")

                return pmids

            except Exception as e:
                last_error = e
                logger.warning(f"PubMed search attempt {attempt + 1}/{retries} failed: {e}")

                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff

        logger.error(f"All PubMed search attempts failed: {last_error}")
        return []

    def fetch_details(self, pmids: List[str]) -> List[Dict]:
        """
        Fetch detailed information for given PubMed IDs.

        Args:
            pmids: List of PubMed IDs

        Returns:
            List of article details as dictionaries
        """
        if not pmids:
            return []

        try:
            # Fetch in MEDLINE format
            handle = Entrez.efetch(
                db="pubmed",
                id=pmids,
                rettype="medline",
                retmode="text"
            )
            records = Medline.parse(handle)

            articles = []
            for record in records:
                article = self._parse_medline_record(record)
                articles.append(article)

            handle.close()
            return articles

        except Exception as e:
            print(f"Error fetching details: {e}")
            return []

    def _parse_medline_record(self, record: Dict) -> Dict:
        """Parse MEDLINE record into standardized format."""
        return {
            "pmid": record.get("PMID", ""),
            "title": record.get("TI", ""),
            "abstract": record.get("AB", ""),
            "authors": record.get("AU", []),
            "journal": record.get("JT", ""),
            "pub_date": record.get("DP", ""),
            "doi": record.get("AID", [""])[0] if record.get("AID") else "",
            "keywords": record.get("OT", []),
            "mesh_terms": record.get("MH", []),
            "publication_types": record.get("PT", []),
            "language": record.get("LA", [""])[0] if record.get("LA") else "",
            "country": record.get("PL", ""),
        }

    def search_and_fetch(
        self,
        query: str,
        max_results: int = 10,
        **kwargs
    ) -> List[Dict]:
        """
        Search and fetch article details in one call with caching support.

        Args:
            query: Search query
            max_results: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            List of article details
        """
        # Check cache first
        if self.enable_cache and self._cache_manager:
            cached = self._cache_manager.get_pubmed_query(
                query=query,
                max_results=max_results,
                **kwargs
            )

            if cached:
                logger.info(f"Cache hit for PubMed query: '{query}'")
                return cached

        # Fetch from API
        logger.info(f"Cache miss - fetching from PubMed API")
        pmids = self.search(query, max_results, **kwargs)

        if not pmids:
            return []

        articles = self.fetch_details(pmids)

        # Cache the results
        if self.enable_cache and self._cache_manager and articles:
            self._cache_manager.set_pubmed_query(
                query=query,
                max_results=max_results,
                results=articles,
                **kwargs
            )
            logger.info(f"Cached {len(articles)} articles for query: '{query}'")

        return articles

    def get_abstract(self, pmid: str) -> Optional[str]:
        """
        Get abstract for a single article.

        Args:
            pmid: PubMed ID

        Returns:
            Abstract text or None
        """
        articles = self.fetch_details([pmid])
        if articles:
            return articles[0].get("abstract")
        return None

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
        pmid = article.get("pmid", "")

        citation = f"{author_str}. {title} {journal}. {year}. PMID: {pmid}"
        return citation

    def get_pubmed_url(self, pmid: str) -> str:
        """Get PubMed URL for an article."""
        return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


# Example usage
if __name__ == "__main__":
    client = PubMedClient()

    # Search example
    results = client.search_and_fetch("diabetes machine learning", max_results=3)

    for article in results:
        print(f"\nTitle: {article['title']}")
        print(f"PMID: {article['pmid']}")
        print(f"Authors: {', '.join(article['authors'][:3])}")
        print(f"Abstract: {article['abstract'][:200]}...")
        print(f"URL: {client.get_pubmed_url(article['pmid'])}")
