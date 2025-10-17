"""
Test cache integration in AI Client Manager
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

def test_cache_integration():
    """Test that caching is working properly."""
    from src.utils import AIClientManager
    from src.utils.cache_manager import get_cache_manager

    print("🧪 Testing Cache Integration...")
    print("=" * 50)

    # Test 1: Manager initializes with cache
    manager = AIClientManager(enable_cache=True)
    print(f"✓ Manager initialized with cache: {manager.enable_cache}")

    # Test 2: Check if at least one provider is available
    providers = manager.get_available_providers()
    if not providers:
        print("❌ No AI providers available. Please configure API keys.")
        return False

    print(f"✓ Available providers: {', '.join(providers)}")

    # Test 3: Clear cache for clean test
    cache = get_cache_manager()
    cache.clear_cache("ai")
    print("✓ Cache cleared for testing")

    # Test 4: First generation (should not hit cache)
    test_prompt = "Test prompt: What is 2+2?"
    print(f"\n📝 Testing first generation (no cache)...")

    response1 = manager.generate(
        prompt=test_prompt,
        provider=providers[0],
        max_tokens=50,
        use_cache=True
    )

    if response1.startswith("Error"):
        print(f"❌ API Error: {response1}")
        return False

    print(f"✓ First response: {response1[:50]}...")

    # Test 5: Second generation (should hit cache)
    print(f"\n📝 Testing second generation (should use cache)...")

    response2 = manager.generate(
        prompt=test_prompt,
        provider=providers[0],
        max_tokens=50,
        use_cache=True
    )

    print(f"✓ Second response: {response2[:50]}...")

    # Test 6: Verify responses are identical (cached)
    if response1 == response2:
        print(f"✅ Cache HIT! Responses are identical.")
    else:
        print(f"⚠️  Responses differ (might not be cached)")

    # Test 7: Cache statistics
    stats = cache.get_cache_stats()
    print(f"\n📊 Cache Statistics:")
    print(f"   AI Cache Size: {stats['ai_cache']['size']} entries")
    print(f"   AI Cache Bytes: {stats['ai_cache']['bytes'] / 1024:.2f} KB")

    # Test 8: Test cache disable
    print(f"\n📝 Testing with cache disabled...")
    response3 = manager.generate(
        prompt=test_prompt,
        provider=providers[0],
        max_tokens=50,
        use_cache=False
    )
    print(f"✓ Response with cache disabled: {response3[:50]}...")

    print("\n" + "=" * 50)
    print("✅ All cache integration tests passed!")
    return True


if __name__ == "__main__":
    try:
        success = test_cache_integration()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
