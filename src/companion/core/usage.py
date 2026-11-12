from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from companion.core.models import ChatLine, DailyUsage
from companion.core.ports import ChatModel, ChatTool, Clock, Repositories
from companion.core.timing import users_today


@dataclass(frozen=True)
class UsageReport:
    """Every User's usage over a period, with the limits in force now.

    Attributes:
        rows: One entry per User per day, newest day first.
        daily_message_limit: The daily message limit.
        web_search_daily_limit: The daily web search limit.
    """

    rows: list[DailyUsage]
    daily_message_limit: int
    web_search_daily_limit: int


class UsageLimiter:
    """Keeps each User within the daily message limit and records their usage.

    Usage is counted on the User's own day, so it starts again at midnight in
    their time zone.
    """

    def __init__(self, repositories: Repositories, clock: Clock) -> None:
        """Set up the limiter.

        Args:
            repositories: Where Users, usage and settings are stored.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._clock = clock

    def claim_message(self, user_id: UUID) -> bool:
        """Count one message toward the User's daily message limit.

        Args:
            user_id: The User who sent it.

        Returns:
            True if it was counted and may be answered; False if the User has
            already reached `daily_message_limit` today.
        """
        daily_limit = self._repositories.platform_settings.get("daily_message_limit")
        return self._repositories.usage.claim_message(
            user_id, self._users_day(user_id), daily_limit
        )

    def limit_reply(self) -> str:
        """Read the in-character reply sent once the daily limit is reached.

        Returns:
            The Admin-set wording.
        """
        reply: str = self._repositories.platform_settings.get("daily_limit_reply")
        return reply

    def record_tokens(self, user_id: UUID, tokens_in: int, tokens_out: int) -> None:
        """Add chat model tokens to the User's day.

        Args:
            user_id: The User the model call was for.
            tokens_in: Tokens the model read.
            tokens_out: Tokens the model wrote.
        """
        self._repositories.usage.add_tokens(
            user_id, self._users_day(user_id), tokens_in, tokens_out
        )

    def report(self, days: int) -> UsageReport:
        """List every User's usage over the last few days.

        Args:
            days: How many days to list, today included (in UTC).

        Returns:
            The usage and the limits in force now.
        """
        settings = self._repositories.platform_settings
        first_day = self._clock.now().date() - timedelta(days=days - 1)
        return UsageReport(
            rows=self._repositories.usage.list_since(first_day),
            daily_message_limit=settings.get("daily_message_limit"),
            web_search_daily_limit=settings.get("web_search_daily_limit"),
        )

    def _users_day(self, user_id: UUID) -> date:
        """Work out today's date where the User lives.

        Args:
            user_id: The User.

        Returns:
            Today's date in their time zone, or in UTC if they have none.
        """
        user = self._repositories.users.get(user_id)
        return users_today(user.time_zone if user else None, self._clock.now())


class UsageRecordingChatModel:
    """Asks the chat model for a User and adds the tokens to their usage."""

    def __init__(self, chat_model: ChatModel, usage_limiter: UsageLimiter) -> None:
        """Set up the wrapper.

        Args:
            chat_model: Generates the answers.
            usage_limiter: Records the tokens each answer took.
        """
        self._chat_model = chat_model
        self._usage_limiter = usage_limiter

    def generate(
        self,
        user_id: UUID,
        model: str,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> str:
        """Generate an answer for a User and record the tokens it took.

        Args:
            user_id: The User the answer is for.
            model: The model to use, e.g. "deepseek-chat".
            instructions: What the model should be and do.
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.

        Returns:
            The answer text.
        """
        answer = self._chat_model.generate(
            model=model, instructions=instructions, history=history, tools=tools
        )
        self._usage_limiter.record_tokens(user_id, answer.tokens_in, answer.tokens_out)
        return answer.text
