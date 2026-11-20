from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    Engine,
    Row,
    Select,
    bindparam,
    delete,
    exists,
    func,
    select,
    text,
    update,
)
from sqlalchemy import case as case_when
from sqlalchemy.dialects.postgresql import distinct_on, insert

from companion.adapters.postgres.repositories import to_model_call
from companion.adapters.postgres.tables import (
    eval_case_results,
    eval_cases,
    eval_images,
    eval_judge_settings,
    eval_model_calls,
    eval_runs,
    eval_variants,
    users,
)
from companion.core.evals.models import (
    CaseCheckResult,
    CaseHistoryRow,
    CaseOutcome,
    CaseResult,
    Check,
    EvalCase,
    EvalImage,
    EvalName,
    EvalRun,
    EvalRunOverview,
    EvalRunState,
    MadeLive,
    ModelTokens,
    RunSnapshot,
    RunTotals,
    StartedFrom,
    StoredEvalCase,
    Variant,
)
from companion.core.models import Feature, ModelCall, Move, Need

TAKE_RUN_LOCK = 7_301_013
RUNNER_LOCK = 7_301_014
TOKENS_BY_MODEL_PER_RUN = text(
    "SELECT result.run_id, used.key AS model, "
    "sum((used.value ->> 'in')::bigint) AS tokens_in, "
    "sum((used.value ->> 'out')::bigint) AS tokens_out "
    "FROM eval_case_results AS result "
    "CROSS JOIN LATERAL jsonb_each(result.tokens_by_model) AS used "
    "WHERE result.run_id IN :run_ids "
    "GROUP BY result.run_id, used.key"
).bindparams(bindparam("run_ids", expanding=True))


def _tokens_by_model_values(tokens: dict[str, ModelTokens]) -> dict[str, Any]:
    """Write tokens by model as values to store.

    Args:
        tokens: Each model's tokens.

    Returns:
        `{"<model>": {"in": ..., "out": ...}}`.
    """
    return {
        model: {"in": count.tokens_in, "out": count.tokens_out}
        for model, count in tokens.items()
    }


def _to_tokens_by_model(values: dict[str, Any]) -> dict[str, ModelTokens]:
    """Read stored tokens by model.

    Args:
        values: `{"<model>": {"in": ..., "out": ...}}`.

    Returns:
        Each model's tokens.
    """
    return {
        model: ModelTokens(count["in"], count["out"]) for model, count in values.items()
    }


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

    def list_for_keys(self, keys: Sequence[str]) -> list[EvalCase]:
        """List the cases with some keys that aren't archived.

        Args:
            keys: The keys.

        Returns:
            The cases found, in the order of `keys`.
        """
        statement = select(eval_cases).where(
            eval_cases.c.key.in_(list(keys)), eval_cases.c.archived.is_(False)
        )
        with self._engine.connect() as connection:
            found = {
                row.key: _to_eval_case(row._asdict())
                for row in connection.execute(statement)
            }
        return [found[key] for key in keys if key in found]

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
        tokens_by_model=_to_tokens_by_model(row.tokens_by_model),
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
        needs=[_to_need(need) for need in row.needs_snapshot],
        moves=[_to_move(move) for move in row.moves_snapshot],
    )


def _need_values(need: Need) -> dict[str, Any]:
    """Write a Need as JSON for a run's snapshot.

    Args:
        need: The Need.

    Returns:
        Its fields, the IDs as text.
    """
    return {
        "id": str(need.id),
        "name": need.name,
        "when_it_fits": need.when_it_fits,
        "how_to_reply": need.how_to_reply,
        "sort_order": need.sort_order,
        "is_fallback": need.is_fallback,
        "ruled_out_move_ids": sorted(
            str(move_id) for move_id in need.ruled_out_move_ids
        ),
    }


def _to_need(values: dict[str, Any]) -> Need:
    """Read a Need from a run's snapshot.

    Snapshots taken before Moves rule none out.

    Args:
        values: Its fields, as `_need_values` wrote them.

    Returns:
        The Need.
    """
    return Need(
        id=UUID(values["id"]),
        name=values["name"],
        when_it_fits=values["when_it_fits"],
        how_to_reply=values["how_to_reply"],
        sort_order=values["sort_order"],
        is_fallback=values["is_fallback"],
        ruled_out_move_ids=frozenset(
            UUID(move_id) for move_id in values.get("ruled_out_move_ids", [])
        ),
    )


def _move_values(move: Move) -> dict[str, Any]:
    """Write a Move as JSON for a run's snapshot.

    Args:
        move: The Move.

    Returns:
        Its fields, the ID as text.
    """
    return {
        "id": str(move.id),
        "name": move.name,
        "when_it_fits": move.when_it_fits,
        "how_to_do_it": move.how_to_do_it,
        "sort_order": move.sort_order,
        "needed_feature": (
            None if move.needed_feature is None else move.needed_feature.value
        ),
        "asks_a_question": move.asks_a_question,
    }


def _to_move(values: dict[str, Any]) -> Move:
    """Read a Move from a run's snapshot.

    Args:
        values: Its fields, as `_move_values` wrote them.

    Returns:
        The Move; one kept before Moves could ask a question asks none.
    """
    needed_feature = values["needed_feature"]
    return Move(
        id=UUID(values["id"]),
        name=values["name"],
        when_it_fits=values["when_it_fits"],
        how_to_do_it=values["how_to_do_it"],
        sort_order=values["sort_order"],
        needed_feature=None if needed_feature is None else Feature(needed_feature),
        asks_a_question=values.get("asks_a_question", False),
    )


def _to_variant(row: Row[Any]) -> Variant:
    """Turn an `eval_variants` row, with its Admin's name, into a Variant.

    Args:
        row: The database row.

    Returns:
        The Variant.
    """
    made_live = (
        MadeLive(
            by_name=row.made_live_by_name,
            at=row.made_live_at,
            applied_keys=row.applied_keys,
            left_out_keys=row.left_out_keys,
        )
        if row.made_live_at is not None
        else None
    )
    return Variant(row.letter, row.setting_overrides, made_live)


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
        case_keys=row.case_keys,
        cancel_requested=row.cancel_requested,
        token_limit=row.token_limit,
        rerun_of=row.rerun_of,
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
        with self._engine.begin() as connection:
            connection.execute(
                insert(eval_runs).values(
                    id=run_id,
                    started_by=started_by,
                    started_from=started_from.value,
                    state=EvalRunState.QUEUED.value,
                    evals=[name.value for name in evals],
                    case_keys=list(case_keys),
                    queued_at=queued_at,
                    repeats=repeats,
                    rerun_of=rerun_of,
                )
            )
            connection.execute(
                insert(eval_variants),
                [
                    {
                        "run_id": run_id,
                        "letter": variant.letter,
                        "setting_overrides": variant.setting_overrides,
                    }
                    for variant in variants
                ],
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

    def get_result(self, run_id: UUID, result_id: UUID) -> CaseResult | None:
        """Read one Case Result of a run.

        Args:
            run_id: The run.
            result_id: The result.

        Returns:
            The result; None if the run has no such result.
        """
        with self._engine.connect() as connection:
            row = connection.execute(
                select(eval_case_results).where(
                    eval_case_results.c.run_id == run_id,
                    eval_case_results.c.id == result_id,
                )
            ).first()
        return _to_case_result(row) if row else None

    def list_result_calls(self, result_id: UUID) -> list[ModelCall]:
        """List a Case Result's model calls, its full trace.

        Each call reads as being for the made-up User of the Eval database.

        Args:
            result_id: The result.

        Returns:
            The calls, in the order they were made.
        """
        statement = (
            select(
                eval_model_calls, eval_model_calls.c.made_up_user_id.label("user_id")
            )
            .where(eval_model_calls.c.case_result_id == result_id)
            .order_by(eval_model_calls.c.position)
        )
        with self._engine.connect() as connection:
            return [to_model_call(row) for row in connection.execute(statement)]

    def newest_tokens_by_case(
        self, case_keys: Sequence[str]
    ) -> dict[str, dict[str, ModelTokens]]:
        """Read each case's tokens by model from its newest Case Result.

        Errors are skipped, since they may have stopped early, and so are
        results from before tokens were kept by model.

        Args:
            case_keys: The cases.

        Returns:
            Tokens by model for each case that has a result; cases never
            run are left out.
        """
        results = eval_case_results.c
        statement = (
            select(results.case_key, results.tokens_by_model)
            .ext(distinct_on(results.case_key))
            .where(
                results.case_key.in_(list(case_keys)),
                results.outcome != CaseOutcome.ERROR.value,
                results.tokens_by_model != {},
            )
            .order_by(results.case_key, results.position.desc())
        )
        with self._engine.connect() as connection:
            return {
                row.case_key: _to_tokens_by_model(row.tokens_by_model)
                for row in connection.execute(statement)
            }

    def list_case_history(self, case_key: str, limit: int) -> list[CaseHistoryRow]:
        """List a case's newest Case Results with what their runs used.

        Args:
            case_key: The case.
            limit: The most results to list.

        Returns:
            The results, newest first.
        """
        statement = (
            select(
                eval_case_results,
                eval_runs.c.queued_at.label("run_queued_at"),
                eval_runs.c.settings_snapshot,
                eval_runs.c.judge_snapshot,
                eval_variants.c.setting_overrides,
            )
            .select_from(
                eval_case_results.join(
                    eval_runs, eval_runs.c.id == eval_case_results.c.run_id
                ).outerjoin(
                    eval_variants,
                    (eval_variants.c.run_id == eval_case_results.c.run_id)
                    & (eval_variants.c.letter == eval_case_results.c.variant),
                )
            )
            .where(eval_case_results.c.case_key == case_key)
            .order_by(eval_case_results.c.position.desc())
            .limit(limit)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(statement).all()
        return [
            CaseHistoryRow(
                result=_to_case_result(row),
                run_queued_at=row.run_queued_at,
                settings={
                    **(row.settings_snapshot or {}),
                    **(row.setting_overrides or {}),
                },
                judge=row.judge_snapshot or {},
            )
            for row in rows
        ]

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

    def save_snapshot(
        self, run_id: UUID, snapshot: RunSnapshot, token_limit: int
    ) -> None:
        """Save what a run uses and the most tokens it may use.

        Args:
            run_id: The run.
            snapshot: The settings, Judge settings, cases and Needs.
            token_limit: The Eval run token limit when it started.
        """
        with self._engine.begin() as connection:
            connection.execute(
                update(eval_runs)
                .where(eval_runs.c.id == run_id)
                .values(
                    settings_snapshot=snapshot.settings,
                    judge_snapshot=snapshot.judge,
                    cases_snapshot=[_eval_case_values(case) for case in snapshot.cases],
                    needs_snapshot=[_need_values(need) for need in snapshot.needs],
                    moves_snapshot=[_move_values(move) for move in snapshot.moves],
                    token_limit=token_limit,
                )
            )

    def add_result(self, result: CaseResult, calls: Sequence[ModelCall]) -> None:
        """Save one Case Result with its full trace, in one step.

        Args:
            result: The result.
            calls: The model calls the case made.
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
                    tokens_by_model=_tokens_by_model_values(result.tokens_by_model),
                    duration_ms=result.duration_ms,
                    finished_at=result.finished_at,
                    **_check_values(result.result),
                )
            )
            if calls:
                connection.execute(
                    insert(eval_model_calls),
                    [_eval_model_call_values(result.id, call) for call in calls],
                )

    def is_cancel_requested(self, run_id: UUID) -> bool:
        """Say whether an Admin asked to cancel a run.

        Args:
            run_id: The run.

        Returns:
            True if they did.
        """
        with self._engine.connect() as connection:
            return bool(
                connection.execute(
                    select(eval_runs.c.cancel_requested).where(eval_runs.c.id == run_id)
                ).scalar()
            )

    def request_cancel(self, run_id: UUID, now: datetime) -> None:
        """Cancel a Queued run now, or ask the runner to cancel a Running one.

        One statement does both, so a run the runner takes at the same
        moment is still cancelled after its first case. Does nothing to a
        run that has ended.

        Args:
            run_id: The run.
            now: When it is cancelled.
        """
        is_queued = eval_runs.c.state == EvalRunState.QUEUED.value
        with self._engine.begin() as connection:
            connection.execute(
                update(eval_runs)
                .where(
                    eval_runs.c.id == run_id,
                    eval_runs.c.state.in_(
                        [EvalRunState.QUEUED.value, EvalRunState.RUNNING.value]
                    ),
                )
                .values(
                    cancel_requested=True,
                    state=case_when(
                        (is_queued, EvalRunState.CANCELLED.value),
                        else_=eval_runs.c.state,
                    ),
                    finished_at=case_when(
                        (is_queued, now), else_=eval_runs.c.finished_at
                    ),
                )
            )

    def end(self, run_id: UUID, state: EvalRunState, now: datetime) -> None:
        """End a Running run as Finished, Cancelled or Stopped over limit.

        A run an Admin asked to cancel ends Cancelled rather than Finished,
        decided in the same statement, so a cancel pressed after the last
        case is never lost.

        Args:
            run_id: The run.
            state: How it ended.
            now: When it ended.
        """
        ended_as: Any = state.value
        if state == EvalRunState.FINISHED:
            ended_as = case_when(
                (eval_runs.c.cancel_requested, EvalRunState.CANCELLED.value),
                else_=state.value,
            )
        with self._engine.begin() as connection:
            connection.execute(
                update(eval_runs)
                .where(
                    eval_runs.c.id == run_id,
                    eval_runs.c.state == EvalRunState.RUNNING.value,
                )
                .values(state=ended_as, finished_at=now)
            )

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
        with self._engine.begin() as connection:
            marked = connection.execute(
                update(eval_variants)
                .where(
                    eval_variants.c.run_id == run_id,
                    eval_variants.c.letter == letter,
                    eval_variants.c.made_live_at.is_(None),
                )
                .values(
                    made_live_by=admin_id,
                    made_live_at=now,
                    applied_keys=list(applied_keys),
                    left_out_keys=list(left_out_keys),
                )
            )
            return marked.rowcount == 1

    def unmark_made_live(self, run_id: UUID, letter: str) -> None:
        """Take off a Variant's made-live mark, when its save was refused.

        Args:
            run_id: The run.
            letter: The Variant's letter.
        """
        with self._engine.begin() as connection:
            connection.execute(
                update(eval_variants)
                .where(
                    eval_variants.c.run_id == run_id,
                    eval_variants.c.letter == letter,
                )
                .values(
                    made_live_by=None,
                    made_live_at=None,
                    applied_keys=[],
                    left_out_keys=[],
                )
            )

    def delete(self, run_id: UUID) -> None:
        """Delete a run with its Variants, Case Results and traces.

        Args:
            run_id: The run.
        """
        with self._engine.begin() as connection:
            connection.execute(delete(eval_runs).where(eval_runs.c.id == run_id))

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
            run_ids = [row.id for row in rows]
            variant_rows = connection.execute(
                select(
                    eval_variants,
                    func.coalesce(users.c.name, users.c.email).label(
                        "made_live_by_name"
                    ),
                )
                .select_from(
                    eval_variants.outerjoin(
                        users, users.c.id == eval_variants.c.made_live_by
                    )
                )
                .where(eval_variants.c.run_id.in_(run_ids))
                .order_by(eval_variants.c.letter)
            ).all()
            token_rows = (
                connection.execute(TOKENS_BY_MODEL_PER_RUN, {"run_ids": run_ids}).all()
                if run_ids
                else []
            )
        tokens_by_model: dict[UUID, dict[str, ModelTokens]] = {}
        for token_row in token_rows:
            tokens_by_model.setdefault(token_row.run_id, {})[token_row.model] = (
                ModelTokens(int(token_row.tokens_in), int(token_row.tokens_out))
            )
        variants: dict[UUID, list[Variant]] = {}
        for variant in variant_rows:
            variants.setdefault(variant.run_id, []).append(_to_variant(variant))
        return [
            EvalRunOverview(
                run=_to_eval_run(row, variants.get(row.id, [])),
                case_count=len(row.case_keys) * row.variant_count * row.repeats,
                totals=RunTotals(
                    passed=row.passed,
                    failed=row.failed,
                    errored=row.errored,
                    tokens_in=row.tokens_in,
                    tokens_out=row.tokens_out,
                    tokens_by_model=tokens_by_model.get(row.id, {}),
                ),
            )
            for row in rows
        ]


def _eval_model_call_values(case_result_id: UUID, call: ModelCall) -> dict[str, Any]:
    """Write a case's model call as values for `eval_model_calls`.

    Args:
        case_result_id: The Case Result it belongs to.
        call: The model call, read from the Eval database.

    Returns:
        Its values; its User is the made-up one.
    """
    return {
        "id": call.id,
        "case_result_id": case_result_id,
        "made_up_user_id": call.user_id,
        "trace_id": call.trace.id,
        "trace_kind": call.trace.kind.value,
        "step": call.step.value,
        "model": call.model,
        "thinking": call.thinking,
        "started_at": call.started_at,
        "duration_ms": call.duration_ms,
        "tokens_in": call.tokens_in,
        "tokens_out": call.tokens_out,
        "error": call.error,
        "tools_called": list(call.tools_called),
        "content": asdict(call.content) if call.content else None,
        "understanding_shape": (
            asdict(call.understanding_shape) if call.understanding_shape else None
        ),
        "check_in_shape": asdict(call.check_in_shape) if call.check_in_shape else None,
        "reply_plan_shape": (
            asdict(call.reply_plan_shape) if call.reply_plan_shape else None
        ),
    }


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
