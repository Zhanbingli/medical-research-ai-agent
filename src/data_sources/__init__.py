"""
Data sources package for medical literature retrieval.

Supports multiple databases:
- PubMed: 35M+ biomedical citations
- Semantic Scholar: 200M+ academic papers with AI-powered search
- Europe PMC: Life sciences literature including preprints
- Unified Search: Search across all sources simultaneously
"""
from .base_client import BaseLiteratureClient, Article
from .pubmed_client import PubMedClient
from .semantic_scholar_client import SemanticScholarClient
from .europe_pmc_client import EuropePMCClient
from .unified_search import UnifiedSearchClient

__all__ = [
    "BaseLiteratureClient",
    "Article",
    "PubMedClient",
    "SemanticScholarClient",
    "EuropePMCClient",
    "UnifiedSearchClient"
]
