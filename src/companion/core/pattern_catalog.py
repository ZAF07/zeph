import re
from collections.abc import Mapping, Sequence
from datetime import date, datetime
from enum import StrEnum
from typing import Any

from companion.core.errors import InvalidError
from companion.core.models import (
    CatalogPatternType,
    ExcludedEvidence,
    LookAlike,
    PatternArea,
    PatternExclusion,
    PatternSign,
    PatternType,
    PatternTypeFile,
    PatternTypeNumbers,
    PatternTypeStatus,
    PatternTypeVersion,
    SignPart,
    SignStrength,
)
from companion.core.ports import PatternCatalogRepository

PATTERN_TYPE_ID = re.compile(r"[A-Z][A-Z0-9]*(\.[A-Z][A-Z0-9]*)+")
VERSION = re.compile(r"\d+\.\d+\.\d+")


class InvalidPatternCatalogError(InvalidError):
    """Raised when the Pattern Catalog's files can't be loaded as they are.

    Attributes:
        problems: Everything wrong, each with its file and field.
    """

    def __init__(self, problems: Sequence[str]) -> None:
        """Set up the error.

        Args:
            problems: Everything wrong, each with its file and field.
        """
        lines = [f"- {problem}" for problem in problems]
        super().__init__(
            "\n".join(
                ["The Pattern Catalog can't be loaded. Nothing was changed.", *lines]
            )
        )
        self.problems = list(problems)


class _Fields:
    """One group of fields in a Pattern Type file, read one field at a time.

    Each problem found is noted with the file and the field's place, and a
    stand-in value is given back, so reading goes on and finds the rest.
    """

    def __init__(
        self, content: Mapping[str, Any], place: str, problems: list[str]
    ) -> None:
        """Set up the group.

        Args:
            content: The group's fields by name.
            place: What goes before a field's name in a problem, such as
                `a.yaml: signs[1].`.
            problems: Where problems are noted.
        """
        self._content = content
        self._place = place
        self._problems = problems
        self._read: set[str] = set()

    def note(self, problem: str) -> None:
        """Note a problem at this group's place.

        Args:
            problem: What is wrong, starting with the field's name.
        """
        self._problems.append(f"{self._place}{problem}")

    def has(self, field: str) -> bool:
        """Say whether a field is given.

        Args:
            field: The field's name.

        Returns:
            True when the file gives it a value.
        """
        self._read.add(field)
        return self._content.get(field) is not None

    def _value(self, field: str) -> Any:
        """Take a required field's value, noting it when it is missing.

        Args:
            field: The field's name.

        Returns:
            Its value, or None when it is missing.
        """
        if not self.has(field):
            self.note(f"{field} is missing.")
        return self._content.get(field)

    def text(self, field: str) -> str:
        """Read a required text field.

        Args:
            field: The field's name.

        Returns:
            The text without surrounding spaces; empty when it is not valid.
        """
        value = self._value(field)
        if value is None:
            return ""
        if not isinstance(value, str):
            self.note(f"{field} must be text.")
            return ""
        if not value.strip():
            self.note(f"{field} must not be empty.")
        return value.strip()

    def optional_text(self, field: str) -> str | None:
        """Read a text field that may be left out.

        Args:
            field: The field's name.

        Returns:
            The text, or None when the field is left out.
        """
        return self.text(field) if self.has(field) else None

    def matching(self, field: str, shape: re.Pattern[str], example: str) -> str:
        """Read a required text field that must have a set shape.

        Args:
            field: The field's name.
            shape: What the whole text must match.
            example: A text of the right shape, shown when it does not.

        Returns:
            The text.
        """
        value = self.text(field)
        if value and not shape.fullmatch(value):
            self.note(f"{field} must look like {example}.")
        return value

    def choice[Choice: StrEnum](self, field: str, choices: type[Choice]) -> Choice:
        """Read a required field whose value comes from a fixed list.

        Args:
            field: The field's name.
            choices: The fixed list.

        Returns:
            The value; the list's first one when it is not valid.
        """
        value = self.text(field)
        allowed = [choice.value for choice in choices]
        if value in allowed:
            return choices(value)
        if value:
            self.note(f"{field} is {value}; it must be one of {', '.join(allowed)}.")
        return next(iter(choices))

    def texts(self, field: str) -> tuple[str, ...]:
        """Read a required list of texts.

        Args:
            field: The field's name.

        Returns:
            The texts; empty when the list is not valid.
        """
        value = self._value(field)
        if value is None:
            return ()
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            self.note(f"{field} must be a list of texts.")
            return ()
        return tuple(item.strip() for item in value)

    def groups(self, field: str, at_least_one: bool = False) -> list["_Fields"]:
        """Read a required list of groups, such as the signs.

        Args:
            field: The field's name.
            at_least_one: Whether an empty list is a problem.

        Returns:
            Each entry's fields, in order; entries that are not groups are
            read as empty ones.
        """
        value = self._value(field)
        if value is None:
            return []
        if not isinstance(value, list):
            self.note(f"{field} must be a list.")
            return []
        if at_least_one and not value:
            self.note(f"{field} needs at least one entry.")
        return [
            self._group(f"{field}[{number}]", entry)
            for number, entry in enumerate(value, start=1)
        ]

    def group(self, field: str) -> "_Fields":
        """Read a required group of fields, such as the numbers.

        Args:
            field: The field's name.

        Returns:
            The group's fields; an empty group when it is missing.
        """
        value = self._value(field)
        return _Fields({}, "", []) if value is None else self._group(field, value)

    def _group(self, name: str, content: Any) -> "_Fields":
        """Open a group inside this one.

        Args:
            name: The group's name with its place in a list, e.g. `signs[1]`.
            content: What the file holds there.

        Returns:
            The group's fields; an empty group when it is not one.
        """
        if not isinstance(content, Mapping):
            self.note(f"{name} must be a group of fields.")
            return _Fields({}, "", [])
        return _Fields(content, f"{self._place}{name}.", self._problems)

    def whole_number(self, field: str) -> int:
        """Read a required whole number, 1 or more.

        Args:
            field: The field's name.

        Returns:
            The number; 1 when it is not valid.
        """
        value = self._value(field)
        if value is None:
            return 1
        if type(value) is not int or value < 1:
            self.note(f"{field} must be a whole number, 1 or more.")
            return 1
        return value

    def share(self, field: str) -> float:
        """Read a required number between 0 and 1.

        Args:
            field: The field's name.

        Returns:
            The number; 0 when it is not valid.
        """
        value = self._value(field)
        if value is None:
            return 0.0
        if type(value) not in (int, float) or not 0 <= value <= 1:
            self.note(f"{field} must be a number between 0 and 1.")
            return 0.0
        return float(value)

    def optional_day(self, field: str) -> date | None:
        """Read a day that may be left out.

        Args:
            field: The field's name.

        Returns:
            The day, or None when it is left out or not valid.
        """
        value = self.optional_text(field)
        try:
            return date.fromisoformat(value) if value else None
        except ValueError:
            self.note(f"{field} must be a day like 2026-11-24.")
            return None

    def no_other_fields(self, owner: str) -> None:
        """Note every field given that was never read, such as a misspelt one.

        Args:
            owner: What the fields belong to, e.g. "a sign".
        """
        for field in self._content:
            if field not in self._read:
                self.note(f"{field} is not a field of {owner}.")


def _read_signs(groups: list[_Fields]) -> tuple[PatternSign, ...]:
    """Read the signs for, or against, a Pattern Type.

    Args:
        groups: Each sign's fields.

    Returns:
        The signs, in order.
    """
    signs = []
    for group in groups:
        signs.append(
            PatternSign(
                id=group.text("id"),
                text=group.text("text"),
                strength=group.choice("strength", SignStrength),
                part=group.choice("part", SignPart),
            )
        )
        group.no_other_fields("a sign")
    return tuple(signs)


def _read_look_alikes(fields: _Fields) -> tuple[LookAlike, ...]:
    """Read what a Pattern Type can be mistaken for.

    Args:
        fields: The Pattern Type's fields.

    Returns:
        The look-alikes, in order.
    """
    look_alikes = []
    for number, group in enumerate(fields.groups("look_alikes"), start=1):
        look_alike = LookAlike(
            pattern_type_id=group.optional_text("pattern_type"),
            name=group.optional_text("name"),
            tells_apart=group.text("tells_apart"),
        )
        names_given = sum(
            name is not None for name in (look_alike.pattern_type_id, look_alike.name)
        )
        if names_given != 1:
            ending = ", not both." if names_given == 2 else "."
            fields.note(
                f"look_alikes[{number}] needs either pattern_type or name{ending}"
            )
        group.no_other_fields("a look-alike")
        look_alikes.append(look_alike)
    return tuple(look_alikes)


def _read_exclusions(groups: list[_Fields]) -> tuple[PatternExclusion, ...]:
    """Read when a Pattern Type must not be shared.

    Args:
        groups: Each exclusion's fields.

    Returns:
        The exclusions, in order.
    """
    exclusions = []
    for group in groups:
        exclusions.append(
            PatternExclusion(
                text=group.text("text"),
                evidence=group.choice("evidence", ExcludedEvidence),
            )
        )
        group.no_other_fields("an exclusion")
    return tuple(exclusions)


def _read_numbers(group: _Fields) -> PatternTypeNumbers:
    """Read a Pattern Type's own numbers.

    Args:
        group: The numbers' fields.

    Returns:
        The numbers.
    """
    numbers = PatternTypeNumbers(
        situations_needed=group.whole_number("situations_needed"),
        base_rate=group.share("base_rate"),
    )
    group.no_other_fields("numbers")
    return numbers


def _read_pattern_type(
    file: PatternTypeFile, problems: list[str]
) -> PatternType | None:
    """Read one Pattern Type file, noting everything wrong with it.

    Args:
        file: The file.
        problems: Where problems are noted.

    Returns:
        The Pattern Type, with stand-in values where the file is wrong; None
        when the file holds no fields at all.
    """
    if not isinstance(file.content, Mapping):
        problems.append(f"{file.name}: the file must hold a Pattern Type's fields.")
        return None
    fields = _Fields(file.content, f"{file.name}: ", problems)
    status = fields.choice("status", PatternTypeStatus)
    approved_by = fields.optional_text("approved_by")
    approval_given = approved_by is not None or fields.has("approved_on")
    approval_whole = approved_by is not None and fields.has("approved_on")
    pattern_type = PatternType(
        id=fields.matching("id", PATTERN_TYPE_ID, "CONF.AVOID.BELONG"),
        version=fields.matching("version", VERSION, "1.0.0"),
        area=fields.choice("area", PatternArea),
        name=fields.text("name"),
        definition=fields.text("definition"),
        if_situation=fields.text("if"),
        then_behaviour=fields.text("then"),
        function=fields.text("function"),
        frameworks=fields.texts("frameworks"),
        signs=_read_signs(fields.groups("signs", at_least_one=True)),
        signs_against=_read_signs(fields.groups("signs_against", at_least_one=True)),
        look_alikes=_read_look_alikes(fields),
        anyone_would=fields.optional_text("anyone_would"),
        exclusions=_read_exclusions(fields.groups("exclusions")),
        approved_wording=fields.text("approved_wording"),
        prediction_wording=fields.text("prediction_wording"),
        numbers=_read_numbers(fields.group("numbers")),
        status=status,
        approved_by=approved_by,
        approved_on=fields.optional_day("approved_on"),
    )
    sign_ids = [sign.id for sign in pattern_type.signs + pattern_type.signs_against]
    for sign_id in dict.fromkeys(sign_ids):
        if sign_id and sign_ids.count(sign_id) > 1:
            fields.note(f"{sign_id} is the ID of more than one sign.")
    if status == PatternTypeStatus.APPROVED and not approval_whole:
        fields.note("an approved Pattern Type needs approved_by and approved_on.")
    if status == PatternTypeStatus.DRAFT and approval_given:
        fields.note(
            "only an approved or archived Pattern Type may have "
            "approved_by and approved_on."
        )
    fields.no_other_fields("a Pattern Type")
    return pattern_type


def _catalog_problems(
    read_files: Sequence[tuple[PatternTypeFile, PatternType]],
) -> list[str]:
    """Find what is wrong between Pattern Types, not inside one.

    Args:
        read_files: Each file with the Pattern Type read from it.

    Returns:
        A problem for each ID used twice and each look-alike naming a
        Pattern Type that is not in the catalog, or itself.
    """
    problems = []
    file_by_id: dict[str, str] = {}
    for file, pattern_type in read_files:
        first_file = file_by_id.setdefault(pattern_type.id, file.name)
        if pattern_type.id and first_file != file.name:
            problems.append(
                f"{file.name}: {pattern_type.id} is already the ID of the "
                f"Pattern Type in {first_file}."
            )
    for file, pattern_type in read_files:
        for number, look_alike in enumerate(pattern_type.look_alikes, start=1):
            other_id = look_alike.pattern_type_id
            if not other_id or (other_id in file_by_id and other_id != pattern_type.id):
                continue
            reason = (
                "this Pattern Type itself"
                if other_id == pattern_type.id
                else "not a Pattern Type in the catalog"
            )
            problems.append(
                f"{file.name}: look_alikes[{number}].pattern_type is {other_id}, "
                f"which is {reason}."
            )
    return problems


def read_pattern_types(files: Sequence[PatternTypeFile]) -> list[PatternType]:
    """Check the Pattern Catalog's files and read their Pattern Types.

    Args:
        files: Every Pattern Type file of the catalog.

    Returns:
        The Pattern Types, in the files' order.

    Raises:
        InvalidPatternCatalogError: If any file misses a required field, has
            a value outside a fixed list, names an unknown look-alike or is
            wrong in another way. It lists every problem found.
    """
    problems: list[str] = []
    read_files = [
        (file, pattern_type)
        for file in files
        if (pattern_type := _read_pattern_type(file, problems)) is not None
    ]
    problems.extend(_catalog_problems(read_files))
    if problems:
        raise InvalidPatternCatalogError(problems)
    return [pattern_type for _, pattern_type in read_files]


class PatternCatalogService:
    """Loads the Pattern Catalog from its files and reads it for Admins.

    Pattern Types are changed only in their files (ADR-0025), so there is no
    way to edit one here. Every version loaded is kept as it was.
    """

    def __init__(self, pattern_catalog: PatternCatalogRepository) -> None:
        """Set up the service.

        Args:
            pattern_catalog: Where Pattern Type versions are stored.
        """
        self._pattern_catalog = pattern_catalog

    def load(self, files: Sequence[PatternTypeFile], now: datetime) -> None:
        """Make the stored catalog follow its files, all together or not at all.

        A version not stored yet is added. Versions stored earlier stay as
        they were; the files' versions become the current ones.

        Args:
            files: Every Pattern Type file of the catalog.
            now: When new versions are loaded.

        Raises:
            InvalidPatternCatalogError: If a file is not valid, or a Pattern
                Type changed while keeping a version already stored.
        """
        pattern_types = read_pattern_types(files)
        stored_content = {
            (stored.pattern_type_id, stored.version): stored.content
            for stored in self._pattern_catalog.list_versions()
        }
        loaded = [
            PatternTypeVersion(
                pattern_type_id=pattern_type.id,
                version=pattern_type.version,
                content=file.content,
                is_current=True,
                loaded_at=now,
            )
            for file, pattern_type in zip(files, pattern_types, strict=True)
        ]
        problems = [
            f"{file.name}: {version.pattern_type_id} has changed but its version "
            f"is still {version.version}. Give it a new version; a stored "
            "version never changes."
            for file, version in zip(files, loaded, strict=True)
            if stored_content.get(
                (version.pattern_type_id, version.version), version.content
            )
            != version.content
        ]
        if problems:
            raise InvalidPatternCatalogError(problems)
        self._pattern_catalog.save_loaded(loaded)

    def catalog(self) -> list[CatalogPatternType]:
        """Read every Pattern Type in the catalog now.

        Returns:
            The Pattern Types at their current versions, by area and then ID,
            each with when it was loaded and its other stored versions.
        """
        versions = self._pattern_catalog.list_versions()
        current = [version for version in versions if version.is_current]
        pattern_types = read_pattern_types(
            [
                PatternTypeFile(name=version.pattern_type_id, content=version.content)
                for version in current
            ]
        )
        area_order = list(PatternArea)
        return sorted(
            (
                CatalogPatternType(
                    pattern_type=pattern_type,
                    loaded_at=version.loaded_at,
                    other_versions=tuple(
                        other.version
                        for other in versions
                        if other.pattern_type_id == pattern_type.id
                        and not other.is_current
                    ),
                )
                for version, pattern_type in zip(current, pattern_types, strict=True)
            ),
            key=lambda entry: (
                area_order.index(entry.pattern_type.area),
                entry.pattern_type.id,
            ),
        )
