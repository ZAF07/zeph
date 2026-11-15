from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import Engine, Row, Select, exists, func, select, update
from sqlalchemy.dialects.postgresql import insert

from companion.adapters.postgres.tables import (
    eval_case_results,
    eval_cases,
    eval_images,
    eval_judge_settings,
    eval_runs,
    eval_variants,
    users,
)
from companion.core.evals.models import (
    FIRST_VARIANT,
    CaseCheckResult,
    CaseOutcome,
    CaseResult,
    Check,
    EvalCase,
    EvalImage,
    EvalName,
    EvalRun,
    EvalRunOverview,
    EvalRunState,
    RunSnapshot,
    RunTotals,
    StartedFrom,
    StoredEvalCase,
    Variant,
)

TAKE_RUN_LOCK = 7_301_013
RUNNER_LOCK = 7_301_014


def _to_eval_case(values: dict[str, Any]) -> EvalCase:
    """Read an Eval Case from its stored values.

    Args:
        values: `key`, `eval`, `content` and `archived`.

    Returns:
        The case.
    """
    return EvalCase(
        key=values["key"],
        eval=EvalName(values["eval"]),
        content=values["content"],
        archived=values["archived"],
    )


def _eval_case_values(case: EvalCase) -> dict[str, Any]:
    """Write an Eval Case as values to store.

    Args:
        case: The case.

    Returns:
        Its `key`, `eval`, `content` and `archived`.
    """
    return {
        "key": case.key,
        "eval": case.eval.value,
        "content": case.content,
        "archived": case.archived,
    }


class PostgresEvalCaseRepository:
    """Stores Eval Cases in the app database."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The app database.
        """
        self._engine = engine

    def list_for_evals(self, evals: Sequence[EvalName]) -> list[EvalCase]:
        """List the cases of some Evals that aren't archived.

        Args:
            evals: The Evals.

        Returns:
            The cases, by Eval in the order given, then in the order added.
        """
        statement = (
            select(eval_cases)
            .where(
                eval_cases.c.eval.in_([name.value for name in evals]),
                eval_cases.c.archived.is_(False),
            )
            .order_by(eval_cases.c.position)
        )
        with self._engine.connect() as connection:
            cases = [
                _to_eval_case(row._asdict()) for row in connection.execute(statement)
            ]
        order = {name: number for number, name in enumerate(evals)}
        return sorted(cases, key=lambda case: order[case.eval])

    def add_missing(self, cases: Sequence[EvalCase], now: datetime) -> list[str]:
        """Add the cases whose key isn't stored yet, archived or not.

        Args:
            cases: The cases.
            now: When they are added.

        Returns:
            The keys added.
        """
        if not cases:
            return []
        rows = [
            {**_eval_case_values(case), "created_at": now, "updated_at": now}
            for case in cases
        ]
        with self._engine.begin() as connection:
            added = connection.execute(
                insert(eval_cases)
                .values(rows)
                .on_conflict_do_nothing()
                .returning(eval_cases.c.key)
            ).scalars()
            return list(added)

    def list_stored(self, eval_name: EvalName) -> list[StoredEvalCase]:
        """List every case of one Eval, archived ones too.

        Args:
            eval_name: The Eval.

        Returns:
            The cases, in the order added.
        """
        statement = (
            self._stored_cases()
            .where(eval_cases.c.eval == eval_name.value)
            .order_by(eval_cases.c.position)
        )
        with self._engine.connect() as connection:
            return [_to_stored_case(row) for row in connection.execute(statement)]

    def get(self, key: str) -> StoredEvalCase | None:
        """Read one case, archived or not.

        Args:
            key: Its key.

        Returns:
            The case; None if no case has the key.
        """
        statement = self._stored_cases().where(eval_cases.c.key == key)
        with self._engine.connect() as connection:
            row = connection.execute(statement).first()
        return _to_stored_case(row) if row is not None else None

    def add(self, case: EvalCase, now: datetime, admin_id: UUID) -> bool:
        """Add a case an Admin wrote.

        Args:
            case: The case.
            now: When it is added.
            admin_id: The Admin adding it.

        Returns:
            True if added; False if its key is taken.
        """
        row = {
            **_eval_case_values(case),
            "edited": True,
            "created_at": now,
            "created_by": admin_id,
            "updated_at": now,
            "updated_by": admin_id,
        }
        with self._engine.begin() as connection:
            added = connection.execute(
                insert(eval_cases)
                .values(row)
                .on_conflict_do_nothing()
                .returning(eval_cases.c.key)
            ).first()
        return added is not None

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
        with self._engine.begin() as connection:
            connection.execute(
                update(eval_cases)
                .where(eval_cases.c.key == key)
                .values(
                    content=content,
                    archived=archived,
                    edited=True,
                    updated_at=now,
                    updated_by=admin_id,
                )
            )

    @staticmethod
    def _stored_cases() -> Select[Any]:
        """Select cases with who last changed them.

        Returns:
            The query.
        """
        return select(
            eval_cases,
            func.coalesce(users.c.name, users.c.email).label("updated_by_name"),
        ).select_from(
            eval_cases.outerjoin(users, users.c.id == eval_cases.c.updated_by)
        )


def _to_stored_case(row: Row[Any]) -> StoredEvalCase:
    """Turn a case row, joined with its last editor, into a stored case.

    Args:
        row: The database row.

    Returns:
        The stored case.
    """
    values = row._asdict()
    return StoredEvalCase(
        case=_to_eval_case(values),
        edited=values["edited"],
        updated_at=values["updated_at"],
        updated_by_name=values["updated_by_name"],
    )


class PostgresEvalImageRepository:
    """Stores the test images cases send, in the app database."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The app database.
        """
        self._engine = engine

    def add_missing(self, images: Sequence[EvalImage], now: datetime) -> None:
        """Add the images whose name isn't stored yet; never change one.

        Args:
            images: The images.
            now: When they are added.
        """
        if not images:
            return
        rows = [
            {
                "name": image.name,
                "content": image.content,
                "media_type": image.media_type,
                "created_at": now,
            }
            for image in images
        ]
        with self._engine.begin() as connection:
            connection.execute(
                insert(eval_images).values(rows).on_conflict_do_nothing()
            )

    def get_many(self, names: Sequence[str]) -> list[EvalImage]:
        """Read some images.

        Args:
            names: Their names.

        Returns:
            The ones stored, in no particular order.
        """
        if not names:
            return []
        statement = select(eval_images).where(eval_images.c.name.in_(list(names)))
        with self._engine.connect() as connection:
            return [
                EvalImage(name=row.name, content=row.content, media_type=row.media_type)
                for row in connection.execute(statement)
            ]


class PostgresJudgeSettingsRepository:
    """Stores the Judge's settings in the app database."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The app database.
        """
        self._engine = engine

    def load(self) -> dict[str, Any]:
        """Read every Judge setting.

        Returns:
            Each setting's value by name.
        """
        with self._engine.connect() as connection:
            rows = connection.execute(select(eval_judge_settings))
            return {row.key: row.value for row in rows}

    def add_missing(self, values: Mapping[str, Any], now: datetime) -> None:
        """Add the settings not stored yet; never change one.

        Args:
            values: Each setting's starting value by name.
            now: When they are added.
        """
        rows = [
            {"key": key, "value": value, "updated_at": now}
            for key, value in values.items()
        ]
        if not rows:
            return
        with self._engine.begin() as connection:
            connection.execute(
                insert(eval_judge_settings).values(rows).on_conflict_do_nothing()
            )

    def save(self, values: Mapping[str, Any], now: datetime, admin_id: UUID) -> None:
        """Save new values for some settings.

        Args:
            values: Each setting's new value by name.
            now: When they changed.
            admin_id: The Admin changing them.
        """
        rows = [
            {"key": key, "value": value, "updated_at": now, "updated_by": admin_id}
            for key, value in values.items()
        ]
        if not rows:
            return
        statement = insert(eval_judge_settings).values(rows)
        with self._engine.begin() as connection:
            connection.execute(
                statement.on_conflict_do_update(
                    index_elements=[eval_judge_settings.c.key],
                    set_={
                        "value": statement.excluded.value,
                        "updated_at": statement.excluded.updated_at,
                        "updated_by": statement.excluded.updated_by,
                    },
                )
            )


def _check_values(result: CaseCheckResult) -> dict[str, Any]:
    """Write what checking a case found as values to store.

    Args:
        result: What checking it found.

    Returns:
        Its outcome, checks, facts, notes and error.
    """
    return {
        "outcome": result.outcome.value,
        "checks": [asdict(check) for check in result.checks],
        "facts": result.facts,
        "notes": result.notes,
        "error": result.error,
    }


def _to_case_result(row: Row[Any]) -> CaseResult:
    """Turn an `eval_case_results` row into a Case Result.

    Args:
        row: The database row.

    Returns:
        The Case Result.
    """
    return CaseResult(
        id=row.id,
        run_id=row.run_id,
        variant=row.variant,
        try_number=row.try_number,
        case_key=row.case_key,
        eval=EvalName(row.eval),
        case_content=row.case_content,
        result=CaseCheckResult(
            outcome=CaseOutcome(row.outcome),
            checks=[Check(**check) for check in row.checks],
            facts=row.facts,
            notes=row.notes,
            error=row.error,
        ),
        tokens_in=row.tokens_in,
        tokens_out=row.tokens_out,
        duration_ms=row.duration_ms,
        finished_at=row.finished_at,
    )


def _to_snapshot(row: Row[Any]) -> RunSnapshot | None:
    """Read a run's snapshot from its row.

    Args:
        row: The `eval_runs` row.

    Returns:
        The snapshot; None while the run is Queued.
    """
    if row.settings_snapshot is None:
        return None
    return RunSnapshot(
        settings=row.settings_snapshot,
        judge=row.judge_snapshot,
        cases=[_to_eval_case(case) for case in row.cases_snapshot],
    )


def _to_eval_run(row: Row[Any], variants: list[Variant]) -> EvalRun:
    """Turn an `eval_runs` row, with its starter's name, into an Eval Run.

    Args:
        row: The database row.
        variants: The run's Variants.

    Returns:
        The run.
    """
    return EvalRun(
        id=row.id,
        started_by_id=row.started_by,
        started_by_name=row.started_by_name,
        started_from=StartedFrom(row.started_from),
        state=EvalRunState(row.state),
        evals=[EvalName(name) for name in row.evals],
        repeats=row.repeats,
        variants=variants,
        queued_at=row.queued_at,
        started_at=row.started_at,
        finished_at=row.finished_at,
        snapshot=_to_snapshot(row),
    )


def _overview_statement() -> Select[Any]:
    """Build the query for runs with their starter's name and totals.

    Returns:
        The query, newest run first.
    """
    results = eval_case_results.c
    totals = (
        select(
            results.run_id,
            func.count()
            .filter(results.outcome == CaseOutcome.PASS.value)
            .label("passed"),
            func.count()
            .filter(results.outcome == CaseOutcome.FAIL.value)
            .label("failed"),
            func.count()
            .filter(results.outcome == CaseOutcome.ERROR.value)
            .label("errored"),
            func.sum(results.tokens_in).label("tokens_in"),
            func.sum(results.tokens_out).label("tokens_out"),
        )
        .group_by(results.run_id)
        .subquery()
    )
    variant_counts = (
        select(eval_variants.c.run_id, func.count().label("variant_count"))
        .group_by(eval_variants.c.run_id)
        .subquery()
    )
    return (
        select(
            eval_runs,
            func.coalesce(users.c.name, users.c.email).label("started_by_name"),
            func.coalesce(totals.c.passed, 0).label("passed"),
            func.coalesce(totals.c.failed, 0).label("failed"),
            func.coalesce(totals.c.errored, 0).label("errored"),
            func.coalesce(totals.c.tokens_in, 0).label("tokens_in"),
            func.coalesce(totals.c.tokens_out, 0).label("tokens_out"),
            func.coalesce(variant_counts.c.variant_count, 1).label("variant_count"),
        )
        .select_from(
            eval_runs.outerjoin(users, users.c.id == eval_runs.c.started_by)
            .outerjoin(totals, totals.c.run_id == eval_runs.c.id)
            .outerjoin(variant_counts, variant_counts.c.run_id == eval_runs.c.id)
        )
        .order_by(eval_runs.c.position.desc())
    )


class PostgresEvalRunRepository:
    """Stores Eval Runs, their Variants and Case Results in the app database."""

    def __init__(self, engine: Engine) -> None:
        """Set up the repository.

        Args:
            engine: The app database.
        """
        self._engine = engine

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
        with self._engine.begin() as connection:
            connection.execute(
                insert(eval_runs).values(
                    id=run_id,
                    started_by=started_by,
                    started_from=started_from.value,
                    state=EvalRunState.QUEUED.value,
                    evals=[name.value for name in evals],
                    queued_at=queued_at,
                )
            )
            connection.execute(
                insert(eval_variants).values(run_id=run_id, letter=FIRST_VARIANT)
            )

    def get(self, run_id: UUID) -> EvalRun | None:
        """Read a run.

        Args:
            run_id: Its ID.

        Returns:
            The run; None if there is no such run.
        """
        overview = self.get_overview(run_id)
        return overview.run if overview else None

    def list_overviews(self, include_terminal: bool) -> list[EvalRunOverview]:
        """List runs with their totals, newest first.

        Args:
            include_terminal: Whether to list runs started from the terminal.

        Returns:
            The runs.
        """
        statement = _overview_statement()
        if not include_terminal:
            statement = statement.where(
                eval_runs.c.started_from != StartedFrom.TERMINAL.value
            )
        return self._read_overviews(statement)

    def get_overview(self, run_id: UUID) -> EvalRunOverview | None:
        """Read one run with its totals.

        Args:
            run_id: Its ID.

        Returns:
            The run; None if there is no such run.
        """
        overviews = self._read_overviews(
            _overview_statement().where(eval_runs.c.id == run_id)
        )
        return overviews[0] if overviews else None

    def list_results(self, run_id: UUID) -> list[CaseResult]:
        """List a run's Case Results in the order they finished.

        Args:
            run_id: The run.

        Returns:
            The results.
        """
        statement = (
            select(eval_case_results)
            .where(eval_case_results.c.run_id == run_id)
            .order_by(eval_case_results.c.position)
        )
        with self._engine.connect() as connection:
            return [_to_case_result(row) for row in connection.execute(statement)]

    def take_next_queued(self, now: datetime) -> EvalRun | None:
        """Mark the oldest Queued run Running, if no run is Running.

        A lock held for the transaction makes two runners taking at once
        safe: the second waits, then sees the first's run Running.

        Args:
            now: When it starts.

        Returns:
            The run taken; None if none was.
        """
        with self._engine.begin() as connection:
            connection.execute(select(func.pg_advisory_xact_lock(TAKE_RUN_LOCK)))
            running = connection.execute(
                select(exists().where(eval_runs.c.state == EvalRunState.RUNNING.value))
            ).scalar()
            if running:
                return None
            run_id = connection.execute(
                select(eval_runs.c.id)
                .where(eval_runs.c.state == EvalRunState.QUEUED.value)
                .order_by(eval_runs.c.position)
                .limit(1)
            ).scalar()
            if run_id is None:
                return None
            connection.execute(
                update(eval_runs)
                .where(eval_runs.c.id == run_id)
                .values(state=EvalRunState.RUNNING.value, started_at=now)
            )
        return self.get(run_id)

    def save_snapshot(self, run_id: UUID, snapshot: RunSnapshot) -> None:
        """Save what a run uses.

        Args:
            run_id: The run.
            snapshot: The settings, Judge settings and cases.
        """
        with self._engine.begin() as connection:
            connection.execute(
                update(eval_runs)
                .where(eval_runs.c.id == run_id)
                .values(
                    settings_snapshot=snapshot.settings,
                    judge_snapshot=snapshot.judge,
                    cases_snapshot=[_eval_case_values(case) for case in snapshot.cases],
                )
            )

    def add_result(self, result: CaseResult) -> None:
        """Save one Case Result.

        Args:
            result: The result.
        """
        with self._engine.begin() as connection:
            connection.execute(
                insert(eval_case_results).values(
                    id=result.id,
                    run_id=result.run_id,
                    variant=result.variant,
                    try_number=result.try_number,
                    case_key=result.case_key,
                    eval=result.eval.value,
                    case_content=result.case_content,
                    tokens_in=result.tokens_in,
                    tokens_out=result.tokens_out,
                    duration_ms=result.duration_ms,
                    finished_at=result.finished_at,
                    **_check_values(result.result),
                )
            )

    def finish(self, run_id: UUID, now: datetime) -> None:
        """Mark a Running run Finished.

        Args:
            run_id: The run.
            now: When it finished.
        """
        with self._engine.begin() as connection:
            connection.execute(
                update(eval_runs)
                .where(
                    eval_runs.c.id == run_id,
                    eval_runs.c.state == EvalRunState.RUNNING.value,
                )
                .values(state=EvalRunState.FINISHED.value, finished_at=now)
            )

    def interrupt_running(self, now: datetime) -> list[UUID]:
        """Mark every Running run Interrupted.

        Args:
            now: When they were interrupted.

        Returns:
            The runs marked.
        """
        with self._engine.begin() as connection:
            interrupted = connection.execute(
                update(eval_runs)
                .where(eval_runs.c.state == EvalRunState.RUNNING.value)
                .values(state=EvalRunState.INTERRUPTED.value, finished_at=now)
                .returning(eval_runs.c.id)
            ).scalars()
            return list(interrupted)

    def _read_overviews(self, statement: Select[Any]) -> list[EvalRunOverview]:
        """Read runs, their Variants and totals.

        Args:
            statement: The overview query, maybe narrowed.

        Returns:
            The runs, in the query's order.
        """
        with self._engine.connect() as connection:
            rows = connection.execute(statement).all()
            variant_rows = connection.execute(
                select(eval_variants)
                .where(eval_variants.c.run_id.in_([row.id for row in rows]))
                .order_by(eval_variants.c.letter)
            ).all()
        variants: dict[UUID, list[Variant]] = {}
        for variant in variant_rows:
            variants.setdefault(variant.run_id, []).append(
                Variant(variant.letter, variant.setting_overrides)
            )
        return [
            EvalRunOverview(
                run=_to_eval_run(row, variants.get(row.id, [])),
                case_count=(
                    len(row.cases_snapshot) * row.variant_count * row.repeats
                    if row.cases_snapshot is not None
                    else None
                ),
                totals=RunTotals(
                    passed=row.passed,
                    failed=row.failed,
                    errored=row.errored,
                    tokens_in=row.tokens_in,
                    tokens_out=row.tokens_out,
                ),
            )
            for row in rows
        ]


@contextmanager
def hold_runner_lock(engine: Engine) -> Iterator[None]:
    """Hold the one Eval runner's lock while the block runs.

    A second runner waits here, so only one ever works runs or marks them
    Interrupted, and the Eval database is never shared.

    Args:
        engine: The app database.

    Yields:
        Control while the lock is held.
    """
    with engine.connect() as connection:
        connection.execute(select(func.pg_advisory_lock(RUNNER_LOCK)))
        connection.commit()
        try:
            yield
        finally:
            connection.execute(select(func.pg_advisory_unlock(RUNNER_LOCK)))
            connection.commit()
