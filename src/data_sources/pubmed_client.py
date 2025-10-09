"""
PubMed API client for searching and fetching medical literature.
Uses Bio.Entrez from Biopython for NCBI E-utilities access.
"""
from typing import List, Dict, Optional
from Bio import Entrez, Medline
import os
from datetime import datetime
import json


class PubMedClient:
    """Client for interacting with PubMed/NCBI databases."""

    def __init__(self, email: Optional[str] = None):
        """
        Initialize PubMed client.

        Args:
            email: Email address for NCBI (recommended for better rate limits)
        """
        self.email = email or os.getenv("PUBMED_EMAIL", "user@example.com")
        Entrez.email = self.email
        # Set tool name for NCBI tracking
        Entrez.tool = "MedPaperAgent"

    def search(
        self,
        query: str,
        max_results: int = 10,
        sort: str = "relevance",
        min_date: Optional[str] = None,
        max_date: Optional[str] = None
    ) -> List[str]:
        """
        Search PubMed for articles matching query.

        Args:
            query: Search query (supports PubMed syntax)
            max_results: Maximum number of results to return
            sort: Sort order ('relevance', 'pub_date', 'first_author')
            min_date: Minimum publication date (YYYY/MM/DD)
            max_date: Maximum publication date (YYYY/MM/DD)

        Returns:
            List of PubMed IDs (PMIDs)
        """
        try:
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

            return record["IdList"]
        except Exception as e:
            print(f"Error searching PubMed: {e}")
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
        Search and fetch article details in one call.

        Args:
            query: Search query
            max_results: Maximum number of results
            **kwargs: Additional search parameters

        Returns:
            List of article details
        """
        pmids = self.search(query, max_results, **kwargs)
        if not pmids:
            return []

        return self.fetch_details(pmids)

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
