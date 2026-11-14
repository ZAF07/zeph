import json
import logging
from collections.abc import Sequence
from dataclasses import asdict
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from companion.core.errors import NotFoundError
from companion.core.models import (
    ChatLine,
    ModelAnswer,
    ModelCall,
    ModelCallContent,
    ModelCallTrace,
    ModelCallTraceDetails,
    ModelCallTraceOverview,
    ModelStep,
    OfferedTool,
    TraceKind,
    UserRole,
    UserSnapshot,
)
from companion.core.ports import ChatTool, Clock, Repositories

logger = logging.getLogger(__name__)

TRACES_LISTED_AT_MOST = 200


def start_trace(kind: TraceKind) -> ModelCallTrace:
    """Start a new Model Call Log trace.

    Args:
        kind: What the trace is for.

    Returns:
        The trace, with a new ID.
    """
    return ModelCallTrace(id=uuid4(), kind=kind)


class ModelCallTraceNotFoundError(NotFoundError):
    """Raised when no Model Call Log trace has the given ID."""

    shown_message = "No such trace"


class ModelCallLog:
    """Records every model call in the Model Call Log, at the right level (ADR-0010).

    Every call keeps its step, model, tokens, time taken, error and the tools
    it called. What the model was given and answered is kept only when the
    User is an Admin, or when every call keeps it (an Eval run). Developer
    logs, when on, get the full content of every call instead.
    """

    def __init__(
        self,
        repositories: Repositories,
        clock: Clock,
        content_for_everyone: bool,
        developer_logs: bool,
    ) -> None:
        """Set up the log.

        Args:
            repositories: Where the log and Users are stored.
            clock: Tells the current time.
            content_for_everyone: Whether every call keeps full content, as in
                an Eval run.
            developer_logs: Whether to write every call's full content to the
                developer logs, as in local and worktree runs.
        """
        self._repositories = repositories
        self._clock = clock
        self._content_for_everyone = content_for_everyone
        self._developer_logs = developer_logs

    def record(
        self,
        snapshot: UserSnapshot,
        step: ModelStep,
        model: str,
        instructions: str,
        history: Sequence[ChatLine],
        tools: Sequence[ChatTool],
        started_at: datetime,
        answer: ModelAnswer | None,
        error: Exception | None,
    ) -> None:
        """Record one model call that has just ended.

        Saving never raises: a failure is logged and the reply goes on.

        Args:
            snapshot: The User the call was for, with the trace it belongs to.
            step: Which step it was for.
            model: The model asked.
            instructions: What the model was told to be and do.
            history: The lines it was given, oldest first.
            tools: The tools it was offered.
            started_at: When it started.
            answer: Its answer; None if it failed.
            error: What it failed with; None if it worked.
        """
        duration = self._clock.now() - started_at
        content = ModelCallContent(
            instructions=instructions,
            history=tuple(history),
            tools_offered=tuple(
                OfferedTool(tool.name, tool.description, tool.parameters)
                for tool in tools
            ),
            tool_calls=answer.tool_calls if answer else (),
            response=answer.text if answer else "",
            reasoning=answer.reasoning if answer else None,
        )
        call = ModelCall(
            id=uuid4(),
            trace=snapshot.trace,
            user_id=snapshot.user.id,
            step=step,
            model=model,
            started_at=started_at,
            duration_ms=duration // timedelta(milliseconds=1),
            tokens_in=answer.tokens_in if answer else 0,
            tokens_out=answer.tokens_out if answer else 0,
            error=type(error).__name__ if error else None,
            tools_called=tuple(
                tool_call.name for tool_call in (answer.tool_calls if answer else ())
            ),
            content=content if self._keeps_content(snapshot) else None,
        )
        if self._developer_logs:
            logger.info(
                "Model call %s for trace %s: %s",
                step.value,
                snapshot.trace.id,
                json.dumps(asdict(content), default=str, ensure_ascii=False),
            )
        try:
            self._repositories.model_calls.add(call)
        except Exception:
            logger.exception("Could not save a Model Call Log entry")

    def list_traces(
        self,
        user_id: UUID | None,
        days: int | None,
        step: ModelStep | None,
        errors_only: bool,
    ) -> list[ModelCallTraceOverview]:
        """List the newest traces for Admins.

        Args:
            user_id: Only this User's traces; None for every User.
            days: Only traces from the last this many days; None for all time.
            step: Only traces with a call for this step; None for every step.
            errors_only: Only traces with a failed call.

        Returns:
            Up to `TRACES_LISTED_AT_MOST` traces, newest first.
        """
        since = self._clock.now() - timedelta(days=days) if days else None
        return self._repositories.model_calls.list_traces(
            user_id, since, step, errors_only, TRACES_LISTED_AT_MOST
        )

    def open_trace(self, trace_id: UUID) -> ModelCallTraceDetails:
        """Read one trace with every call in it, for Admins.

        Args:
            trace_id: The trace's ID.

        Returns:
            The trace.

        Raises:
            ModelCallTraceNotFoundError: If there is no such trace.
        """
        trace = self._repositories.model_calls.get_trace(trace_id)
        if trace is None:
            raise ModelCallTraceNotFoundError(trace_id)
        return trace

    def _keeps_content(self, snapshot: UserSnapshot) -> bool:
        """Say whether a call for this User keeps its full content.

        Args:
            snapshot: The User the call was for.

        Returns:
            True for an Admin, or for everyone in an Eval run.
        """
        return self._content_for_everyone or snapshot.user.role == UserRole.ADMIN
