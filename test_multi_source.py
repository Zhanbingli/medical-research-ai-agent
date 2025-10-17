#!/usr/bin/env python3
"""
Test script for multi-source literature search functionality.

Tests PubMed, Semantic Scholar, and Europe PMC integration.
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data_sources import (
    PubMedClient,
    SemanticScholarClient,
    EuropePMCClient,
    UnifiedSearchClient
)


def test_pubmed():
    """Test PubMed client."""
    print("\n" + "="*60)
    print("Testing PubMed")
    print("="*60)

    try:
        client = PubMedClient()
        articles = client.search_and_fetch("diabetes", max_results=2)

        print(f"✓ PubMed client initialized")
        print(f"✓ Found {len(articles)} articles")

        if articles:
            article = articles[0]
            print(f"\nSample article:")
            print(f"  Title: {article['title'][:60]}...")
            print(f"  Authors: {', '.join(article.get('authors', [])[:2])}")
            print(f"  Source: {article.get('source', 'pubmed')}")

        return True

    except Exception as e:
        print(f"✗ PubMed test failed: {e}")
        return False


def test_semantic_scholar():
    """Test Semantic Scholar client."""
    print("\n" + "="*60)
    print("Testing Semantic Scholar")
    print("="*60)

    try:
        client = SemanticScholarClient()
        articles = client.search_and_fetch(
            "machine learning healthcare",
            max_results=2,
            fields_of_study=["Medicine", "Computer Science"]
        )

        print(f"✓ Semantic Scholar client initialized")
        print(f"✓ Found {len(articles)} articles")

        if articles:
            article = articles[0]
            print(f"\nSample article:")
            print(f"  Title: {article['title'][:60]}...")
            print(f"  Citations: {article.get('citation_count', 0)}")
            print(f"  Open Access: {article.get('open_access', False)}")
            print(f"  Source: {article.get('source', 'semantic_scholar')}")
            if article.get('pdf_url'):
                print(f"  PDF: {article['pdf_url'][:50]}...")

        return True

    except Exception as e:
        print(f"✗ Semantic Scholar test failed: {e}")
        return False


def test_europe_pmc():
    """Test Europe PMC client."""
    print("\n" + "="*60)
    print("Testing Europe PMC")
    print("="*60)

    try:
        client = EuropePMCClient()
        articles = client.search_and_fetch("diabetes", max_results=2)

        print(f"✓ Europe PMC client initialized")
        print(f"✓ Found {len(articles)} articles")

        if articles:
            article = articles[0]
            print(f"\nSample article:")
            print(f"  Title: {article['title'][:60]}...")
            print(f"  Journal: {article.get('journal', 'N/A')}")
            print(f"  Open Access: {article.get('open_access', False)}")
            print(f"  Source: {article.get('source', 'europe_pmc')}")

        return True

    except Exception as e:
        print(f"✗ Europe PMC test failed: {e}")
        return False


def test_unified_search():
    """Test unified search client."""
    print("\n" + "="*60)
    print("Testing Unified Search")
    print("="*60)

    try:
        client = UnifiedSearchClient()

        available = client.get_available_sources()
        print(f"✓ Unified client initialized")
        print(f"✓ Available sources: {', '.join(available)}")

        # Test single source search
        print(f"\nTesting single source search...")
        if 'pubmed' in available:
            articles = client.search_single_source(
                source='pubmed',
                query='diabetes',
                max_results=1
            )
            print(f"✓ Single source search: {len(articles)} article(s)")

        # Test multi-source search
        print(f"\nTesting multi-source search...")
        results = client.search_all_sources(
            query='machine learning',
            max_results_per_source=1
        )

        total = sum(len(articles) for articles in results.values())
        print(f"✓ Multi-source search: {total} total articles")

        for source, articles in results.items():
            print(f"  - {source}: {len(articles)} article(s)")

        # Test merge functionality
        print(f"\nTesting merge and deduplication...")
        merged = client.search_and_merge(
            query='diabetes',
            max_results_per_source=2,
            deduplicate=True,
            sort_by='citation_count'
        )

        print(f"✓ Merged results: {len(merged)} unique articles")

        if merged:
            top = merged[0]
            print(f"\nTop article:")
            print(f"  Title: {top['title'][:60]}...")
            print(f"  Source: {top.get('source', 'unknown')}")
            print(f"  Citations: {top.get('citation_count', 0)}")

        return True

    except Exception as e:
        print(f"✗ Unified search test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_statistics():
    """Test statistics functionality."""
    print("\n" + "="*60)
    print("Testing Statistics")
    print("="*60)

    try:
        client = UnifiedSearchClient()

        results = client.search_all_sources(
            'diabetes treatment',
            max_results_per_source=5
        )

        stats = client.get_statistics(results)

        print(f"✓ Statistics generated")
        print(f"\nStatistics:")
        print(f"  Total articles: {stats['total_articles']}")
        print(f"  Open access: {stats['open_access_count']}")
        print(f"  With PDF: {stats['with_pdf_count']}")
        print(f"  Avg citations: {stats['avg_citation_count']:.1f}")

        print(f"\n  By source:")
        for source, count in stats['by_source'].items():
            print(f"    - {source}: {count}")

        return True

    except Exception as e:
        print(f"✗ Statistics test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("Multi-Source Literature Search Tests")
    print("="*60)

    results = {}

    # Run tests
    results['PubMed'] = test_pubmed()
    results['Semantic Scholar'] = test_semantic_scholar()
    results['Europe PMC'] = test_europe_pmc()
    results['Unified Search'] = test_unified_search()
    results['Statistics'] = test_statistics()

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name}: {status}")

    passed_count = sum(1 for p in results.values() if p)
    total_count = len(results)

    print(f"\nTotal: {passed_count}/{total_count} tests passed")

    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️ {total_count - passed_count} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
