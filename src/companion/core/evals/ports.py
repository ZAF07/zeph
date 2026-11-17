from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any, Protocol
from uuid import UUID

from companion.core.evals.models import (
    CaseHistoryRow,
    CaseResult,
    EvalCase,
    EvalImage,
    EvalName,
    EvalRun,
    EvalRunOverview,
    EvalRunState,
    ModelTokens,
    Replies,
    RunSnapshot,
    StartedFrom,
    StoredEvalCase,
    Variant,
)
from companion.core.models import ModelCall, Need
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

    def tokens_by_model(self) -> dict[str, ModelTokens]:
        """Add up the same tokens by the model that used them.

        Returns:
            Each model's tokens, the app's and the Judge's.
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
        """Send one of the case's test images from the User as a photo.

        Args:
            image_name: The test image's name.
            caption: The photo's caption; "" for none.

        Returns:
            What the Companion sent back.

        Raises:
            EvalSetupError: If the case has no image by that name.
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

    def keep_move_outcomes(self, conversation_id: UUID) -> None:
        """Run the Conversation-end Move Outcome keeping step on a Conversation.

        It runs as it does after the quiet gap, in its own Conversation-end
        trace, with the Eval database's Platform Settings.

        Args:
            conversation_id: The made-up User's finished Conversation.

        Raises:
            EvalSetupError: If no User is connected, or User Memory doesn't
                work for them.
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

    def fresh_companion(
        self,
        platform_settings: dict[str, Any],
        needs: Sequence[Need],
        images: Sequence[EvalImage],
    ) -> EvalCompanion:
        """Empty the Eval database, seed it and build the app on it.

        Args:
            platform_settings: The Platform Settings to write into it, by
                key; settings missing here come from the seed.
            needs: The Needs to write into it; the seed's when empty.
            images: The test images the case sends, by name.

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

    def list_for_keys(self, keys: Sequence[str]) -> list[EvalCase]:
        """List the cases with some keys that aren't archived.

        Args:
            keys: The keys.

        Returns:
            The cases found, in the order of `keys`.
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

    def list_stored(self, eval_name: EvalName) -> list[StoredEvalCase]:
        """List every case of one Eval, archived ones too.

        Args:
            eval_name: The Eval.

        Returns:
            The cases, in the order added.
        """
        ...

    def get(self, key: str) -> StoredEvalCase | None:
        """Read one case, archived or not.

        Args:
            key: Its key.

        Returns:
            The case; None if no case has the key.
        """
        ...

    def add(self, case: EvalCase, now: datetime, admin_id: UUID) -> bool:
        """Add a case an Admin wrote.

        Args:
            case: The case.
            now: When it is added.
            admin_id: The Admin adding it.

        Returns:
            True if added; False if its key is taken.
        """
        ...

    def update(
        self,
        key: str,
        content: dict[str, Any],
        *,
        archived: bool,
        now: datetime,
        admin_id: UUID,
    ) -> None:
        """Change a case and mark it edited, so the seed leaves it alone.

        Args:
            key: Its key.
            content: Its new content.
            archived: Whether it is archived.
            now: When it changed.
            admin_id: The Admin changing it.
        """
        ...


class EvalImageRepository(Protocol):
    """Stores the test images cases send, kept with the cases."""

    def add_missing(self, images: Sequence[EvalImage], now: datetime) -> None:
        """Add the images whose name isn't stored yet; never change one.

        Args:
            images: The images.
            now: When they are added.
        """
        ...

    def get_many(self, names: Sequence[str]) -> list[EvalImage]:
        """Read some images.

        Args:
            names: Their names.

        Returns:
            The ones stored, in no particular order.
        """
        ...


class JudgeSettingsRepository(Protocol):
    """Stores the Judge's settings, set by Admins."""

    def load(self) -> dict[str, Any]:
        """Read every Judge setting.

        Returns:
            Each setting's value by name.
        """
        ...

    def add_missing(self, values: Mapping[str, Any], now: datetime) -> None:
        """Add the settings not stored yet; never change one.

        Args:
            values: Each setting's starting value by name.
            now: When they are added.
        """
        ...

    def save(self, values: Mapping[str, Any], now: datetime, admin_id: UUID) -> None:
        """Save new values for some settings.

        Args:
            values: Each setting's new value by name.
            now: When they changed.
            admin_id: The Admin changing them.
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
        case_keys: Sequence[str],
        queued_at: datetime,
        variants: Sequence[Variant],
        repeats: int,
        rerun_of: UUID | None = None,
    ) -> None:
        """Save a new run as Queued.

        Args:
            run_id: Its ID.
            started_by: The Admin starting it; None from the terminal.
            started_from: Where it is started.
            evals: The Evals of the cases it runs.
            case_keys: The keys of the cases it runs, in order.
            queued_at: When it is started.
            variants: Its Variants, each with its Setting Overrides.
            repeats: How many times each case runs per Variant.
            rerun_of: The run whose failed cases it runs again, if any.
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

    def get_result(self, run_id: UUID, result_id: UUID) -> CaseResult | None:
        """Read one Case Result of a run.

        Args:
            run_id: The run.
            result_id: The result.

        Returns:
            The result; None if the run has no such result.
        """
        ...

    def list_result_calls(self, result_id: UUID) -> list[ModelCall]:
        """List a Case Result's model calls, its full trace.

        Args:
            result_id: The result.

        Returns:
            The calls, in the order they were made.
        """
        ...

    def newest_tokens_by_case(
        self, case_keys: Sequence[str]
    ) -> dict[str, dict[str, ModelTokens]]:
        """Read each case's tokens by model from its newest Case Result.

        Args:
            case_keys: The cases.

        Returns:
            Tokens by model for each case that has a result; cases never
            run are left out.
        """
        ...

    def list_case_history(self, case_key: str, limit: int) -> list[CaseHistoryRow]:
        """List a case's newest Case Results with what their runs used.

        Args:
            case_key: The case.
            limit: The most results to list.

        Returns:
            The results, newest first.
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

    def save_snapshot(
        self, run_id: UUID, snapshot: RunSnapshot, token_limit: int
    ) -> None:
        """Save what a run uses and the most tokens it may use.

        Args:
            run_id: The run.
            snapshot: The settings, Judge settings, cases and Needs.
            token_limit: The Eval run token limit when it started.
        """
        ...

    def add_result(self, result: CaseResult, calls: Sequence[ModelCall]) -> None:
        """Save one Case Result with its full trace.

        Args:
            result: The result.
            calls: The model calls the case made.
        """
        ...

    def is_cancel_requested(self, run_id: UUID) -> bool:
        """Say whether an Admin asked to cancel a run.

        Args:
            run_id: The run.

        Returns:
            True if they did.
        """
        ...

    def request_cancel(self, run_id: UUID, now: datetime) -> None:
        """Cancel a Queued run now, or ask the runner to cancel a Running one.

        Does nothing to a run that has ended.

        Args:
            run_id: The run.
            now: When it is cancelled.
        """
        ...

    def end(self, run_id: UUID, state: EvalRunState, now: datetime) -> None:
        """End a Running run as Finished, Cancelled or Stopped over limit.

        A run an Admin asked to cancel ends Cancelled rather than Finished,
        even if the cancel came after its last case.

        Args:
            run_id: The run.
            state: How it ended.
            now: When it ended.
        """
        ...

    def mark_made_live(
        self,
        run_id: UUID,
        letter: str,
        admin_id: UUID,
        now: datetime,
        applied_keys: Sequence[str],
        left_out_keys: Sequence[str],
    ) -> bool:
        """Record that an Admin made a Variant's Setting Overrides live.

        Only a Variant not made live yet is marked, in one step.

        Args:
            run_id: The run.
            letter: The Variant's letter.
            admin_id: The Admin.
            now: When.
            applied_keys: The overrides applied.
            left_out_keys: The overrides left out.

        Returns:
            True if it was marked; False if it was made live already.
        """
        ...

    def unmark_made_live(self, run_id: UUID, letter: str) -> None:
        """Take off a Variant's made-live mark, when its save was refused.

        Args:
            run_id: The run.
            letter: The Variant's letter.
        """
        ...

    def delete(self, run_id: UUID) -> None:
        """Delete a run with its Variants, Case Results and traces.

        Args:
            run_id: The run.
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
