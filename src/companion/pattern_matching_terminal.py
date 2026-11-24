import argparse
import sys
from collections.abc import Callable, Sequence

from companion.core.errors import InvalidError
from companion.core.pattern_matching import PatternMatcher, report_lines
from companion.main import build_production_app


def read_pattern_type_ids(ids: str) -> list[str]:
    """Read the Pattern Types asked for on the command line.

    Args:
        ids: Comma-separated Pattern Type IDs; "" for all.

    Returns:
        The IDs.
    """
    return [value.strip() for value in ids.split(",") if value.strip()]


def match_and_report(
    matcher: PatternMatcher,
    pattern_type_ids: Sequence[str],
    write: Callable[[str], None],
) -> None:
    """Run the matching pass and print what it did.

    Args:
        matcher: Matches Patterns with no Pattern Type to the catalog.
        pattern_type_ids: The Pattern Types to match against; all when
            empty.
        write: Prints one line.

    Raises:
        InvalidError: If an ID given isn't in the Pattern Catalog.
    """
    for line in report_lines(matcher.match(pattern_type_ids)):
        write(line)


def main() -> None:
    """Run `make match-patterns`: match this stack's Patterns to the catalog.

    Matches against every Pattern Type unless `--pattern-types` picks some.

    Exits 0 when the pass ran, and 2 when a Pattern Type asked for isn't in
    the Pattern Catalog.
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
    matcher: PatternMatcher = build_production_app().state.pattern_matcher
    try:
        match_and_report(matcher, arguments.pattern_types, print)
    except InvalidError as error:
        print(error, file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
