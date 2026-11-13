import logging
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from companion.core.features import FeatureService
from companion.core.models import Feature, WebSearchResult
from companion.core.ports import ChatTool, Clock, Repositories, WebSearch
from companion.core.timing import user_today

logger = logging.getLogger(__name__)

MAX_PAGE_CHARACTERS = 6_000
LIMIT_REACHED = "No more web searches today. Answer without searching."
SEARCH_FAILED = "The web search didn't work just now. Answer without it."
PAGE_FAILED = "The page couldn't be read. Answer without it."
MISSING_QUERY = "The web search needs a query."
MISSING_URL = "Reading a page needs a web address starting with http:// or https://."

SEARCH_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {"query": {"type": "string", "description": "What to search for."}},
    "required": ["query"],
}
FETCH_PARAMETERS: dict[str, Any] = {
    "type": "object",
    "properties": {"url": {"type": "string", "description": "The page's address."}},
    "required": ["url"],
}


@dataclass(frozen=True)
class WebSearchOffer:
    """The web tools a reply may use, and how the model should use them.

    Attributes:
        tools: The tools; empty when web search is off or used up for today.
        instructions: The reply instructions about using the web; the limit
            note once the Web Search Limit is reached; "" when Web Search
            doesn't work for the User.
    """

    tools: list[ChatTool]
    instructions: str


def format_search_results(
    query: str, results: list[WebSearchResult], source_reminder: str
) -> str:
    """Write web search results for the model, each with where it is from.

    Args:
        query: What was searched for.
        results: The results, best first.
        source_reminder: The Admin-set reminder to say where web information
            came from, put last.

    Returns:
        The results as text.
    """
    if not results:
        return f'No web results for "{query}".'
    listed = [
        f"{number}. {result.title}\n{result.url}\n{result.content}"
        for number, result in enumerate(results, start=1)
    ]
    return (
        f'Web results for "{query}":\n\n'
        + "\n\n".join(listed)
        + f"\n\n{source_reminder}"
    )


class WebSearchTools:
    """Offers web search and page reading to replies, within the daily limit."""

    def __init__(
        self,
        repositories: Repositories,
        features: FeatureService,
        web_search: WebSearch,
        clock: Clock,
    ) -> None:
        """Set up the web tools.

        Args:
            repositories: Where Users, usage and settings are stored.
            features: Says whether Web Search works for the User.
            web_search: Searches the web and reads pages.
            clock: Tells the current time, to know the User's day.
        """
        self._repositories = repositories
        self._features = features
        self._web_search = web_search
        self._clock = clock

    def offer(self, user_id: UUID) -> WebSearchOffer:
        """Pick the web tools for a reply to a User.

        None are offered when Web Search doesn't work for the User, or once
        they have made `web_search_daily_limit` searches on their own day.
        Reading a page counts as a web search too. At the limit the
        instructions are `reply_web_search_limit_note`, so the reply says it
        can't check instead of claiming it searched.

        Args:
            user_id: The User being replied to.

        Returns:
            The tools and their reply instructions.
        """
        settings = self._repositories.platform_settings
        usage = self._repositories.usage
        daily_limit = settings.get("web_search_daily_limit")
        today = user_today(self._repositories.users, user_id, self._clock.now())
        source_reminder = settings.get("web_result_source_reminder")
        used_today = usage.count_web_searches(user_id, today)
        if not self._features.works_for(user_id, Feature.WEB_SEARCH):
            return WebSearchOffer(tools=[], instructions="")
        if used_today >= daily_limit:
            return WebSearchOffer(
                tools=[], instructions=settings.get("reply_web_search_limit_note")
            )

        def run_search(arguments: dict[str, Any]) -> str:
            """Search the web for the model, if a search is left today.

            Args:
                arguments: The model's arguments, with the "query".

            Returns:
                The results, or why there are none.
            """
            query = str(arguments.get("query", "")).strip()
            if not query:
                return MISSING_QUERY
            if not usage.claim_web_search(user_id, today, daily_limit):
                return LIMIT_REACHED
            try:
                return format_search_results(
                    query, self._web_search.search(query), source_reminder
                )
            except Exception:
                logger.exception("Web search failed")
                return SEARCH_FAILED

        def run_fetch(arguments: dict[str, Any]) -> str:
            """Read a web page for the model, if a search is left today.

            Args:
                arguments: The model's arguments, with the "url".

            Returns:
                The page's text with its address, or why it can't be read.
            """
            url = str(arguments.get("url", "")).strip()
            if not url.startswith(("http://", "https://")):
                return MISSING_URL
            if not usage.claim_web_search(user_id, today, daily_limit):
                return LIMIT_REACHED
            try:
                text = self._web_search.fetch_page(url)
            except Exception:
                logger.exception("Reading a web page failed")
                return PAGE_FAILED
            if not text.strip():
                return PAGE_FAILED
            return f"Page {url}:\n\n{text[:MAX_PAGE_CHARACTERS]}\n\n{source_reminder}"

        return WebSearchOffer(
            tools=[
                ChatTool(
                    name="web_search",
                    description=settings.get("web_search_tool_description"),
                    parameters=SEARCH_PARAMETERS,
                    run=run_search,
                ),
                ChatTool(
                    name="fetch_page",
                    description=settings.get("page_fetch_tool_description"),
                    parameters=FETCH_PARAMETERS,
                    run=run_fetch,
                ),
            ],
            instructions=settings.get("reply_web_search_instructions"),
        )
