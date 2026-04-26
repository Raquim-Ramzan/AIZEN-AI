import logging
from typing import Any

import aiohttp

from app.tools.base import BaseTool

logger = logging.getLogger(__name__)


class WebSearchTool(BaseTool):
    """Web search using DuckDuckGo and Wikipedia"""

    def __init__(self):
        super().__init__()
        self.name = "web_search"
        self.description = "Search the web using DuckDuckGo or lookup information on Wikipedia"
        self.parameters = {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "source": {
                    "type": "string",
                    "enum": ["duckduckgo", "wikipedia"],
                    "description": "Search source",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 5,
                },
            },
            "required": ["query"],
        }

    async def execute(
        self, query: str, source: str = "duckduckgo", max_results: int = 5
    ) -> dict[str, Any]:
        """Execute web search"""
        try:
            if source == "wikipedia":
                return await self._search_wikipedia(query)
            else:
                return await self._search_duckduckgo(query, max_results)
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return {"error": str(e), "results": []}

    async def _search_duckduckgo(self, query: str, max_results: int) -> dict[str, Any]:
        """Search using DuckDuckGo Instant Answer API"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://api.duckduckgo.com/"
                params = {"q": query, "format": "json", "no_html": 1, "skip_disambig": 1}

                async with session.get(url, params=params) as resp:
                    data = await resp.json()

                    results = []

                    # Abstract
                    if data.get("Abstract"):
                        results.append(
                            {
                                "title": data.get("Heading", "Result"),
                                "snippet": data.get("Abstract"),
                                "url": data.get("AbstractURL", ""),
                            }
                        )

                    # Related topics
                    for topic in data.get("RelatedTopics", [])[:max_results]:
                        if "Text" in topic:
                            results.append(
                                {
                                    "title": topic.get("Text", "")[:50],
                                    "snippet": topic.get("Text", ""),
                                    "url": topic.get("FirstURL", ""),
                                }
                            )

                    return {
                        "query": query,
                        "source": "duckduckgo",
                        "results": results[:max_results],
                    }
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return {"error": str(e), "results": []}

    async def _search_wikipedia(self, query: str) -> dict[str, Any]:
        """Search Wikipedia"""
        try:
            async with aiohttp.ClientSession() as session:
                url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "exintro": True,
                    "explaintext": True,
                    "titles": query,
                }

                async with session.get(url, params=params) as resp:
                    data = await resp.json()
                    pages = data.get("query", {}).get("pages", {})

                    results = []
                    for page_id, page in pages.items():
                        if page_id != "-1":
                            results.append(
                                {
                                    "title": page.get("title", ""),
                                    "snippet": page.get("extract", "")[:500],
                                    "url": f"https://en.wikipedia.org/wiki/{page.get('title', '').replace(' ', '_')}",
                                }
                            )

                    return {"query": query, "source": "wikipedia", "results": results}
        except Exception as e:
            logger.error(f"Wikipedia search error: {e}")
            return {"error": str(e), "results": []}
