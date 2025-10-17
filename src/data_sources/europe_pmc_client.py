"""
Europe PMC API client for medical literature search.

Europe PMC is a free database of life sciences literature including
PubMed, PMC full texts, and preprints from bioRxiv and medRxiv.

API Docs: https://europepmc.org/RestfulWebService
"""
from typing import List, Dict, Optional
import requests
import time
import logging
from .base_client import BaseLiteratureClient, Article

logger = logging.getLogger(__name__)


class EuropePMCClient(BaseLiteratureClient):
    """Client for Europe PMC API."""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"
    REQUEST_DELAY = 0.2  # Conservative rate limiting

    def __init__(self, email: Optional[str] = None, enable_cache: bool = True):
        """
        Initialize Europe PMC client.

        Args:
            email: Contact email (optional but recommended)
            enable_cache: Enable caching for queries
        """
        super().__init__(enable_cache)
        self.email = email
        self._last_request_time = 0

        logger.info("Europe PMC client initialized")

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

        if params is None:
            params = {}

        params['format'] = 'json'

        if self.email:
            params['email'] = self.email

        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return None

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None

    def search(
        self,
        query: str,
        max_results: int = 10,
        source: str = "MED",  # MED=PubMed, PMC=PMC articles, PPR=preprints
        sort: str = "relevance",  # relevance, cited, date
        **kwargs
    ) -> List[str]:
        """
        Search for articles on Europe PMC.

        Args:
            query: Search query
            max_results: Maximum number of results (max 1000)
            source: Data source (MED, PMC, PPR, AGR, CBA, CTX, ETH, HIR, PAT)
            sort: Sort order (relevance, cited, date)

        Returns:
            List of article IDs
        """
        params = {
            'query': query,
            'pageSize': min(max_results, 1000),
            'cursorMark': '*',
            'sort': sort
        }

        try:
            logger.info(f"Searching Europe PMC: '{query}' (max={max_results})")

            data = self._make_request('search', params)

            if not data or 'resultList' not in data:
                logger.warning("No results returned")
                return []

            results = data['resultList'].get('result', [])

            # Extract IDs based on source
            ids = []
            for result in results:
                if 'id' in result:
                    source_type = result.get('source', 'MED')
                    ids.append(f"{source_type}:{result['id']}")

            logger.info(f"Found {len(ids)} articles")
            return ids

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def fetch_details(self, ids: List[str]) -> List[Article]:
        """
        Fetch detailed information for articles.

        Args:
            ids: List of article IDs (format: "SOURCE:ID")

        Returns:
            List of Article objects
        """
        if not ids:
            return []

        articles = []

        for article_id in ids:
            try:
                # Parse source and ID
                if ':' in article_id:
                    source, id_num = article_id.split(':', 1)
                else:
                    source, id_num = 'MED', article_id

                # Fetch article details
                endpoint = f'{source}/{id_num}'
                data = self._make_request(endpoint)

                if not data or 'result' not in data:
                    continue

                result = data['result']

                # Extract data
                authors = []
                if 'authorList' in result and 'author' in result['authorList']:
                    authors = [
                        f"{author.get('firstName', '')} {author.get('lastName', '')}".strip()
                        for author in result['authorList']['author']
                    ]

                # Get abstract
                abstract = result.get('abstractText', '')

                # Get publication date
                pub_date = result.get('firstPublicationDate', '')
                if not pub_date and 'pubYear' in result:
                    pub_date = str(result['pubYear'])

                # Get DOI
                doi = ''
                if 'doi' in result:
                    doi = result['doi']
                elif 'DOI' in result:
                    doi = result['DOI']

                # Get URLs
                url = f"https://europepmc.org/article/{source}/{id_num}"
                pdf_url = ''
                open_access = result.get('isOpenAccess', 'N') == 'Y'

                if open_access and 'fullTextUrlList' in result:
                    urls = result['fullTextUrlList'].get('fullTextUrl', [])
                    for url_item in urls:
                        if url_item.get('documentStyle') == 'pdf':
                            pdf_url = url_item.get('url', '')
                            break

                article = Article(
                    id=id_num,
                    title=result.get('title', ''),
                    abstract=abstract,
                    authors=authors,
                    journal=result.get('journalTitle', ''),
                    pub_date=pub_date,
                    doi=doi,
                    url=url,
                    source='europe_pmc',
                    citation_count=result.get('citedByCount', 0),
                    pdf_url=pdf_url,
                    open_access=open_access
                )

                articles.append(article)

            except Exception as e:
                logger.warning(f"Failed to fetch details for {article_id}: {e}")
                continue

        logger.info(f"Fetched details for {len(articles)} articles")
        return articles

    def get_source_name(self) -> str:
        """Get source name."""
        return "europe_pmc"

    def get_full_text(self, article_id: str) -> Optional[str]:
        """
        Get full text if available.

        Args:
            article_id: Article ID (format: "SOURCE:ID")

        Returns:
            Full text or None
        """
        try:
            if ':' in article_id:
                source, id_num = article_id.split(':', 1)
            else:
                source, id_num = 'PMC', article_id

            endpoint = f'{source}/{id_num}/fullTextXML'
            response = requests.get(f"{self.BASE_URL}/{endpoint}", timeout=30)

            if response.status_code == 200:
                return response.text

            return None

        except Exception as e:
            logger.error(f"Failed to get full text: {e}")
            return None

    def search_preprints(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict]:
        """
        Search for preprints (bioRxiv, medRxiv).

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of article dictionaries
        """
        # Search in preprint sources
        params = {
            'query': f"{query} AND SRC:PPR",
            'pageSize': max_results
        }

        try:
            data = self._make_request('search', params)

            if not data or 'resultList' not in data:
                return []

            results = data['resultList'].get('result', [])
            ids = [f"PPR:{r['id']}" for r in results if 'id' in r]

            articles = self.fetch_details(ids)
            return [article.to_dict() for article in articles]

        except Exception as e:
            logger.error(f"Preprint search failed: {e}")
            return []


# Example usage
if __name__ == "__main__":
    client = EuropePMCClient(email="your@email.com")

    # Search for medical papers
    articles = client.search_and_fetch(
        "COVID-19 vaccine",
        max_results=5,
        sort="cited"
    )

    for article in articles:
        print(f"\nTitle: {article['title']}")
        print(f"Journal: {article['journal']}")
        print(f"Date: {article['pub_date']}")
        print(f"Citations: {article['citation_count']}")
        print(f"Open Access: {article['open_access']}")
        if article['doi']:
            print(f"DOI: {article['doi']}")
