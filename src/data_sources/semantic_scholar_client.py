"""
Semantic Scholar API client for academic literature search.

Semantic Scholar is a free AI-powered research tool that indexes
200M+ papers including medical literature.

API Docs: https://api.semanticscholar.org/
"""
from typing import List, Dict, Optional
import requests
import time
import logging
from .base_client import BaseLiteratureClient, Article

logger = logging.getLogger(__name__)


class SemanticScholarClient(BaseLiteratureClient):
    """Client for Semantic Scholar Academic Graph API."""

    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    REQUEST_DELAY = 0.1  # 10 requests per second (free tier)

    def __init__(
        self,
        api_key: Optional[str] = None,
        enable_cache: bool = True
    ):
        """
        Initialize Semantic Scholar client.

        Args:
            api_key: Optional API key for higher rate limits
            enable_cache: Enable caching for queries
        """
        super().__init__(enable_cache)
        self.api_key = api_key
        self._last_request_time = 0

        logger.info("Semantic Scholar client initialized")

    def _rate_limit(self):
        """Enforce rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        if time_since_last < self.REQUEST_DELAY:
            sleep_time = self.REQUEST_DELAY - time_since_last
            time.sleep(sleep_time)

        self._last_request_time = time.time()

    def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict] = None
    ) -> Optional[Dict]:
        """
        Make API request with error handling.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            Response JSON or None on error
        """
        self._rate_limit()

        headers = {}
        if self.api_key:
            headers['x-api-key'] = self.api_key

        try:
            url = f"{self.BASE_URL}{endpoint}"
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                logger.warning("Rate limit exceeded. Consider getting an API key.")
            else:
                logger.error(f"HTTP error: {e}")
            return None

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    def search(
        self,
        query: str,
        max_results: int = 10,
        year: Optional[str] = None,
        fields_of_study: Optional[List[str]] = None,
        open_access_only: bool = False,
        **kwargs
    ) -> List[str]:
        """
        Search for papers on Semantic Scholar.

        Args:
            query: Search query
            max_results: Maximum number of results (max 100 per request)
            year: Filter by year (e.g., "2020" or "2020-2023")
            fields_of_study: Filter by fields (e.g., ["Medicine", "Biology"])
            open_access_only: Only return open access papers

        Returns:
            List of paper IDs
        """
        params = {
            'query': query,
            'limit': min(max_results, 100),
            'fields': 'paperId'
        }

        if year:
            params['year'] = year

        if fields_of_study:
            params['fieldsOfStudy'] = ','.join(fields_of_study)

        if open_access_only:
            params['openAccessPdf'] = ''

        try:
            logger.info(f"Searching Semantic Scholar: '{query}' (max={max_results})")

            data = self._make_request('/paper/search', params)

            if not data or 'data' not in data:
                logger.warning("No results returned")
                return []

            paper_ids = [paper['paperId'] for paper in data['data'] if 'paperId' in paper]
            logger.info(f"Found {len(paper_ids)} papers")

            return paper_ids

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def fetch_details(self, ids: List[str]) -> List[Article]:
        """
        Fetch detailed information for papers.

        Args:
            ids: List of paper IDs

        Returns:
            List of Article objects
        """
        if not ids:
            return []

        articles = []
        fields = 'paperId,title,abstract,authors,year,journal,citationCount,openAccessPdf,externalIds,url'

        for paper_id in ids:
            try:
                data = self._make_request(f'/paper/{paper_id}', {'fields': fields})

                if not data:
                    continue

                # Extract data
                article = Article(
                    id=data.get('paperId', ''),
                    title=data.get('title', ''),
                    abstract=data.get('abstract', ''),
                    authors=[author.get('name', '') for author in data.get('authors', [])],
                    journal=data.get('journal', {}).get('name', '') if data.get('journal') else '',
                    pub_date=str(data.get('year', '')),
                    doi=data.get('externalIds', {}).get('DOI', ''),
                    url=data.get('url', ''),
                    source='semantic_scholar',
                    citation_count=data.get('citationCount', 0),
                    pdf_url=data.get('openAccessPdf', {}).get('url', '') if data.get('openAccessPdf') else '',
                    open_access=bool(data.get('openAccessPdf'))
                )

                articles.append(article)

            except Exception as e:
                logger.warning(f"Failed to fetch details for {paper_id}: {e}")
                continue

        logger.info(f"Fetched details for {len(articles)} papers")
        return articles

    def get_source_name(self) -> str:
        """Get source name."""
        return "semantic_scholar"

    def get_paper_by_doi(self, doi: str) -> Optional[Dict]:
        """
        Get paper by DOI.

        Args:
            doi: Paper DOI

        Returns:
            Article dictionary or None
        """
        fields = 'paperId,title,abstract,authors,year,journal,citationCount,openAccessPdf,url'

        try:
            data = self._make_request(f'/paper/DOI:{doi}', {'fields': fields})

            if not data:
                return None

            article = Article(
                id=data.get('paperId', ''),
                title=data.get('title', ''),
                abstract=data.get('abstract', ''),
                authors=[author.get('name', '') for author in data.get('authors', [])],
                journal=data.get('journal', {}).get('name', '') if data.get('journal') else '',
                pub_date=str(data.get('year', '')),
                doi=doi,
                url=data.get('url', ''),
                source='semantic_scholar',
                citation_count=data.get('citationCount', 0),
                pdf_url=data.get('openAccessPdf', {}).get('url', '') if data.get('openAccessPdf') else '',
                open_access=bool(data.get('openAccessPdf'))
            )

            return article.to_dict()

        except Exception as e:
            logger.error(f"Failed to fetch paper by DOI: {e}")
            return None

    def get_recommendations(
        self,
        paper_id: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Get paper recommendations based on a paper.

        Args:
            paper_id: Paper ID
            max_results: Maximum recommendations

        Returns:
            List of recommended article dictionaries
        """
        params = {
            'fields': 'paperId,title,abstract,authors,year',
            'limit': max_results
        }

        try:
            data = self._make_request(
                f'/paper/{paper_id}/recommendations',
                params
            )

            if not data or 'recommendedPapers' not in data:
                return []

            paper_ids = [
                paper['paperId']
                for paper in data['recommendedPapers']
                if 'paperId' in paper
            ]

            articles = self.fetch_details(paper_ids)
            return [article.to_dict() for article in articles]

        except Exception as e:
            logger.error(f"Failed to get recommendations: {e}")
            return []


# Example usage
if __name__ == "__main__":
    client = SemanticScholarClient()

    # Search for medical papers
    articles = client.search_and_fetch(
        "diabetes machine learning",
        max_results=5,
        fields_of_study=["Medicine", "Computer Science"]
    )

    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"Authors: {', '.join(article['authors'][:3])}")
        print(f"Year: {article['pub_date']}")
        print(f"Citations: {article['citation_count']}")
        print(f"Open Access: {article['open_access']}")
        if article['pdf_url']:
            print(f"PDF: {article['pdf_url']}")
