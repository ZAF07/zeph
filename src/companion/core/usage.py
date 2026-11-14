from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import timedelta
from uuid import UUID

from companion.core.model_call_log import ModelCallLog, ModelCallRequest
from companion.core.models import (
    ChatLine,
    ChatRole,
    DailyUsage,
    ModelAnswer,
    ModelStep,
    PhotoImage,
    PlatformSettings,
    UserSnapshot,
)
from companion.core.platform_settings import (
    DAILY_LIMIT_REPLY,
    DAILY_MESSAGE_LIMIT,
    WEB_SEARCH_DAILY_LIMIT,
)
from companion.core.ports import ChatModel, ChatTool, Clock, PhotoViewer, Repositories
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

    def claim_message(self, snapshot: UserSnapshot) -> bool:
        """Count one message toward the User's daily message limit.

        Args:
            snapshot: The User who sent it, as read when the reply started.

        Returns:
            True if it was counted and may be answered; False if the User has
            already reached `daily_message_limit` today.
        """
        daily_limit = snapshot.settings.get(DAILY_MESSAGE_LIMIT)
        return self._repositories.usage.claim_message(
            snapshot.user.id, snapshot.today, daily_limit
        )

    def users_who_used_up_daily_message_limit(
        self, snapshots: Sequence[UserSnapshot]
    ) -> set[UUID]:
        """Find which Users have used up today's daily message limit, in one query.

        It is used up once their message count for their day has reached the
        limit, even if no message was turned away yet.

        Args:
            snapshots: The Users, as read when the tick started.

        Returns:
            The IDs of those whose next message today would get the limit
            reply.
        """
        daily_limits = {
            snapshot.user.id: snapshot.settings.get(DAILY_MESSAGE_LIMIT)
            for snapshot in snapshots
        }
        counts = self._repositories.usage.count_messages_on_days(
            {snapshot.user.id: snapshot.today for snapshot in snapshots}
        )
        return {
            user_id
            for user_id, count in counts.items()
            if count >= daily_limits[user_id]
        }

    def limit_reply(self, settings: PlatformSettings) -> str:
        """Read the in-character reply sent once the daily limit is reached.

        Args:
            settings: The platform settings, read once for the reply.

        Returns:
            The Admin-set wording.
        """
        return settings.get(DAILY_LIMIT_REPLY)

    def record_tokens(
        self, snapshot: UserSnapshot, tokens_in: int, tokens_out: int
    ) -> None:
        """Add chat model tokens to the User's day.

        Args:
            snapshot: The User the model call was for.
            tokens_in: Tokens the model read.
            tokens_out: Tokens the model wrote.
        """
        self._repositories.usage.add_tokens(
            snapshot.user.id, snapshot.today, tokens_in, tokens_out
        )

    def report(self, days: int) -> UsageReport:
        """List every User's usage over the last few days.

        Each User's days are their own, so "today" is today where they live.

        Args:
            days: How many days to list, today included.

        Returns:
            The usage and the limits in force now.
        """
        settings = self._repositories.platform_settings.load()
        now = self._clock.now()
        earliest_possible_day = now.date() - timedelta(days=days)
        rows = [
            row
            for row in self._repositories.usage.list_since(earliest_possible_day)
            if row.day > users_today(row.user_time_zone, now) - timedelta(days=days)
        ]
        return UsageReport(
            rows=rows,
            daily_message_limit=settings.get(DAILY_MESSAGE_LIMIT),
            web_search_daily_limit=settings.get(WEB_SEARCH_DAILY_LIMIT),
        )


class UsageRecordingChatModel:
    """Asks the chat model or photo viewer for a User, recording each call.

    The tokens are added to the User's usage, and every call goes into the
    Model Call Log, failed ones included, so no service has to log itself.
    """

    def __init__(
        self,
        chat_model: ChatModel,
        photo_viewer: PhotoViewer,
        usage_limiter: UsageLimiter,
        model_call_log: ModelCallLog,
        clock: Clock,
    ) -> None:
        """Set up the wrapper.

        Args:
            chat_model: Generates the answers.
            photo_viewer: Looks at photos.
            usage_limiter: Records the tokens each answer took.
            model_call_log: Records each call.
            clock: Tells when each call starts.
        """
        self._chat_model = chat_model
        self._photo_viewer = photo_viewer
        self._usage_limiter = usage_limiter
        self._model_call_log = model_call_log
        self._clock = clock

    def generate(
        self,
        snapshot: UserSnapshot,
        step: ModelStep,
        model: str,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
    ) -> str:
        """Generate an answer for a User and record the call.

        Args:
            snapshot: The User the answer is for.
            step: Which step the answer is for.
            model: The model to use, e.g. "deepseek-chat".
            instructions: What the model should be and do.
            history: The Conversation so far, oldest first.
            tools: The tools the model may call; none by default.

        Returns:
            The answer text.

        Raises:
            Exception: Whatever the chat model raises, once it is recorded.
        """
        request = ModelCallRequest(step, model, instructions, tuple(history), tools)
        return self._ask_and_record(
            snapshot,
            request,
            lambda: self._chat_model.generate(
                model=model, instructions=instructions, history=history, tools=tools
            ),
        )

    def look(
        self, snapshot: UserSnapshot, model: str, instructions: str, photo: PhotoImage
    ) -> str:
        """Look at a photo for a User and record the call.

        The Model Call Log keeps the instructions and the answer, never the
        image.

        Args:
            snapshot: The User who sent the photo.
            model: The model to use, e.g. "deepseek-chat".
            instructions: What to write about the photo.
            photo: The photo's image.

        Returns:
            The text.

        Raises:
            Exception: Whatever the photo viewer raises, once it is recorded.
        """
        request = ModelCallRequest(
            step=ModelStep.PHOTO,
            model=model,
            instructions=instructions,
            history=(ChatLine(role=ChatRole.USER, text="[photo]"),),
            tools=(),
        )
        return self._ask_and_record(
            snapshot,
            request,
            lambda: self._photo_viewer.look(
                model=model, instructions=instructions, photo=photo
            ),
        )

    def _ask_and_record(
        self,
        snapshot: UserSnapshot,
        request: ModelCallRequest,
        ask: Callable[[], ModelAnswer],
    ) -> str:
        """Ask the model, then record the call, failed or not, and its tokens.

        Args:
            snapshot: The User the call is for.
            request: What the model is asked.
            ask: Makes the call.

        Returns:
            The answer text.

        Raises:
            Exception: Whatever the call raises, once it is recorded.
        """
        started_at = self._clock.now()
        try:
            answer = ask()
        except Exception as error:
            self._model_call_log.record(snapshot, request, started_at, error)
            raise
        self._usage_limiter.record_tokens(snapshot, answer.tokens_in, answer.tokens_out)
        self._model_call_log.record(snapshot, request, started_at, answer)
        return answer.text
