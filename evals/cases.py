from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml

from companion.core.models import CuriositySensitivity, ThreadReaction

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


@dataclass(frozen=True)
class EvalSummary:
    """A Conversation Summary from before the case starts.

    Attributes:
        days_ago: How many days before the case's time it was written.
        summary: What the Conversation was about.
        mood: How the person seemed.
    """

    days_ago: int
    summary: str
    mood: str = ""


@dataclass(frozen=True)
class EvalThread:
    """A Life Thread the person already has when the case starts.

    Attributes:
        title: Its title, which checks name it by.
        story: What happened.
        people: The people or things in it.
        is_open: Whether it is still going on.
        updated_days_ago: How many days before the case's time it was last
            updated.
        raised_days_ago: How many days before the case's time Zeph last
            brought it up; None if it never did.
        reaction: How the person took it then; None if not known.
        raised_in_this_conversation: Whether Zeph already brought it up in
            the case's open Conversation.
    """

    title: str
    story: str
    people: list[str] = field(default_factory=list)
    is_open: bool = True
    updated_days_ago: int = 0
    raised_days_ago: int | None = None
    reaction: ThreadReaction | None = None
    raised_in_this_conversation: bool = False


@dataclass(frozen=True)
class EvalCuriosity:
    """A Curiosity waiting to be asked when the case starts.

    Attributes:
        question: What Zeph wants to ask.
        why: Why it wants to ask.
        not_before_days_ago: How many days before the case's time its day
            came (0 for today, below 0 for a day still to come); None for
            any time.
        sensitivity: How carefully it must be asked.
    """

    question: str
    why: str
    not_before_days_ago: int | None = 0
    sensitivity: CuriositySensitivity = CuriositySensitivity.LOW


@dataclass(frozen=True)
class EvalKnowledgeDocument:
    """A Knowledge Document an Admin uploads before the case starts.

    Attributes:
        title: Its title.
        source: Where it comes from.
        tradition: Its tradition.
        when_it_helps: The "when it helps" description the Admin sets.
        text: Its text.
    """

    title: str
    source: str
    tradition: str
    when_it_helps: str
    text: str


@dataclass(frozen=True)
class EvalMemory:
    """The made-up User Memory a case starts with.

    Attributes:
        portrait: The User Portrait; "" for none.
        items: Memory Items' contents by Memory Category name.
        summaries: Conversation Summaries from earlier Conversations.
        threads: Life Threads.
        curiosities: Waiting Curiosities.
        knowledge_documents: Knowledge Documents on the platform.
    """

    portrait: str = ""
    items: dict[str, list[str]] = field(default_factory=dict)
    summaries: list[EvalSummary] = field(default_factory=list)
    threads: list[EvalThread] = field(default_factory=list)
    curiosities: list[EvalCuriosity] = field(default_factory=list)
    knowledge_documents: list[EvalKnowledgeDocument] = field(default_factory=list)


@dataclass(frozen=True)
class EarlierLine:
    """A message already in the case's open Conversation.

    Attributes:
        from_person: True if the person sent it; False if Zeph did.
        text: What it says.
    """

    from_person: bool
    text: str


@dataclass(frozen=True)
class UnderstandingExpectations:
    """What one Message's Understanding and reply should do.

    Each field left empty, or None, isn't checked.

    Attributes:
        need: The Needs that may be picked.
        found: Life Threads, by title, the Companion must be reminded of.
        raised: Life Threads, by title, it must bring up.
        not_raised: Life Threads, by title, it must not bring up.
        curiosity_raised: Whether it must bring up a Curiosity.
        asked_why: Whether it must gently ask why they feel as they do.
        knowledge: Whether it must choose Knowledge documents to search.
        rules: The IDs of the rules the Judge checks the reply against.
    """

    need: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)
    raised: list[str] = field(default_factory=list)
    not_raised: list[str] = field(default_factory=list)
    curiosity_raised: bool | None = None
    asked_why: bool | None = None
    knowledge: bool | None = None
    rules: list[str] = field(default_factory=list)

    @property
    def thread_titles(self) -> list[str]:
        """List every Life Thread the expectations name.

        Returns:
            The titles in `found`, `raised` and `not_raised`.
        """
        return [*self.found, *self.raised, *self.not_raised]


@dataclass(frozen=True)
class UnderstandingMessage:
    """One Message the person sends in an Understanding case.

    Attributes:
        text: What it says.
        expect: What its Understanding and reply should do.
    """

    text: str
    expect: UnderstandingExpectations


@dataclass(frozen=True)
class UnderstandingCase:
    """A made-up User Memory and Conversation, then Messages to check.

    Attributes:
        id: A short name for the case.
        now: When the first Message is sent, in UTC.
        memory: The User Memory the person has.
        earlier: Messages already in the open Conversation, oldest first.
        messages: What the person sends, in order.
    """

    id: str
    now: datetime
    memory: EvalMemory
    earlier: list[EarlierLine]
    messages: list[UnderstandingMessage]


@dataclass(frozen=True)
class UnderstandingCases:
    """The Judge's rules and the Understanding cases.

    Attributes:
        rules: Each rule's ID and what the Judge checks.
        cases: The cases.
    """

    rules: dict[str, str]
    cases: list[UnderstandingCase]


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


def to_utc(value: Any) -> datetime:
    """Read a time from a cases file as UTC.

    Args:
        value: The time, as YAML read it, e.g. 2026-11-13T18:30:00.

    Returns:
        The time in UTC; a time with no zone is taken as UTC.
    """
    moment = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def to_eval_thread(entry: dict[str, Any]) -> EvalThread:
    """Read a Life Thread as written in the cases file.

    Args:
        entry: A mapping with `title` and `story`, and optionally `people`,
            `open`, `updated_days_ago`, `raised_days_ago`, `reaction` and
            `raised_in_this_conversation`.

    Returns:
        The Thread.

    Raises:
        ValueError: If its reaction isn't one Threads can have.
    """
    reaction = entry.get("reaction")
    return EvalThread(
        title=entry["title"],
        story=entry["story"],
        people=entry.get("people", []),
        is_open=entry.get("open", True),
        updated_days_ago=entry.get("updated_days_ago", 0),
        raised_days_ago=entry.get("raised_days_ago"),
        reaction=ThreadReaction(reaction) if reaction else None,
        raised_in_this_conversation=entry.get("raised_in_this_conversation", False),
    )


def to_eval_memory(entry: dict[str, Any]) -> EvalMemory:
    """Read a case's made-up User Memory as written in the cases file.

    Args:
        entry: A mapping with any of `portrait`, `items`, `summaries`,
            `threads`, `curiosities` and `knowledge_documents`.

    Returns:
        The memory.

    Raises:
        ValueError: If a Thread's reaction or a Curiosity's sensitivity
            isn't a known one.
    """
    return EvalMemory(
        portrait=entry.get("portrait", ""),
        items=entry.get("items", {}),
        summaries=[
            EvalSummary(
                days_ago=summary["days_ago"],
                summary=summary["summary"],
                mood=summary.get("mood", ""),
            )
            for summary in entry.get("summaries", [])
        ],
        threads=[to_eval_thread(thread) for thread in entry.get("threads", [])],
        curiosities=[
            EvalCuriosity(
                question=curiosity["question"],
                why=curiosity["why"],
                not_before_days_ago=curiosity.get("not_before_days_ago", 0),
                sensitivity=CuriositySensitivity(curiosity.get("sensitivity", "low")),
            )
            for curiosity in entry.get("curiosities", [])
        ],
        knowledge_documents=[
            EvalKnowledgeDocument(
                title=document["title"],
                source=document["source"],
                tradition=document["tradition"],
                when_it_helps=document["when_it_helps"],
                text=document["text"],
            )
            for document in entry.get("knowledge_documents", [])
        ],
    )


def to_earlier_line(entry: dict[str, str]) -> EarlierLine:
    """Read a message already in the open Conversation.

    Args:
        entry: `{person: <text>}` or `{zeph: <text>}`.

    Returns:
        The message.
    """
    if "person" in entry:
        return EarlierLine(from_person=True, text=entry["person"])
    return EarlierLine(from_person=False, text=entry["zeph"])


def to_understanding_message(entry: dict[str, Any]) -> UnderstandingMessage:
    """Read one Message of an Understanding case and what it should do.

    Args:
        entry: A mapping with `text` and optionally `expect`.

    Returns:
        The Message.
    """
    expect = entry.get("expect", {})
    return UnderstandingMessage(
        text=entry["text"],
        expect=UnderstandingExpectations(
            need=expect.get("need", []),
            found=expect.get("found", []),
            raised=expect.get("raised", []),
            not_raised=expect.get("not_raised", []),
            curiosity_raised=expect.get("curiosity_raised"),
            asked_why=expect.get("asked_why"),
            knowledge=expect.get("knowledge"),
            rules=expect.get("rules", []),
        ),
    )


def texts_besides_threads(case: UnderstandingCase) -> list[str]:
    """List every text in a case the Understanding may see, except its Threads.

    Args:
        case: The case.

    Returns:
        The Portrait, Memory Items, Summaries, Curiosities, Knowledge
        Documents, earlier messages and Messages.
    """
    memory = case.memory
    return [
        memory.portrait,
        *(content for contents in memory.items.values() for content in contents),
        *(summary.summary for summary in memory.summaries),
        *(f"{item.question} {item.why}" for item in memory.curiosities),
        *(
            f"{document.title} {document.when_it_helps}"
            for document in memory.knowledge_documents
        ),
        *(line.text for line in case.earlier),
        *(message.text for message in case.messages),
    ]


def require_checkable_names(
    case: UnderstandingCase, rules: dict[str, str], cases_file: Path
) -> None:
    """Check a case names only rules and Life Threads it can be checked by.

    A Thread's title may appear only in the Thread itself, so "found"
    passes only when the Companion was reminded of it.

    Args:
        case: The case.
        rules: The rules the cases file defines.
        cases_file: The file it came from, for the error message.

    Raises:
        InvalidEvalCasesError: If it names an unknown rule or Thread, writes
            a Thread's title elsewhere, or has a Thread raised in its
            Conversation but no earlier lines.
    """
    titles = {thread.title for thread in case.memory.threads}
    for message in case.messages:
        unknown_rules = [rule for rule in message.expect.rules if rule not in rules]
        unknown_threads = [
            title for title in message.expect.thread_titles if title not in titles
        ]
        if unknown_rules or unknown_threads:
            raise InvalidEvalCasesError(
                f"{cases_file.name}: {case.id} names unknown rules or Threads: "
                + ", ".join(unknown_rules + unknown_threads)
            )
    other_texts = texts_besides_threads(case)
    written_elsewhere = [
        title for title in titles if any(title in text for text in other_texts)
    ]
    if written_elsewhere:
        raise InvalidEvalCasesError(
            f"{cases_file.name}: {case.id} writes Thread titles outside the "
            "Threads: " + ", ".join(written_elsewhere)
        )
    raised_here = any(
        thread.raised_in_this_conversation for thread in case.memory.threads
    )
    if raised_here and not case.earlier:
        raise InvalidEvalCasesError(
            f"{cases_file.name}: {case.id} has a Thread raised in this "
            "Conversation, so it needs earlier lines"
        )


def load_understanding_cases(cases_file: Path) -> UnderstandingCases:
    """Read the Judge's rules and the Understanding cases.

    Args:
        cases_file: YAML with `now` (the default time cases start), `rules`
            (ID to what the Judge checks) and `cases`; see the file's top
            for each case's shape.

    Returns:
        The rules and cases.

    Raises:
        InvalidEvalCasesError: If a case names an unknown rule or Life
            Thread, writes a Thread's title outside it, has a Thread raised
            in its Conversation but no earlier lines, or two cases share an
            ID.
    """
    content: dict[str, Any] = yaml.safe_load(cases_file.read_text())
    rules: dict[str, str] = content["rules"]
    cases = [
        UnderstandingCase(
            id=entry["id"],
            now=to_utc(entry.get("now", content["now"])),
            memory=to_eval_memory(entry.get("memory", {})),
            earlier=[to_earlier_line(line) for line in entry.get("earlier", [])],
            messages=[
                to_understanding_message(message) for message in entry["messages"]
            ],
        )
        for entry in content["cases"]
    ]
    for case in cases:
        require_checkable_names(case, rules, cases_file)
    require_unique_ids([case.id for case in cases], cases_file)
    return UnderstandingCases(rules=rules, cases=cases)
