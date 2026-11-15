from collections.abc import Sequence
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from companion.core.evals.models import (
    CaseResult,
    EvalCase,
    EvalName,
    EvalRun,
    EvalRunOverview,
    Replies,
    RunSnapshot,
    StartedFrom,
)
from companion.core.ports import ChatModel, Embedder, Repositories


class EvalSetupError(Exception):
    """Raised when an Eval couldn't set up what its case needs.

    The case then ends as an Error, not a Fail.
    """


class EvalCompanion(Protocol):
    """The whole app, built on the Eval database for one case.

    Messages go through the real Telegram webhook and reply path. Only the
    chat channel and web search are stand-ins, so nothing reaches a real
    chat and no search credits are spent. Methods raise `EvalSetupError`
    when the app refuses a step of the setup.
    """

    @property
    def repositories(self) -> Repositories:
        """The Eval database's repositories, to set up and read data."""
        ...

    @property
    def embedder(self) -> Embedder:
        """Embeds made-up memory the way the Companion does."""
        ...

    @property
    def judge_chat_model(self) -> ChatModel:
        """The chat model the Judge asks, counted with the app's tokens."""
        ...

    def tokens_used(self) -> tuple[int, int]:
        """Add up the tokens the LLM read and wrote since the case started.

        Returns:
            Tokens in and tokens out, the app's and the Judge's.
        """
        ...

    def called_tools(self) -> list[str]:
        """List the tools the reply model called since the case started.

        Returns:
            Their names, in order.
        """
        ...

    def clear_called_tools(self) -> None:
        """Forget the tools called so far."""
        ...

    def now(self) -> datetime:
        """Tell the app's time.

        Returns:
            The current time, as the app sees it.
        """
        ...

    def move_clock(self, by: timedelta) -> None:
        """Move the app's clock on, or back for a negative amount.

        Args:
            by: How far to move it.
        """
        ...

    def connect_user(
        self, check_ins: bool = False, onboarding_reasons: bool = True
    ) -> UUID:
        """Sign up the made-up User, onboard them and connect their Telegram.

        Args:
            check_ins: Whether they answer onboarding with Check-ins on
                "most days" in Singapore.
            onboarding_reasons: Whether that onboarding says what brings
                them here, which saves Memory Items.

        Returns:
            The User's ID.
        """
        ...

    def send_text(self, text: str) -> Replies:
        """Send a text from the User and wait for the reply.

        Args:
            text: What they send.

        Returns:
            What the Companion sent back.
        """
        ...

    def send_photo(self, image_name: str, caption: str) -> Replies:
        """Send a test image from the User as a photo and wait for the reply.

        Args:
            image_name: The test image's file name.
            caption: The photo's caption; "" for none.

        Returns:
            What the Companion sent back.
        """
        ...

    def memory_item_contents(self) -> list[str]:
        """List the contents of the User's Memory Items, as the Dashboard does.

        Returns:
            The contents, whatever their category.
        """
        ...

    def turn_photo_viewing_off(self) -> None:
        """Turn Photo Viewing off for the User."""
        ...

    def add_shared_photo(self, file_id: str, description: str, note: str) -> None:
        """Keep a Shared Photo for the User, as memory processing would.

        Args:
            file_id: The photo's file ID.
            description: What it shows.
            note: Why it matters to them.
        """
        ...

    def safeguard_risk_types(self) -> list[str]:
        """List the risk types of the Safeguard Events, newest first.

        Returns:
            One risk type per event.
        """
        ...

    def upload_starter_library(self) -> None:
        """Upload the starter Knowledge library as an Admin."""
        ...

    def upload_knowledge(
        self, file_name: str, content: bytes, title: str, source: str, tradition: str
    ) -> str:
        """Upload a Knowledge Document as an Admin.

        Args:
            file_name: The file's name.
            content: The file.
            title: Its title.
            source: Where it comes from.
            tradition: Its tradition.

        Returns:
            The document's ID.
        """
        ...

    def wait_until_knowledge_ready(self, document_id: str) -> None:
        """Wait until a Knowledge Document is Ready.

        Args:
            document_id: The document.

        Raises:
            EvalSetupError: If it failed or wasn't Ready in time.
        """
        ...

    def edit_knowledge_text(self, document_id: str, text: str) -> None:
        """Edit a Knowledge Document's text as an Admin.

        Args:
            document_id: The document.
            text: The new text.
        """
        ...

    def edit_knowledge_details(self, document_id: str, details: dict[str, str]) -> None:
        """Edit a Knowledge Document's details as an Admin.

        Args:
            document_id: The document.
            details: The details to change, e.g. `title` or `when_it_helps`.
        """
        ...

    def replace_knowledge_file(
        self, document_id: str, file_name: str, content: bytes
    ) -> None:
        """Replace a Knowledge Document's file as an Admin.

        Args:
            document_id: The document.
            file_name: The new file's name.
            content: The new file.
        """
        ...

    def close(self) -> None:
        """Stop the app."""
        ...


class EvalEnvironment(Protocol):
    """Prepares the Eval database and builds the app on it."""

    def start_run(self) -> None:
        """Wipe the Eval database and bring its schema up to date."""
        ...

    def fresh_companion(self, platform_settings: dict[str, Any]) -> EvalCompanion:
        """Empty the Eval database, seed it and build the app on it.

        Args:
            platform_settings: The Platform Settings to write into it, by
                key; settings missing here come from the seed.

        Returns:
            The app, ready for one case.
        """
        ...


class EvalCaseRepository(Protocol):
    """Stores the Eval Cases."""

    def list_for_evals(self, evals: Sequence[EvalName]) -> list[EvalCase]:
        """List the cases of some Evals that aren't archived.

        Args:
            evals: The Evals.

        Returns:
            The cases, by Eval in the order given, then in the order added.
        """
        ...

    def add_missing(self, cases: Sequence[EvalCase], now: datetime) -> list[str]:
        """Add the cases whose key isn't stored yet, archived or not.

        Args:
            cases: The cases.
            now: When they are added.

        Returns:
            The keys added.
        """
        ...


class EvalRunRepository(Protocol):
    """Stores Eval Runs and their Case Results."""

    def add(
        self,
        run_id: UUID,
        started_by: UUID | None,
        started_from: StartedFrom,
        evals: Sequence[EvalName],
        queued_at: datetime,
    ) -> None:
        """Save a new run as Queued, with one Variant (A) and one try.

        Args:
            run_id: Its ID.
            started_by: The Admin starting it; None from the terminal.
            started_from: Where it is started.
            evals: The Evals whose cases it runs.
            queued_at: When it is started.
        """
        ...

    def get(self, run_id: UUID) -> EvalRun | None:
        """Read a run.

        Args:
            run_id: Its ID.

        Returns:
            The run; None if there is no such run.
        """
        ...

    def list_overviews(self, include_terminal: bool) -> list[EvalRunOverview]:
        """List runs with their totals, newest first.

        Args:
            include_terminal: Whether to list runs started from the terminal.

        Returns:
            The runs.
        """
        ...

    def get_overview(self, run_id: UUID) -> EvalRunOverview | None:
        """Read one run with its totals.

        Args:
            run_id: Its ID.

        Returns:
            The run; None if there is no such run.
        """
        ...

    def list_results(self, run_id: UUID) -> list[CaseResult]:
        """List a run's Case Results in the order they finished.

        Args:
            run_id: The run.

        Returns:
            The results.
        """
        ...

    def take_next_queued(self, now: datetime) -> EvalRun | None:
        """Mark the oldest Queued run Running, if no run is Running.

        Args:
            now: When it starts.

        Returns:
            The run taken; None if none was.
        """
        ...

    def save_snapshot(self, run_id: UUID, snapshot: RunSnapshot) -> None:
        """Save what a run uses.

        Args:
            run_id: The run.
            snapshot: The settings, Judge settings and cases.
        """
        ...

    def add_result(self, result: CaseResult) -> None:
        """Save one Case Result.

        Args:
            result: The result.
        """
        ...

    def finish(self, run_id: UUID, now: datetime) -> None:
        """Mark a Running run Finished.

        Args:
            run_id: The run.
            now: When it finished.
        """
        ...

    def interrupt_running(self, now: datetime) -> list[UUID]:
        """Mark every Running run Interrupted.

        Args:
            now: When they were interrupted.

        Returns:
            The runs marked.
        """
        ...
