"""
Test Suite for AIZEN Enhanced Features
=======================================
Tests the new infrastructure components.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


async def test_cache():
    """Test caching layer"""
    print("\n=== Testing Cache ===")
    from app.core.cache import get_all_cache_stats, get_embedding_cache

    cache = get_embedding_cache()

    # Test set and get
    cache.set("test_key", [1.0, 2.0, 3.0])
    hit, value = cache.get("test_key")

    assert hit, "Cache should hit"
    assert value == [1.0, 2.0, 3.0], "Value should match"

    # Test miss
    hit, value = cache.get("nonexistent")
    assert not hit, "Should be cache miss"

    stats = get_all_cache_stats()
    print(f"Cache stats: {stats}")
    print("[PASS] Cache tests passed")


async def test_connection_pool():
    """Test connection pool"""
    print("\n=== Testing Connection Pool ===")
    from app.core.connection_pool import get_connection_pool

    pool = await get_connection_pool()
    assert pool._initialized, "Pool should be initialized"

    session = pool.http_session
    assert session is not None, "Should have HTTP session"
    assert not session.closed, "Session should be open"

    stats = pool.get_stats()
    print(f"Connection pool stats: {stats}")
    print("[PASS] Connection pool tests passed")


async def test_metrics():
    """Test metrics collection"""
    print("\n=== Testing Metrics ===")
    from app.core.metrics import Metrics, get_metrics

    metrics = get_metrics()

    # Test counter
    metrics.increment(Metrics.REQUESTS_TOTAL)
    metrics.increment(Metrics.REQUESTS_TOTAL)
    assert metrics.get_counter(Metrics.REQUESTS_TOTAL) == 2

    # Test gauge
    metrics.set_gauge("test_gauge", 42.5)

    # Test histogram
    metrics.observe(Metrics.LLM_LATENCY, 0.5)
    metrics.observe(Metrics.LLM_LATENCY, 1.0)
    stats = metrics.get_histogram_stats(Metrics.LLM_LATENCY)
    assert stats["count"] == 2

    all_metrics = metrics.get_all_metrics()
    print(f"Metrics: {all_metrics}")

    prometheus = metrics.to_prometheus_format()
    print(f"Prometheus format:\n{prometheus[:500]}...")
    print("[PASS] Metrics tests passed")


async def test_audit_logger():
    """Test audit logging"""
    print("\n=== Testing Audit Logger ===")
    from app.core.audit_logger import EventType, get_audit_logger

    logger = await get_audit_logger()

    # Log an event
    event_id = await logger.log(
        EventType.USER_MESSAGE, "Test message", user_id="test_user", metadata={"test": True}
    )

    assert event_id is not None
    print(f"Logged event: {event_id}")

    # Query events
    events = await logger.get_events(limit=5)
    assert len(events) > 0
    print(f"Found {len(events)} events")

    # Get stats
    stats = await logger.get_stats()
    print(f"Audit stats: {stats}")
    print("[PASS] Audit logger tests passed")


async def test_reranker():
    """Test reranker"""
    print("\n=== Testing Reranker ===")
    from app.memory.reranker import get_reranker

    reranker = get_reranker()

    documents = [
        {"content": "Python is a programming language"},
        {"content": "The weather today is sunny"},
        {"content": "Python code examples for beginners"},
    ]

    # Test reranking (will use LLM if available, otherwise return as-is)
    reranked = await reranker.rerank("How to write Python code", documents, top_k=2)

    print(f"Reranked {len(documents)} docs to {len(reranked)}")
    for doc in reranked:
        print(f"  - Score: {doc.get('rerank_score', 'N/A')}: {doc['content'][:50]}")

    print("[PASS] Reranker tests passed")


async def test_history_manager():
    """Test history manager"""
    print("\n=== Testing History Manager ===")
    from app.memory.history_manager import SlidingWindowHistory, get_history_manager

    manager = get_history_manager()

    # Test token estimation
    messages = [
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing great, thanks for asking!"},
    ]

    tokens = manager.estimate_tokens(messages)
    print(f"Estimated tokens: {tokens}")

    # Test sliding window
    window = SlidingWindowHistory(max_messages=5, max_tokens=1000)
    window.add_message("user", "First message")
    window.add_message("assistant", "First response")
    window.add_message("user", "Second message")

    messages = window.get_messages()
    assert len(messages) == 3
    print(f"Sliding window has {len(messages)} messages")

    print("[PASS] History manager tests passed")


async def test_rate_limiter():
    """Test rate limiter"""
    print("\n=== Testing Rate Limiter ===")
    from app.core.rate_limiter import RateLimiter, TokenBucket

    # Test token bucket
    bucket = TokenBucket(tokens_per_second=10.0, bucket_size=5)

    # Should allow 5 requests immediately
    for i in range(5):
        assert bucket.consume(), f"Request {i + 1} should be allowed"

    # 6th request should fail
    assert not bucket.consume(), "6th request should be rate limited"

    # Test wait time
    wait = bucket.get_wait_time()
    assert wait > 0, "Should have wait time"
    print(f"Wait time after burst: {wait:.2f}s")

    # Test rate limiter stats
    limiter = RateLimiter()
    stats = limiter.get_stats()
    print(f"Rate limiter stats: {stats}")

    print("[PASS] Rate limiter tests passed")


async def test_backup_manager():
    """Test backup manager"""
    print("\n=== Testing Backup Manager ===")
    from app.core.backup import get_backup_manager

    manager = get_backup_manager()

    # List existing backups
    backups = await manager.list_backups()
    print(f"Existing backups: {len(backups)}")

    # Note: We don't actually create a backup in tests to avoid slow operations
    print("[PASS] Backup manager tests passed (listing only)")


async def main():
    """Run all tests"""
    print("=" * 60)
    print("AIZEN Enhanced Features Test Suite")
    print("=" * 60)

    try:
        await test_cache()
        await test_connection_pool()
        await test_metrics()
        await test_audit_logger()
        await test_reranker()
        await test_history_manager()
        await test_rate_limiter()
        await test_backup_manager()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)

    finally:
        # Cleanup connection pool
        from app.core.connection_pool import close_connection_pool

        await close_connection_pool()


if __name__ == "__main__":
    asyncio.run(main())
