"""
Connection Pool Manager for AIZEN
==================================
Manages shared HTTP sessions and AI client instances.
Prevents creating new connections for every request.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

import aiohttp

logger = logging.getLogger(__name__)


class ConnectionPool:
    """
    Manages shared HTTP sessions and connection pools.
    Ensures efficient reuse of connections across requests.
    """

    _instance: Optional["ConnectionPool"] = None
    _lock = asyncio.Lock()

    def __init__(self):
        self._http_session: aiohttp.ClientSession | None = None
        self._ollama_session: aiohttp.ClientSession | None = None
        self._initialized = False

        # Connection pool settings
        self._connector_settings = {
            "limit": 100,  # Max simultaneous connections
            "limit_per_host": 30,  # Max connections per host
            "ttl_dns_cache": 300,  # DNS cache TTL
            "enable_cleanup_closed": True,
        }

        # Timeout settings
        self._timeout = aiohttp.ClientTimeout(total=60, connect=10, sock_read=30)

    @classmethod
    async def get_instance(cls) -> "ConnectionPool":
        """Get or create singleton instance"""
        if cls._instance is None:
            async with cls._lock:
                if cls._instance is None:
                    cls._instance = ConnectionPool()
                    await cls._instance.initialize()
        return cls._instance

    async def initialize(self):
        """Initialize connection pools"""
        if self._initialized:
            return

        # Create shared connector
        connector = aiohttp.TCPConnector(**self._connector_settings)

        # Create shared HTTP session
        self._http_session = aiohttp.ClientSession(
            connector=connector, timeout=self._timeout, headers={"User-Agent": "AIZEN/1.0"}
        )

        # Create separate session for Ollama (different timeout needs)
        ollama_connector = aiohttp.TCPConnector(limit=20, limit_per_host=10)
        self._ollama_session = aiohttp.ClientSession(
            connector=ollama_connector, timeout=aiohttp.ClientTimeout(total=120, connect=5)
        )

        self._initialized = True
        logger.info("Connection pools initialized")

    @property
    def http_session(self) -> aiohttp.ClientSession:
        """Get shared HTTP session"""
        if not self._http_session:
            raise RuntimeError("Connection pool not initialized")
        return self._http_session

    @property
    def ollama_session(self) -> aiohttp.ClientSession:
        """Get Ollama-specific session"""
        if not self._ollama_session:
            raise RuntimeError("Connection pool not initialized")
        return self._ollama_session

    async def close(self):
        """Close all sessions"""
        if self._http_session:
            await self._http_session.close()
            self._http_session = None

        if self._ollama_session:
            await self._ollama_session.close()
            self._ollama_session = None

        self._initialized = False
        logger.info("Connection pools closed")

    def get_stats(self) -> dict[str, Any]:
        """Get connection pool statistics"""
        stats = {"initialized": self._initialized}

        if self._http_session and not self._http_session.closed:
            connector = self._http_session.connector
            if isinstance(connector, aiohttp.TCPConnector):
                stats["http_pool"] = {
                    "limit": connector.limit,
                    "limit_per_host": connector.limit_per_host,
                }

        return stats


# Global accessor
async def get_connection_pool() -> ConnectionPool:
    """Get the shared connection pool"""
    return await ConnectionPool.get_instance()


@asynccontextmanager
async def get_http_session():
    """Context manager for getting HTTP session"""
    pool = await get_connection_pool()
    yield pool.http_session


async def close_connection_pool():
    """Close the global connection pool"""
    if ConnectionPool._instance:
        await ConnectionPool._instance.close()
        ConnectionPool._instance = None
