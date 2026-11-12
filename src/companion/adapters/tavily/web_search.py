from typing import Any

import httpx

from companion.core.models import WebSearchResult

TAVILY_API_URL = "https://api.tavily.com"
MAX_RESULTS = 5


class TavilyWebSearch:
    """Searches the web and reads pages through the Tavily API."""

    def __init__(self, api_key: str, http_client: httpx.Client | None = None) -> None:
        """Set up the adapter.

        Args:
            api_key: The Tavily API key.
            http_client: The HTTP client to use; a new one is made if not given.
        """
        self._api_key = api_key
        self._http = http_client or httpx.Client(timeout=20)

    def search(self, query: str) -> list[WebSearchResult]:
        """Search the web.

        Args:
            query: What to search for.

        Returns:
            The best results, best first.
        """
        body = self._post("search", {"query": query, "max_results": MAX_RESULTS})
        return [
            WebSearchResult(
                title=str(result.get("title") or ""),
                url=str(result["url"]),
                content=str(result.get("content") or ""),
            )
            for result in body.get("results", [])
        ]

    def fetch_page(self, url: str) -> str:
        """Read the text of a web page.

        Args:
            url: The page's address.

        Returns:
            The page's text, or "" if Tavily could not read it.
        """
        body = self._post("extract", {"urls": [url]})
        results = body.get("results", [])
        return str(results[0].get("raw_content") or "") if results else ""

    def _post(self, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Call one Tavily endpoint.

        Args:
            endpoint: The endpoint, e.g. "search".
            payload: The request body.

        Returns:
            The response body.

        Raises:
            httpx.HTTPStatusError: If Tavily answers with an error.
        """
        response = self._http.post(
            f"{TAVILY_API_URL}/{endpoint}",
            json=payload,
            headers={"Authorization": f"Bearer {self._api_key}"},
        )
        response.raise_for_status()
        body: dict[str, Any] = response.json()
        return body
