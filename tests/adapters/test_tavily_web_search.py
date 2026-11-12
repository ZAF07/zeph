import json

import httpx
import pytest

from companion.adapters.tavily.web_search import TavilyWebSearch
from companion.core.models import WebSearchResult


def tavily_with(
    responses: dict[str, httpx.Response], requests: list[httpx.Request]
) -> TavilyWebSearch:
    def handle(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return responses[request.url.path]

    return TavilyWebSearch(
        "tvly-test", http_client=httpx.Client(transport=httpx.MockTransport(handle))
    )


def test_a_search_sends_the_query_and_returns_titles_addresses_and_snippets() -> None:
    requests: list[httpx.Request] = []
    tavily = tavily_with(
        {
            "/search": httpx.Response(
                200,
                json={
                    "results": [
                        {
                            "title": "Seneca - Wikipedia",
                            "url": "https://en.wikipedia.org/wiki/Seneca",
                            "content": "Seneca was a Stoic philosopher.",
                            "score": 0.9,
                        }
                    ]
                },
            )
        },
        requests,
    )

    results = tavily.search("Seneca")

    assert results == [
        WebSearchResult(
            title="Seneca - Wikipedia",
            url="https://en.wikipedia.org/wiki/Seneca",
            content="Seneca was a Stoic philosopher.",
        )
    ]
    [request] = requests
    assert request.headers["Authorization"] == "Bearer tvly-test"
    assert json.loads(request.content) == {"query": "Seneca", "max_results": 5}


def test_reading_a_page_returns_its_text_or_nothing_if_it_failed() -> None:
    requests: list[httpx.Request] = []
    tavily = tavily_with(
        {
            "/extract": httpx.Response(
                200,
                json={
                    "results": [{"url": "https://a.test", "raw_content": "Page text"}],
                    "failed_results": [],
                },
            )
        },
        requests,
    )
    failing = tavily_with(
        {
            "/extract": httpx.Response(
                200,
                json={"results": [], "failed_results": [{"url": "https://b.test"}]},
            )
        },
        [],
    )

    assert tavily.fetch_page("https://a.test") == "Page text"
    assert json.loads(requests[0].content) == {"urls": ["https://a.test"]}
    assert failing.fetch_page("https://b.test") == ""


def test_an_error_from_tavily_is_raised() -> None:
    tavily = tavily_with({"/search": httpx.Response(401)}, [])

    with pytest.raises(httpx.HTTPStatusError):
        tavily.search("Seneca")
