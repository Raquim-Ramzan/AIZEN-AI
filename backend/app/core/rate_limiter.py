"""
Rate Limiting for AIZEN API
============================
Implements token bucket rate limiting for API endpoints.
"""

import logging
import time
from typing import Dict, Optional
from collections import defaultdict
import threading
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TokenBucket:
    """
    Token bucket rate limiter.
    Allows burst of requests up to bucket size, then refills at steady rate.
    """
    
    def __init__(self, tokens_per_second: float, bucket_size: int):
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.tokens = bucket_size
        self.last_update = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens.
        Returns True if successful, False if rate limited.
        """
        with self.lock:
            now = time.time()
            
            # Refill tokens based on time elapsed
            elapsed = now - self.last_update
            self.tokens = min(
                self.bucket_size,
                self.tokens + elapsed * self.tokens_per_second
            )
            self.last_update = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            return False
    
    def get_wait_time(self) -> float:
        """Get time to wait until tokens available"""
        if self.tokens >= 1:
            return 0
        tokens_needed = 1 - self.tokens
        return tokens_needed / self.tokens_per_second


class RateLimiter:
    """
    Rate limiter that tracks limits per client/endpoint.
    """
    
    def __init__(self):
        # Default limits (requests per second, burst size)
        self.default_rps = 10.0
        self.default_burst = 20
        
        # Per-endpoint limits
        self.endpoint_limits = {
            "/api/chat": (5.0, 10),
            "/api/ws": (2.0, 5),  # WebSocket connection rate
            "/api/rag/rebuild": (0.1, 1),  # Expensive operation
        }
        
        # Client buckets: {client_key: {endpoint: TokenBucket}}
        self._buckets: Dict[str, Dict[str, TokenBucket]] = defaultdict(dict)
        self._lock = threading.Lock()
        
        # Global bucket for overall system protection
        self._global_bucket = TokenBucket(100.0, 200)
    
    def _get_client_key(self, request: Request) -> str:
        """Get unique client identifier"""
        # Use forwarded IP if behind proxy, else client host
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def _get_endpoint_key(self, path: str) -> str:
        """Normalize endpoint path"""
        # Strip trailing slashes and params for matching
        path = path.rstrip("/")
        
        # Check for specific endpoint patterns
        for endpoint in self.endpoint_limits:
            if path.startswith(endpoint):
                return endpoint
        
        return "default"
    
    def _get_bucket(self, client_key: str, endpoint_key: str) -> TokenBucket:
        """Get or create bucket for client/endpoint"""
        with self._lock:
            if endpoint_key not in self._buckets[client_key]:
                rps, burst = self.endpoint_limits.get(
                    endpoint_key,
                    (self.default_rps, self.default_burst)
                )
                self._buckets[client_key][endpoint_key] = TokenBucket(rps, burst)
            
            return self._buckets[client_key][endpoint_key]
    
    def is_allowed(self, request: Request) -> bool:
        """Check if request is allowed"""
        # Check global limit first
        if not self._global_bucket.consume():
            logger.warning("Global rate limit exceeded")
            return False
        
        # Check per-client limit
        client_key = self._get_client_key(request)
        endpoint_key = self._get_endpoint_key(request.url.path)
        bucket = self._get_bucket(client_key, endpoint_key)
        
        if not bucket.consume():
            logger.warning(f"Rate limit exceeded for client {client_key} on {endpoint_key}")
            return False
        
        return True
    
    def get_retry_after(self, request: Request) -> float:
        """Get seconds until request would be allowed"""
        client_key = self._get_client_key(request)
        endpoint_key = self._get_endpoint_key(request.url.path)
        bucket = self._get_bucket(client_key, endpoint_key)
        return bucket.get_wait_time()
    
    def get_stats(self) -> Dict[str, any]:
        """Get rate limiter statistics"""
        with self._lock:
            return {
                "total_clients": len(self._buckets),
                "global_tokens": self._global_bucket.tokens,
                "default_limits": {
                    "rps": self.default_rps,
                    "burst": self.default_burst
                },
                "endpoint_limits": self.endpoint_limits
            }


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.
    """
    
    def __init__(self, app, rate_limiter: RateLimiter = None):
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/", "/metrics"]:
            return await call_next(request)
        
        if not self.rate_limiter.is_allowed(request):
            retry_after = self.rate_limiter.get_retry_after(request)
            
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please slow down.",
                headers={"Retry-After": str(int(retry_after) + 1)}
            )
        
        response = await call_next(request)
        return response


# Singleton
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create rate limiter"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter
