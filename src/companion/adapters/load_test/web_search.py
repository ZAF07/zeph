import logging

from companion.core.models import WebSearchResult

logger = logging.getLogger(__name__)


class EmptyWebSearch:
    """Web search for load tests: finds nothing and makes no network call."""

    def search(self, query: str) -> list[WebSearchResult]:
        """Log the search and find nothing.

        Args:
            query: What to search for; not logged.

        Returns:
            No results.
        """
        logger.info("Load test: searched the web")
        return []

    def fetch_page(self, url: str) -> str:
        """Log the read and give no text.

        Args:
            url: The page's address; not logged.

        Returns:
            "", as for a page that could not be read.
        """
        logger.info("Load test: read a web page")
        return ""
