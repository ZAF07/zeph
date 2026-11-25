import logging
import time
from collections.abc import Callable, Sequence
from dataclasses import replace
from datetime import datetime, timedelta
from typing import Any

from companion.core.evals.cases import EvalWebResult
from companion.core.evals.models import ModelTokens
from companion.core.evals.ports import EvalSetupError
from companion.core.incoming_messages import MESSAGE_WAIT_PREFIX
from companion.core.models import (
    AccountIdentity,
    ChannelSticker,
    ChatLine,
    ModelAnswer,
    PhotoImage,
    StickerImage,
    WebSearchResult,
)
from companion.core.ports import ChatModel, ChatTool, PhotoViewer

logger = logging.getLogger(__name__)


class RecordingChatChannel:
    """Chat channel for Evals: records what Zeph sends and serves test images.

    Nothing reaches a real chat. A photo is downloaded from `photos`, set by
    the Eval before it sends the photo.
    """

    def __init__(self) -> None:
        """Start with nothing sent and no photos to serve."""
        self.sent_texts: list[str] = []
        self.sent_photo_file_ids: list[str] = []
        self.photos: dict[str, PhotoImage] = {}

    def send_text(
        self, chat_id: int, text: str, reply_to_message_id: int | None = None
    ) -> None:
        """Record a text.

        Args:
            chat_id: The chat it is for.
            text: The text.
            reply_to_message_id: The message it replies to; not recorded.
        """
        self.sent_texts.append(text)

    def show_typing(self, chat_id: int) -> None:
        """Do nothing; there is no chat to show typing in.

        Args:
            chat_id: The chat.
        """

    def send_sticker(self, chat_id: int, file_id: str) -> None:
        """Do nothing; no Eval checks stickers.

        Args:
            chat_id: The chat.
            file_id: The sticker's file ID.
        """

    def react(self, chat_id: int, message_id: int, emoji: str) -> None:
        """Do nothing; no Eval checks reactions.

        Args:
            chat_id: The chat.
            message_id: The message.
            emoji: The reaction.
        """

    def send_photo(self, chat_id: int, file_id: str) -> None:
        """Record a photo sent back by its file ID.

        Args:
            chat_id: The chat it is for.
            file_id: The photo's file ID.
        """
        self.sent_photo_file_ids.append(file_id)

    def get_sticker_set(self, name: str) -> list[ChannelSticker] | None:
        """Know no sticker sets.

        Args:
            name: The set's name.

        Returns:
            None.
        """
        return None

    def get_sticker_image(self, file_id: str) -> StickerImage | None:
        """Know no sticker images.

        Args:
            file_id: The image's file ID.

        Returns:
            None.
        """
        return None

    def download_photo(self, file_id: str) -> PhotoImage:
        """Serve the test image set for a file ID.

        Args:
            file_id: The photo's file ID.

        Returns:
            The image.

        Raises:
            KeyError: If no image was set for it.
        """
        return self.photos[file_id]


class CannedWebSearch:
    """Web search for Evals: finds only a case's made-up pages, for free.

    Every search finds every page set; with none set it finds nothing, so
    no search credits are ever spent.
    """

    def __init__(self) -> None:
        """Start with no pages to find."""
        self.pages: list[EvalWebResult] = []

    def search(self, query: str) -> list[WebSearchResult]:
        """Find every page set.

        Args:
            query: What to search for.

        Returns:
            Each page's title, address and text.
        """
        return [
            WebSearchResult(title=page.title, url=page.url, content=page.text)
            for page in self.pages
        ]

    def fetch_page(self, url: str) -> str:
        """Read a page set, by its address.

        Args:
            url: The page's address.

        Returns:
            Its text; "" when no page set has that address.
        """
        return next((page.text for page in self.pages if page.url == url), "")


class EvalAccounts:
    """Sign-in for Evals: accepts tokens it handed out, with no auth provider."""

    def __init__(self) -> None:
        """Start with no tokens."""
        self._identities_by_token: dict[str, AccountIdentity] = {}

    def token_for(self, auth_id: str, email: str) -> str:
        """Hand out a token that signs in as an account.

        Args:
            auth_id: The account's ID.
            email: Its email address.

        Returns:
            A bearer token.
        """
        token = f"eval-{auth_id}"
        self._identities_by_token[token] = AccountIdentity(auth_id=auth_id, email=email)
        return token

    def verify(self, token: str) -> AccountIdentity | None:
        """Look up a token's account.

        Args:
            token: The bearer token.

        Returns:
            The account; None for a token not handed out.
        """
        return self._identities_by_token.get(token)

    def delete_account(self, auth_id: str) -> None:
        """Forget an account's tokens.

        Args:
            auth_id: The account's ID.
        """
        self._identities_by_token = {
            token: identity
            for token, identity in self._identities_by_token.items()
            if identity.auth_id != auth_id
        }


class ManualTimer:
    """Timer for Evals: waiting work runs only when the Eval ends the wait."""

    def __init__(self) -> None:
        """Start with nothing waiting."""
        self._waiting: dict[str, Callable[[], None]] = {}

    def start(self, key: str, seconds: float, work: Callable[[], None]) -> None:
        """Keep the work, replacing any under the same key.

        Args:
            key: Names the wait.
            seconds: How long a real timer would wait.
            work: What to run when the wait ends.
        """
        self._waiting[key] = work

    def end_message_waits(self) -> None:
        """Run the waiting Message work now, as if the User had paused."""
        keys = [key for key in self._waiting if key.startswith(MESSAGE_WAIT_PREFIX)]
        for key in keys:
            self._waiting.pop(key)()


class InlineUserWorkQueue:
    """User work queue for Evals: runs work right away, on the caller's thread.

    An Eval sends one text at a time, so its texts are checked and answered
    in order before the Eval moves on. Work added under a key whose work is
    running waits until that work is done, so each key's work still runs one
    piece at a time, in order. A piece that fails is logged, and later work
    under its key still runs.
    """

    def __init__(self) -> None:
        """Start with nothing waiting."""
        self._waiting: dict[str, list[Callable[[], None]]] = {}

    def add(self, key: str, work: Callable[[], None]) -> None:
        """Run the work now, unless the key's work is running.

        Args:
            key: Names one line of a User's work.
            work: What to run.
        """
        line = self._waiting.get(key)
        if line is not None:
            line.append(work)
            return
        line = self._waiting[key] = [work]
        while line:
            try:
                line[0]()
            except Exception:
                logger.exception("A User's queued work failed")
            line.pop(0)
        del self._waiting[key]


class ManualScheduler:
    """Scheduler for Evals: never ticks on its own, so no Check-in runs unasked.

    An Eval that needs the scheduled work, e.g. to end a quiet Conversation,
    runs one tick by hand.
    """

    def __init__(self) -> None:
        """Start with no tick to run."""
        self._tick: Callable[[], None] | None = None

    def start(self, tick: Callable[[], None]) -> None:
        """Keep the scheduled work, without running it.

        Args:
            tick: The work a real scheduler would run.
        """
        self._tick = tick

    def stop(self) -> None:
        """Do nothing."""

    def run_tick(self) -> None:
        """Run the scheduled work once, as the real scheduler does every so often.

        Raises:
            EvalSetupError: If the app hasn't started the scheduler.
        """
        if self._tick is None:
            raise EvalSetupError("The app has not started the scheduler")
        self._tick()


class RunningClock:
    """Clock for Evals that moves with real time and can be moved on or back.

    Sleeping on it moves it on without waiting, so typing pauses don't slow
    an Eval down. Because it moves with real time, the Model Call Log
    records how long each model call really took.
    """

    def __init__(self, start: datetime) -> None:
        """Set the starting time.

        Args:
            start: The time the clock starts at.
        """
        self._start = start
        self._moved = timedelta()
        self._started = time.monotonic()

    def now(self) -> datetime:
        """Tell the time.

        Returns:
            The start, plus the real time passed, plus any moves.
        """
        passed = timedelta(seconds=time.monotonic() - self._started)
        return self._start + passed + self._moved

    def sleep(self, seconds: float) -> None:
        """Move the clock on without waiting.

        Args:
            seconds: How long the pause is.
        """
        self._moved += timedelta(seconds=seconds)

    def move(self, by: timedelta) -> None:
        """Move the clock on, or back for a negative amount.

        Args:
            by: How far to move it.
        """
        self._moved += by


class TokenCounter:
    """Adds up the tokens of every model answer in one Eval case, by model."""

    def __init__(self) -> None:
        """Start at zero."""
        self.tokens_in = 0
        self.tokens_out = 0
        self.by_model: dict[str, ModelTokens] = {}

    def add(self, model: str, answer: ModelAnswer) -> None:
        """Add an answer's tokens.

        Args:
            model: The model that gave it.
            answer: The model's answer.
        """
        self.tokens_in += answer.tokens_in
        self.tokens_out += answer.tokens_out
        self.by_model[model] = self.by_model.get(model, ModelTokens()).plus(
            ModelTokens(answer.tokens_in, answer.tokens_out)
        )


class CountingChatModel:
    """Chat model that counts tokens and notes the tools the model called."""

    def __init__(self, chat_model: ChatModel, counter: TokenCounter) -> None:
        """Wrap a chat model.

        Args:
            chat_model: The real chat model.
            counter: Where the tokens are added up.
        """
        self._chat_model = chat_model
        self._counter = counter
        self.called_tools: list[str] = []

    def generate(
        self,
        model: str,
        thinking: bool,
        instructions: str,
        history: list[ChatLine],
        tools: Sequence[ChatTool] = (),
        message_instructions: str = "",
    ) -> ModelAnswer:
        """Generate an answer with the real chat model and count its tokens.

        Args:
            model: The model to use.
            thinking: Whether the model should think before it answers.
            instructions: What the model should be and do.
            history: The conversation so far, oldest first.
            tools: The tools the model may call.
            message_instructions: The instructions made for this one call.

        Returns:
            The real chat model's answer.
        """
        recorded_tools = [self._recording(tool) for tool in tools]
        answer = self._chat_model.generate(
            model=model,
            thinking=thinking,
            instructions=instructions,
            history=history,
            tools=recorded_tools,
            message_instructions=message_instructions,
        )
        self._counter.add(model, answer)
        return answer

    def _recording(self, tool: ChatTool) -> ChatTool:
        """Wrap a tool so each call to it is noted in `called_tools`.

        Args:
            tool: The tool.

        Returns:
            The same tool, noting its name before it runs.
        """

        def run(arguments: dict[str, Any]) -> str:
            """Note the call, then run the tool.

            Args:
                arguments: The model's arguments.

            Returns:
                What the tool returns.
            """
            self.called_tools.append(tool.name)
            return tool.run(arguments)

        return replace(tool, run=run)


class CountingPhotoViewer:
    """Photo viewer that counts the tokens of every look."""

    def __init__(self, photo_viewer: PhotoViewer, counter: TokenCounter) -> None:
        """Wrap a photo viewer.

        Args:
            photo_viewer: The real photo viewer.
            counter: Where the tokens are added up.
        """
        self._photo_viewer = photo_viewer
        self._counter = counter

    def look(
        self, model: str, thinking: bool, instructions: str, photo: PhotoImage
    ) -> ModelAnswer:
        """Look at a photo with the real photo viewer and count its tokens.

        Args:
            model: The model to use.
            thinking: Whether the model should think before it answers.
            instructions: What to write about the photo.
            photo: The photo's image.

        Returns:
            The real photo viewer's answer.
        """
        answer = self._photo_viewer.look(model, thinking, instructions, photo)
        self._counter.add(model, answer)
        return answer
