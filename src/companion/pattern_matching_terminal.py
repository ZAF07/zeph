import argparse
import sys
from collections.abc import Callable, Sequence

from companion.config import load_settings
from companion.core.errors import InvalidError
from companion.core.model_call_log import ModelCallLog
from companion.core.observations import PatternTagger
from companion.core.pattern_catalog import PatternCatalogService
from companion.core.pattern_matching import PatternMatcher, UserMatchingReport
from companion.core.pattern_scoring import PatternScorer
from companion.core.ports import ChatModel, Clock, PhotoViewer, Repositories
from companion.core.usage import UsageLimiter, UsageRecordingChatModel
from companion.core.user_snapshot import UserSnapshotLoader
from companion.main import (
    build_chat_model,
    build_clock,
    build_database_engine,
    build_photo_viewer,
    build_repositories,
)


def read_pattern_type_ids(ids: str) -> list[str]:
    """Read the Pattern Types asked for on the command line.

    Args:
        ids: Comma-separated Pattern Type IDs; "" for all.

    Returns:
        The IDs.
    """
    return [value.strip() for value in ids.split(",") if value.strip()]


def report_lines(reports: Sequence[UserMatchingReport]) -> list[str]:
    """Write what the matching pass did, for the Admin who ran it.

    Args:
        reports: What was done for each User.

    Returns:
        One line per User and per Pattern, with IDs and counts only, never
        a User's words; a single line when there was nothing to match.
    """
    if not reports:
        return ["No Pattern to match."]
    lines = []
    for report in reports:
        if report.skipped_why is not None:
            lines.append(f"User {report.user_id}: skipped ({report.skipped_why})")
            continue
        matched = sum(1 for match in report.matches if match.pattern_type_id)
        lines.append(
            f"User {report.user_id}: {len(report.matches)} Patterns looked at, "
            f"{matched} matched, {report.conversations_tagged} Conversations tagged "
            f"again, {report.observations_kept} Observations kept, "
            f"{report.days_without_messages} evidence days with no messages left"
        )
        lines.extend(
            f"  Pattern {match.pattern_id} ({match.state.value}): "
            f"{match.pattern_type_id or 'fits no Pattern Type'}"
            for match in report.matches
        )
    return lines


def match_and_report(
    matcher: PatternMatcher,
    pattern_type_ids: Sequence[str],
    write: Callable[[str], None],
) -> bool:
    """Run the matching pass and print what it did.

    Args:
        matcher: Matches Patterns with no Pattern Type to the catalog.
        pattern_type_ids: The Pattern Types to match against; all when
            empty.
        write: Prints one line.

    Returns:
        True if no User's matching failed.

    Raises:
        InvalidError: If an ID given isn't in the Pattern Catalog.
    """
    reports = matcher.match(pattern_type_ids)
    for line in report_lines(reports):
        write(line)
    return not any(report.failed for report in reports)


def build_pattern_matcher(
    repositories: Repositories,
    chat_model: ChatModel,
    photo_viewer: PhotoViewer,
    clock: Clock,
) -> PatternMatcher:
    """Build the Pattern matcher on the app database, as the backend builds its steps.

    Args:
        repositories: Where everything is stored.
        chat_model: Generates the answers.
        photo_viewer: Looks at photos; never used by matching.
        clock: Tells the time.

    Returns:
        The matcher.
    """
    model_call_log = ModelCallLog(
        repositories, clock, content_for_everyone=False, developer_logs=False
    )
    recording_chat_model = UsageRecordingChatModel(
        chat_model,
        photo_viewer,
        UsageLimiter(repositories, clock),
        model_call_log,
        clock,
    )
    pattern_catalog = PatternCatalogService(repositories.pattern_catalog)
    return PatternMatcher(
        repositories=repositories,
        pattern_catalog=pattern_catalog,
        user_snapshots=UserSnapshotLoader(repositories, clock),
        chat_model=recording_chat_model,
        pattern_tagger=PatternTagger(
            repositories=repositories,
            pattern_catalog=pattern_catalog,
            chat_model=recording_chat_model,
            model_call_log=model_call_log,
            clock=clock,
        ),
        pattern_scorer=PatternScorer(repositories, pattern_catalog, clock),
    )


def main() -> None:
    """Run `make match-patterns`: match this stack's Patterns to the catalog.

    Matches against every Pattern Type unless `--pattern-types` picks some.

    Exits 0 when the pass ran for every User, 1 when it failed for one, and
    2 when a Pattern Type asked for isn't in the Pattern Catalog.
    """
    parser = argparse.ArgumentParser(
        description="Match Patterns with no Pattern Type to the Pattern Catalog."
    )
    parser.add_argument(
        "--pattern-types",
        type=read_pattern_type_ids,
        default=[],
        help="Comma-separated Pattern Type IDs to match against; all by default.",
    )
    arguments = parser.parse_args()
    settings = load_settings()
    matcher = build_pattern_matcher(
        build_repositories(settings, build_database_engine(settings)),
        build_chat_model(settings),
        build_photo_viewer(settings),
        build_clock(settings),
    )
    try:
        every_user_done = match_and_report(matcher, arguments.pattern_types, print)
    except InvalidError as error:
        print(error, file=sys.stderr)
        sys.exit(2)
    sys.exit(0 if every_user_done else 1)


if __name__ == "__main__":
    main()
