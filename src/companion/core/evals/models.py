from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from companion.core.models import Move, Need


class EvalName(StrEnum):
    """One of the nine Evals."""

    SAFEGUARD = "safeguard"
    PERSONA = "persona"
    KNOWLEDGE = "knowledge"
    SETTINGS = "settings"
    PHOTO_DESCRIPTIONS = "photo_descriptions"
    UNDERSTANDING = "understanding"
    MOVE_OUTCOME = "move_outcome"
    DAY_SUMMARY = "day_summary"
    TAGGING = "tagging"


class EvalRunState(StrEnum):
    """Where an Eval Run stands."""

    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    CANCELLED = "cancelled"
    STOPPED_OVER_LIMIT = "stopped_over_limit"
    INTERRUPTED = "interrupted"


ENDED_STATES = frozenset(
    {
        EvalRunState.FINISHED,
        EvalRunState.CANCELLED,
        EvalRunState.STOPPED_OVER_LIMIT,
        EvalRunState.INTERRUPTED,
    }
)


class StartedFrom(StrEnum):
    """Where an Eval Run was started."""

    DASHBOARD = "dashboard"
    TERMINAL = "terminal"


class CaseOutcome(StrEnum):
    """How one Eval Case went.

    An Error means the case couldn't be checked, so it never counts as a
    Fail.
    """

    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


FIRST_VARIANT = "A"
VARIANT_LETTERS = "ABC"
FIRST_TRY = 1
MAX_REPEATS = 5


@dataclass(frozen=True)
class ModelTokens:
    """The tokens one model read and wrote.

    Attributes:
        tokens_in: Tokens it read.
        tokens_out: Tokens it wrote.
    """

    tokens_in: int = 0
    tokens_out: int = 0

    def plus(self, other: "ModelTokens") -> "ModelTokens":
        """Add another count to this one.

        Args:
            other: The other count.

        Returns:
            Both added up.
        """
        return ModelTokens(
            self.tokens_in + other.tokens_in, self.tokens_out + other.tokens_out
        )

    def times(self, count: int) -> "ModelTokens":
        """Count these tokens a number of times over.

        Args:
            count: How many times.

        Returns:
            The tokens times `count`.
        """
        return ModelTokens(self.tokens_in * count, self.tokens_out * count)


def add_tokens_by_model(
    *counts: dict[str, ModelTokens],
) -> dict[str, ModelTokens]:
    """Add up tokens by model.

    Args:
        counts: Tokens by model name, any number of them.

    Returns:
        Each model's tokens across all of them.
    """
    total: dict[str, ModelTokens] = {}
    for count in counts:
        for model, tokens in count.items():
            total[model] = total.get(model, ModelTokens()).plus(tokens)
    return total


class CaseStoppedError(Exception):
    """Raised inside a case when its run is to stop before the case ends.

    The case then ends as an Error with this message.
    """


type StopCheck = Callable[[], str | None]


@dataclass(frozen=True)
class EvalCase:
    """A test case of one Eval, kept as data.

    Attributes:
        key: Its stable name, e.g. `reminded-of-sister`.
        eval: The Eval it belongs to.
        content: The case itself, in its Eval's case shape.
        archived: Whether it is archived, so new runs leave it out.
    """

    key: str
    eval: EvalName
    content: dict[str, Any]
    archived: bool = False


@dataclass(frozen=True)
class StoredEvalCase:
    """An Eval Case as Admins see it in the case list.

    Attributes:
        case: The case.
        edited: Whether an Admin changed it after it was added.
        updated_at: When it last changed.
        updated_by_name: The name or email of the Admin who last changed
            it; None if the seed added it and nobody changed it since.
    """

    case: EvalCase
    edited: bool
    updated_at: datetime
    updated_by_name: str | None


@dataclass(frozen=True)
class EvalImage:
    """A test image a case sends as a photo, kept with the cases.

    A stored image never changes, so an old run's cases still show the
    image they used.

    Attributes:
        name: Its name, which cases refer to it by.
        content: The image file.
        media_type: Its type, e.g. image/png.
    """

    name: str
    content: bytes
    media_type: str


@dataclass(frozen=True)
class Check:
    """One thing checked in a case, such as a Judge rule.

    Attributes:
        name: What was checked, e.g. a rule's ID or "need".
        passed: Whether it was as expected.
        detail: What happened, such as the Judge's reason.
        group: What it belongs to inside the case, such as the Message it
            checks; "" when the case has one part.
    """

    name: str
    passed: bool
    detail: str
    group: str = ""


@dataclass(frozen=True)
class CaseCheckResult:
    """What checking one case found, before it is saved.

    Attributes:
        outcome: Pass, Fail or Error.
        checks: Each thing checked, in order.
        facts: What the report needs besides the checks, such as the risk
            type the Safeguard saw.
        notes: Lines that help read a failure, such as the conversation.
        error: What went wrong, for an Error; "" otherwise.
    """

    outcome: CaseOutcome
    checks: list[Check] = field(default_factory=list)
    facts: dict[str, Any] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    error: str = ""


@dataclass(frozen=True)
class CaseResult:
    """One case's result in an Eval Run.

    Attributes:
        id: The result's ID.
        run_id: The Eval Run it belongs to.
        variant: The Variant's letter.
        try_number: Which try of the case this is, from 1.
        case_key: The case's key.
        eval: The case's Eval.
        case_content: The case as it was when it ran.
        result: What checking it found.
        tokens_in: Tokens the LLM read, the app's and the Judge's.
        tokens_out: Tokens the LLM wrote, the app's and the Judge's.
        duration_ms: How long the case took.
        finished_at: When it finished.
        tokens_by_model: The same tokens, by the model that used them.
    """

    id: UUID
    run_id: UUID
    variant: str
    try_number: int
    case_key: str
    eval: EvalName
    case_content: dict[str, Any]
    result: CaseCheckResult
    tokens_in: int
    tokens_out: int
    duration_ms: int
    finished_at: datetime
    tokens_by_model: dict[str, ModelTokens] = field(default_factory=dict)


@dataclass(frozen=True)
class MadeLive:
    """When an Admin made a Variant's Setting Overrides live, and what went live.

    Attributes:
        by_name: The Admin's name or email; None if they have since gone.
        at: When.
        applied_keys: The overrides applied, by key.
        left_out_keys: The overrides left out because their live value had
            changed since the run started, by key.
    """

    by_name: str | None
    at: datetime
    applied_keys: list[str]
    left_out_keys: list[str]


@dataclass(frozen=True)
class Variant:
    """One set of settings an Eval Run runs its cases with.

    Attributes:
        letter: Its letter, e.g. "A".
        setting_overrides: Platform Settings changed for it, by key, and
            Needs as `need:<id>`; empty for the live settings.
        made_live: When its overrides were made live; None if never.
    """

    letter: str
    setting_overrides: dict[str, Any] = field(default_factory=dict)
    made_live: MadeLive | None = None


@dataclass(frozen=True)
class RunSnapshot:
    """What an Eval Run used, kept so it can be read later.

    Attributes:
        settings: The live Platform Settings when it started, by key.
        judge: The Judge's settings, by name.
        cases: Each case as it was when it started.
        needs: The live Needs when it started, in order.
        moves: The live Moves when it started, in order.
    """

    settings: dict[str, Any]
    judge: dict[str, Any]
    cases: list[EvalCase]
    needs: list[Need] = field(default_factory=list)
    moves: list[Move] = field(default_factory=list)


@dataclass(frozen=True)
class EvalRun:
    """A run of some Evals' cases.

    Attributes:
        id: Its ID.
        started_by_id: The Admin who started it; None from the terminal.
        started_by_name: Their name or email; None from the terminal.
        started_from: The Dashboard or the terminal.
        state: Where it stands.
        evals: The Evals whose cases it runs.
        repeats: How many times each case runs per Variant.
        variants: The settings it runs the cases with.
        queued_at: When it was started.
        started_at: When the runner took it; None while Queued.
        finished_at: When it ended; None until then.
        snapshot: What it used; None until the runner takes it.
        case_keys: The keys of the cases it runs, in order.
        cancel_requested: Whether an Admin asked to cancel it while it ran.
        token_limit: The most tokens it may use; None until the runner
            takes it.
        rerun_of: The run whose failed cases it runs again; None otherwise.
    """

    id: UUID
    started_by_id: UUID | None
    started_by_name: str | None
    started_from: StartedFrom
    state: EvalRunState
    evals: list[EvalName]
    repeats: int
    variants: list[Variant]
    queued_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    snapshot: RunSnapshot | None = None
    case_keys: list[str] = field(default_factory=list)
    cancel_requested: bool = False
    token_limit: int | None = None
    rerun_of: UUID | None = None


@dataclass(frozen=True)
class RunTotals:
    """How an Eval Run's finished cases went, added up.

    Attributes:
        passed: Cases that passed.
        failed: Cases that failed.
        errored: Cases that couldn't be checked.
        tokens_in: Tokens the LLM read.
        tokens_out: Tokens the LLM wrote.
        tokens_by_model: The same tokens, by the model that used them.
    """

    passed: int = 0
    failed: int = 0
    errored: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    tokens_by_model: dict[str, ModelTokens] = field(default_factory=dict)


@dataclass(frozen=True)
class Cost:
    """What some tokens cost in SGD.

    Attributes:
        sgd: The cost of the tokens of models with a price.
        unpriced_models: Models that used tokens but have no price set, so
            their tokens aren't in `sgd`.
    """

    sgd: float = 0.0
    unpriced_models: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvalRunOverview:
    """An Eval Run with its totals, for the runs list.

    Attributes:
        run: The run.
        case_count: How many cases it runs in all, counting each Variant
            and Repeat.
        totals: Its finished cases added up.
        cost: What its tokens so far cost; empty until it is priced.
    """

    run: EvalRun
    case_count: int
    totals: RunTotals
    cost: Cost = field(default_factory=Cost)


@dataclass(frozen=True)
class VariantTotals:
    """How one Variant's finished cases went, added up.

    Attributes:
        letter: The Variant's letter.
        totals: Its passes, fails, errors and tokens.
        duration_ms: The time its cases took, added up.
        cost: What its tokens cost.
    """

    letter: str
    totals: RunTotals
    duration_ms: int
    cost: Cost


@dataclass(frozen=True)
class EvalRunDetails:
    """An Eval Run with its Case Results so far.

    Attributes:
        overview: The run and its totals.
        results: Its Case Results, in the order they finished.
        variant_totals: Each Variant's totals, in letter order.
    """

    overview: EvalRunOverview
    results: list[CaseResult]
    variant_totals: list[VariantTotals] = field(default_factory=list)


@dataclass(frozen=True)
class LiveChange:
    """An overridden setting whose live value changed since the run started.

    Attributes:
        key: The setting's key, or `need:<id>` for a Need.
        then: Its live value when the run started.
        now: Its live value now; None for a Need deleted since.
        override: The Variant's value.
    """

    key: str
    then: Any
    now: Any
    override: Any


@dataclass(frozen=True)
class EvalOverview:
    """An Eval and the cases a new run of it would run.

    Attributes:
        eval: The Eval.
        case_keys: Its cases' keys, not archived, in order.
    """

    eval: EvalName
    case_keys: list[str]


@dataclass(frozen=True)
class Replies:
    """What the Companion sent back to one message in an Eval.

    Attributes:
        texts: Its texts, in order.
        photo_file_ids: The file IDs of the photos it sent, in order.
    """

    texts: list[str]
    photo_file_ids: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class CaseHistoryRow:
    """A case's result in one run, with what that run used.

    Attributes:
        result: The Case Result, with the case as it was.
        run_queued_at: When its run was started.
        settings: The Platform Settings its Variant ran with: the run's
            snapshot with the Variant's Setting Overrides.
        judge: The Judge's settings in the run's snapshot.
    """

    result: CaseResult
    run_queued_at: datetime
    settings: dict[str, Any]
    judge: dict[str, Any]


@dataclass(frozen=True)
class CaseHistoryEntry:
    """A case's result in one run, marked with what changed since the run before.

    Attributes:
        result: The Case Result.
        run_queued_at: When its run was started.
        case_changed: Whether the case was different from the older result.
        changed_settings: The Platform Settings, and Judge settings as
            `judge.<name>`, that were different from the older result's run.
    """

    result: CaseResult
    run_queued_at: datetime
    case_changed: bool
    changed_settings: list[str]


@dataclass(frozen=True)
class CaseHistory:
    """A case and its pass or fail in recent runs.

    Attributes:
        case: The case as it is now.
        entries: Its newest results first, each marked with what changed
            since the result after it in the list.
    """

    case: EvalCase
    entries: list[CaseHistoryEntry]


@dataclass(frozen=True)
class VariantEstimate:
    """What one Variant of a run would use, before it starts.

    Attributes:
        letter: The Variant's letter.
        tokens: The tokens it would use, by model, counting every Repeat.
        cost: What those tokens would cost.
    """

    letter: str
    tokens: dict[str, ModelTokens]
    cost: Cost


@dataclass(frozen=True)
class Estimate:
    """What a run would use, before it starts. It is only an estimate.

    Attributes:
        tokens: The tokens it would use, by model, counting every Variant
            and Repeat.
        cost: What those tokens would cost.
        case_count: How many cases it would run, counting every Variant
            and Repeat.
        rough_case_count: How many of the cases picked have never run, so
            use a rough figure for their Eval.
        variants: What each Variant would use.
    """

    tokens: dict[str, ModelTokens]
    cost: Cost
    case_count: int
    rough_case_count: int
    variants: list[VariantEstimate] = field(default_factory=list)
