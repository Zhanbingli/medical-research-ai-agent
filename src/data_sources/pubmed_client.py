"""Lightweight PubMed API client using Biopython's Entrez utilities."""
from typing import List, Dict, Optional
from Bio import Entrez, Medline
import os
import logging
import time
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class PubMedClient:
    """Client for interacting with PubMed/NCBI databases with basic rate limiting."""

    # NCBI recommends max 3 requests per second without API key
    REQUEST_DELAY = 0.34  # ~3 requests per second

    def __init__(self, email: Optional[str] = None, request_delay: Optional[float] = None):
        """
        Initialize PubMed client.

        Args:
            email: Email address for NCBI (recommended for better rate limits)
            request_delay: Optional override for request delay in seconds
        """
        self.email = email or os.getenv("PUBMED_EMAIL", "user@example.com")
        Entrez.email = self.email
        # Set tool name for NCBI tracking
        Entrez.tool = "MedPaperAgent"

        self.request_delay = self._resolve_request_delay(request_delay)
        self._last_request_time = 0

    def _rate_limit(self):
        """Enforce rate limiting for NCBI API."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _resolve_request_delay(self, request_delay: Optional[float]) -> float:
        """Resolve request delay from argument, env, or default constant."""
        if request_delay is not None:
            return max(request_delay, 0.0)

        env_delay = os.getenv("PUBMED_REQUEST_DELAY")
        if env_delay:
            try:
                parsed = float(env_delay)
                if parsed < 0:
                    raise ValueError("Request delay must be non-negative.")
                return parsed
            except Exception as exc:  # pragma: no cover - defensive parsing
                logger.warning(f"Invalid PUBMED_REQUEST_DELAY '{env_delay}', using default: {exc}")

        return self.REQUEST_DELAY

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
        logger.info(f"Searching PubMed API")
        pmids = self.search(query, max_results, **kwargs)

        if not pmids:
            return []

        articles = self.fetch_details(pmids)

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
