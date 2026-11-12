import logging
from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID
from zoneinfo import ZoneInfo

from companion.core.models import WebSearchResult
from companion.core.ports import ChatTool, Clock, Repositories, WebSearch

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
        instructions: The reply instructions about using the web; "" when
            there are no tools.
    """

    tools: list[ChatTool]
    instructions: str


def format_search_results(query: str, results: list[WebSearchResult]) -> str:
    """Write web search results for the model, each with where it is from.

    Args:
        query: What was searched for.
        results: The results, best first.

    Returns:
        The results as text.
    """
    if not results:
        return f'No web results for "{query}".'
    listed = [
        f"{number}. {result.title}\n{result.url}\n{result.content}"
        for number, result in enumerate(results, start=1)
    ]
    return f'Web results for "{query}":\n\n' + "\n\n".join(listed)


class WebSearchTools:
    """Offers web search and page reading to replies, within the daily limit."""

    def __init__(
        self, repositories: Repositories, web_search: WebSearch, clock: Clock
    ) -> None:
        """Set up the web tools.

        Args:
            repositories: Where Users, usage and settings are stored.
            web_search: Searches the web and reads pages.
            clock: Tells the current time, to know the User's day.
        """
        self._repositories = repositories
        self._web_search = web_search
        self._clock = clock

    def offer(self, user_id: UUID) -> WebSearchOffer:
        """Pick the web tools for a reply to a User.

        None are offered when web search is turned off, or once the User has
        made `web_search_daily_limit` searches on their own day. Reading a
        page counts as a web search too.

        Args:
            user_id: The User being replied to.

        Returns:
            The tools and their reply instructions.
        """
        settings = self._repositories.platform_settings
        daily_limit = settings.get("web_search_daily_limit")
        used_today = self._repositories.usage.count_web_searches(
            user_id, self._users_day(user_id)
        )
        if not settings.get("web_search_enabled") or used_today >= daily_limit:
            return WebSearchOffer(tools=[], instructions="")

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
            if not self._claim_web_search(user_id):
                return LIMIT_REACHED
            try:
                return format_search_results(query, self._web_search.search(query))
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
            if not self._claim_web_search(user_id):
                return LIMIT_REACHED
            try:
                text = self._web_search.fetch_page(url)
            except Exception:
                logger.exception("Reading a web page failed")
                return PAGE_FAILED
            if not text.strip():
                return PAGE_FAILED
            return f"Page {url}:\n\n{text[:MAX_PAGE_CHARACTERS]}"

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

    def _claim_web_search(self, user_id: UUID) -> bool:
        """Count one web search for the User today, unless the limit is reached.

        Args:
            user_id: The User.

        Returns:
            True if the search may go ahead.
        """
        daily_limit = self._repositories.platform_settings.get("web_search_daily_limit")
        return self._repositories.usage.claim_web_search(
            user_id, self._users_day(user_id), daily_limit
        )

    def _users_day(self, user_id: UUID) -> date:
        """Work out today's date where the User lives.

        Args:
            user_id: The User.

        Returns:
            Today's date in their time zone, or in UTC if they have none.
        """
        user = self._repositories.users.get(user_id)
        time_zone = ZoneInfo(user.time_zone) if user and user.time_zone else None
        now = self._clock.now()
        return (now.astimezone(time_zone) if time_zone else now).date()
