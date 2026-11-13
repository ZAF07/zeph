from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

CASES_DIR = Path(__file__).parent / "cases"
IMAGES_DIR = Path(__file__).parent / "images"


class InvalidEvalCasesError(ValueError):
    """Raised when an eval cases file names something that doesn't exist."""


class SafeguardCaseKind(StrEnum):
    """How a Safeguard case is labelled."""

    CLEAR_CRISIS = "clear_crisis"
    SUBTLE_CRISIS = "subtle_crisis"
    FALSE_ALARM = "false_alarm"


@dataclass(frozen=True)
class SafeguardCase:
    """A labelled message for the Safeguard to classify.

    Attributes:
        id: A short name for the case.
        kind: Whether it is a clear crisis, a subtle crisis or a false alarm.
        message: The message to classify, or the photo's caption; "" for a
            photo with none.
        earlier: Messages the person sent before it, for context.
        photo: The file name of a test image in `evals/images/` sent as a
            photo with the message as its caption; None for a text message.
    """

    id: str
    kind: SafeguardCaseKind
    message: str = ""
    earlier: list[str] = field(default_factory=list)
    photo: str | None = None

    @property
    def is_crisis(self) -> bool:
        """Whether the Safeguard must catch this message.

        Returns:
            True for clear and subtle crises.
        """
        return self.kind != SafeguardCaseKind.FALSE_ALARM


@dataclass(frozen=True)
class EvalPhoto:
    """A test image sent as a photo, and what it really shows.

    Attributes:
        file_name: The image's file name in `evals/images/`.
        shows: What is really in it, as the judge is told.
    """

    file_name: str
    shows: str


@dataclass(frozen=True)
class EvalSharedPhoto:
    """A Shared Photo the person already has before a scripted conversation.

    Attributes:
        description: What it shows.
        note: Why it matters to them.
    """

    description: str
    note: str


@dataclass(frozen=True)
class PersonaMessage:
    """One message the person sends in a scripted conversation.

    Attributes:
        text: The text, or the photo's caption; "" for a photo with none.
        photo: The photo it is sent as, with `text` as its caption; None for
            a text message.
    """

    text: str
    photo: EvalPhoto | None = None


@dataclass(frozen=True)
class PersonaConversation:
    """A scripted conversation judged against some Persona rules.

    Attributes:
        id: A short name for the conversation.
        messages: What the person sends, in order.
        rules: The IDs of the rules its replies are judged against.
        shared_photos: The Shared Photos the person has before it starts.
        photo_viewing: Whether the person has Photo Viewing on.
    """

    id: str
    messages: list[PersonaMessage]
    rules: list[str]
    shared_photos: list[EvalSharedPhoto] = field(default_factory=list)
    photo_viewing: bool = True


@dataclass(frozen=True)
class PersonaCases:
    """The Persona rules and the scripted conversations.

    Attributes:
        rules: Each rule's ID and what the judge checks.
        conversations: The scripted conversations.
    """

    rules: dict[str, str]
    conversations: list[PersonaConversation]


@dataclass(frozen=True)
class KnowledgeDetails:
    """A Knowledge Document's title, source and tradition.

    Attributes:
        title: The title.
        source: Where it comes from.
        tradition: Its tradition.
    """

    title: str
    source: str
    tradition: str

    def describe(self) -> str:
        """Write the details as one line for the judge.

        Returns:
            The details, e.g. "title “Night”, source Brother Elk, tradition
            Coast".
        """
        return f"title “{self.title}”, source {self.source}, tradition {self.tradition}"


@dataclass(frozen=True)
class KnowledgeCase:
    """A made-up teaching, and the ways an Admin changes its document.

    Attributes:
        id: A short name for the case.
        question: What the User asks that the teaching answers.
        source_question: What the User asks to hear where the idea comes from.
        original_file_name: The first file's name.
        original_text: The first file's text.
        original_details: The details it is uploaded with.
        edited_text: The text the Admin edits it to.
        edited_details: The details the Admin edits it to.
        replacement_file_name: The replacement file's name.
        replacement_text: The replacement file's text.
    """

    id: str
    question: str
    source_question: str
    original_file_name: str
    original_text: str
    original_details: KnowledgeDetails
    edited_text: str
    edited_details: KnowledgeDetails
    replacement_file_name: str
    replacement_text: str


@dataclass(frozen=True)
class PhotoDescriptionCase:
    """A test image whose description must leave some details out.

    Attributes:
        id: A short name for the case.
        photo: The image's file name in `evals/images/`.
        must_leave_out: Text in the image that must never be in its
            description, like a card number or password.
    """

    id: str
    photo: str
    must_leave_out: list[str]


@dataclass(frozen=True)
class SettingsCase:
    """A message asking, or not asking, to change a setting in chat.

    Attributes:
        id: A short name for the case.
        message: What the User sends.
        tools: The settings tools the reply must call; empty when no setting
            may change.
    """

    id: str
    message: str
    tools: list[str]


def require_unique_ids(ids: Sequence[str], cases_file: Path) -> None:
    """Check that no two cases in a file share an ID.

    Args:
        ids: The cases' IDs.
        cases_file: The file they came from, for the error message.

    Raises:
        InvalidEvalCasesError: If an ID is used twice.
    """
    seen: set[str] = set()
    for case_id in ids:
        if case_id in seen:
            raise InvalidEvalCasesError(
                f"{cases_file.name}: id {case_id} is used twice"
            )
        seen.add(case_id)


def require_image(file_name: str, cases_file: Path) -> str:
    """Check that a test image a case names is in `evals/images/`.

    Args:
        file_name: The image's file name.
        cases_file: The file the case came from, for the error message.

    Returns:
        The file name.

    Raises:
        InvalidEvalCasesError: If there is no such image.
    """
    if not (IMAGES_DIR / file_name).is_file():
        raise InvalidEvalCasesError(
            f"{cases_file.name}: there is no image {file_name} in evals/images"
        )
    return file_name


def load_safeguard_cases(cases_file: Path) -> list[SafeguardCase]:
    """Read the labelled Safeguard messages.

    Args:
        cases_file: YAML list of cases with `id`, `kind`, and a `message`, a
            `photo` or both, and optionally `earlier`.

    Returns:
        The cases, in the order listed.

    Raises:
        InvalidEvalCasesError: If two cases share an ID or a case names an
            image that isn't there.
    """
    entries: list[dict[str, Any]] = yaml.safe_load(cases_file.read_text())
    cases = [
        SafeguardCase(
            id=entry["id"],
            kind=SafeguardCaseKind(entry["kind"]),
            message=entry.get("message", ""),
            earlier=entry.get("earlier", []),
            photo=require_image(entry["photo"], cases_file)
            if "photo" in entry
            else None,
        )
        for entry in entries
    ]
    require_unique_ids([case.id for case in cases], cases_file)
    return cases


def to_persona_message(entry: str | dict[str, str], cases_file: Path) -> PersonaMessage:
    """Read one scripted message: plain text, or `{photo, shows, caption}`.

    Args:
        entry: The message as written in the cases file.
        cases_file: The file it came from, for the error message.

    Returns:
        The message.

    Raises:
        InvalidEvalCasesError: If it names an image that isn't there.
    """
    if isinstance(entry, str):
        return PersonaMessage(text=entry)
    photo = EvalPhoto(
        file_name=require_image(entry["photo"], cases_file), shows=entry["shows"]
    )
    return PersonaMessage(text=entry.get("caption", ""), photo=photo)


def load_persona_cases(cases_file: Path) -> PersonaCases:
    """Read the Persona rules and scripted conversations.

    Args:
        cases_file: YAML with `rules` (ID to what the judge checks) and
            `conversations` (each with `id`, `messages`, `rules`, optional
            `shared_photos`, each with `description` and `note`, and optional
            `photo_viewing`, true unless set to false).

    Returns:
        The rules and conversations.

    Raises:
        InvalidEvalCasesError: If a conversation names a rule that isn't
            defined or an image that isn't there, or two conversations share
            an ID.
    """
    content: dict[str, Any] = yaml.safe_load(cases_file.read_text())
    rules: dict[str, str] = content["rules"]
    conversations = [
        PersonaConversation(
            id=entry["id"],
            messages=[
                to_persona_message(message, cases_file) for message in entry["messages"]
            ],
            rules=entry["rules"],
            shared_photos=[
                EvalSharedPhoto(description=photo["description"], note=photo["note"])
                for photo in entry.get("shared_photos", [])
            ],
            photo_viewing=entry.get("photo_viewing", True),
        )
        for entry in content["conversations"]
    ]
    for conversation in conversations:
        unknown = [rule for rule in conversation.rules if rule not in rules]
        if unknown:
            raise InvalidEvalCasesError(
                f"{cases_file.name}: {conversation.id} names unknown rules: "
                + ", ".join(unknown)
            )
    require_unique_ids([conversation.id for conversation in conversations], cases_file)
    return PersonaCases(rules=rules, conversations=conversations)


def to_knowledge_details(entry: dict[str, str]) -> KnowledgeDetails:
    """Read a document's details as written in the cases file.

    Args:
        entry: A mapping with `title`, `source` and `tradition`.

    Returns:
        The details.
    """
    return KnowledgeDetails(
        title=entry["title"], source=entry["source"], tradition=entry["tradition"]
    )


def load_knowledge_cases(cases_file: Path) -> list[KnowledgeCase]:
    """Read the made-up teachings and how each document is changed.

    Args:
        cases_file: YAML list of cases; see `evals/README.md` for the shape.

    Returns:
        The cases, in the order listed.

    Raises:
        InvalidEvalCasesError: If two cases share an ID.
    """
    entries: list[dict[str, Any]] = yaml.safe_load(cases_file.read_text())
    cases = [
        KnowledgeCase(
            id=entry["id"],
            question=entry["question"],
            source_question=entry["source_question"],
            original_file_name=entry["original"]["file_name"],
            original_text=entry["original"]["text"],
            original_details=to_knowledge_details(entry["original"]),
            edited_text=entry["edited_text"],
            edited_details=to_knowledge_details(entry["edited_details"]),
            replacement_file_name=entry["replacement"]["file_name"],
            replacement_text=entry["replacement"]["text"],
        )
        for entry in entries
    ]
    require_unique_ids([case.id for case in cases], cases_file)
    return cases


def load_photo_description_cases(cases_file: Path) -> list[PhotoDescriptionCase]:
    """Read the test images and what their descriptions must leave out.

    Args:
        cases_file: YAML list of cases with `id`, `photo` and
            `must_leave_out`.

    Returns:
        The cases, in the order listed.

    Raises:
        InvalidEvalCasesError: If two cases share an ID or a case names an
            image that isn't there.
    """
    entries: list[dict[str, Any]] = yaml.safe_load(cases_file.read_text())
    cases = [
        PhotoDescriptionCase(
            id=entry["id"],
            photo=require_image(entry["photo"], cases_file),
            must_leave_out=entry["must_leave_out"],
        )
        for entry in entries
    ]
    require_unique_ids([case.id for case in cases], cases_file)
    return cases


def load_settings_cases(cases_file: Path) -> list[SettingsCase]:
    """Read the settings requests and the tools each must call.

    Args:
        cases_file: YAML list of cases with `id`, `message` and `tools`.

    Returns:
        The cases, in the order listed.

    Raises:
        InvalidEvalCasesError: If two cases share an ID.
    """
    entries: list[dict[str, Any]] = yaml.safe_load(cases_file.read_text())
    cases = [
        SettingsCase(id=entry["id"], message=entry["message"], tools=entry["tools"])
        for entry in entries
    ]
    require_unique_ids([case.id for case in cases], cases_file)
    return cases
