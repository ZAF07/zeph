from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID


class EvalName(StrEnum):
    """One of the six Evals."""

    SAFEGUARD = "safeguard"
    PERSONA = "persona"
    KNOWLEDGE = "knowledge"
    SETTINGS = "settings"
    PHOTO_DESCRIPTIONS = "photo_descriptions"
    UNDERSTANDING = "understanding"


class EvalRunState(StrEnum):
    """Where an Eval Run stands."""

    QUEUED = "queued"
    RUNNING = "running"
    FINISHED = "finished"
    INTERRUPTED = "interrupted"


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
FIRST_TRY = 1


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


@dataclass(frozen=True)
class Variant:
    """One set of settings an Eval Run runs its cases with.

    Attributes:
        letter: Its letter, e.g. "A".
        setting_overrides: Platform Settings changed for it, by key; empty
            for the live settings.
    """

    letter: str
    setting_overrides: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RunSnapshot:
    """What an Eval Run used, kept so it can be read later.

    Attributes:
        settings: The live Platform Settings when it started, by key.
        judge: The Judge's settings, by name.
        cases: Each case as it was when it started.
    """

    settings: dict[str, Any]
    judge: dict[str, Any]
    cases: list[EvalCase]


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


@dataclass(frozen=True)
class RunTotals:
    """How an Eval Run's finished cases went, added up.

    Attributes:
        passed: Cases that passed.
        failed: Cases that failed.
        errored: Cases that couldn't be checked.
        tokens_in: Tokens the LLM read.
        tokens_out: Tokens the LLM wrote.
    """

    passed: int = 0
    failed: int = 0
    errored: int = 0
    tokens_in: int = 0
    tokens_out: int = 0


@dataclass(frozen=True)
class EvalRunOverview:
    """An Eval Run with its totals, for the runs list.

    Attributes:
        run: The run.
        case_count: How many cases it runs in all; None while Queued.
        totals: Its finished cases added up.
    """

    run: EvalRun
    case_count: int | None
    totals: RunTotals


@dataclass(frozen=True)
class EvalRunDetails:
    """An Eval Run with its Case Results so far.

    Attributes:
        overview: The run and its totals.
        results: Its Case Results, in the order they finished.
    """

    overview: EvalRunOverview
    results: list[CaseResult]


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
