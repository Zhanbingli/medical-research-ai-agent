"""
Quick test script to verify the installation and API connectivity.
"""
import sys
import os
from dotenv import load_dotenv

def test_imports():
    """Test if all required packages are installed."""
    print("Testing imports...")
    try:
        import streamlit
        import anthropic
        from Bio import Entrez
        import pandas
        print("✓ All required packages installed")
        return True
    except ImportError as e:
        print(f"✗ Missing package: {e}")
        return False

def test_environment():
    """Test environment configuration."""
    print("\nTesting environment configuration...")
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("✗ ANTHROPIC_API_KEY not configured in .env")
        return False

    print("✓ ANTHROPIC_API_KEY found")
    return True

def test_pubmed():
    """Test PubMed connection."""
    print("\nTesting PubMed connection...")
    try:
        from src.data_sources import PubMedClient
        client = PubMedClient()
        results = client.search("covid-19", max_results=1)
        if results:
            print(f"✓ PubMed connection successful (found PMID: {results[0]})")
            return True
        else:
            print("✗ PubMed search returned no results")
            return False
    except Exception as e:
        print(f"✗ PubMed connection failed: {e}")
        return False

def test_claude():
    """Test Claude API connection."""
    print("\nTesting Claude API connection...")
    load_dotenv()

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("⊘ Skipping Claude test (API key not configured)")
        return None

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=50,
            messages=[{"role": "user", "content": "Hello"}]
        )
        print("✓ Claude API connection successful")
        return True
    except Exception as e:
        print(f"✗ Claude API connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 50)
    print("Medical Literature Agent - Setup Test")
    print("=" * 50)

    results = []

    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_environment()))
    results.append(("PubMed", test_pubmed()))
    results.append(("Claude API", test_claude()))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)

    for name, result in results:
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"{name:20} {status}")

    print("\n" + "=" * 50)

    # Overall status
    failed = sum(1 for _, r in results if r is False)

    if failed == 0:
        print("✅ All tests passed! Ready to run: streamlit run app.py")
        return 0
    else:
        print(f"⚠️  {failed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
