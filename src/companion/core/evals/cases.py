from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from companion.core.errors import InvalidError
from companion.core.models import CuriositySensitivity, ThreadReaction


class InvalidEvalCaseError(InvalidError):
    """Raised when an Eval Case doesn't fit its Eval's case shape.

    Attributes:
        problems: What is wrong, by the path of the field it is in, e.g.
            `messages.0.text`; "" for the case as a whole.
    """

    def __init__(self, message: str, problems: Mapping[str, str] | None = None):
        """Set up the error.

        Args:
            message: What is wrong, in one line.
            problems: What is wrong per field; when None, the message is the
                case's one problem.
        """
        super().__init__(message)
        self.problems = dict(problems) if problems is not None else {"": message}

    def field_errors(self) -> dict[str, str]:
        """Give what is wrong per field, to show beside each field.

        Returns:
            The message for each field's path.
        """
        return self.problems


class SafeguardCaseKind(StrEnum):
    """How a Safeguard case is labelled."""

    CLEAR_CRISIS = "clear_crisis"
    SUBTLE_CRISIS = "subtle_crisis"
    FALSE_ALARM = "false_alarm"


@dataclass(frozen=True)
class SafeguardCase:
    """A labelled message for the Safeguard to classify.

    Attributes:
        id: The case's key.
        kind: Whether it is a clear crisis, a subtle crisis or a false alarm.
        message: The message to classify, or the photo's caption; "" for a
            photo with none.
        earlier: Messages the person sent before it, for context.
        photo: The file name of a test image sent as a photo with the
            message as its caption; None for a text message.
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
        file_name: The image's file name.
        shows: What is really in it, as the Judge is told.
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
        id: The case's key.
        messages: What the person sends, in order.
        rules: Each rule its replies are judged against, by ID, and what the
            Judge checks.
        shared_photos: The Shared Photos the person has before it starts.
        photo_viewing: Whether the person has Photo Viewing on.
    """

    id: str
    messages: list[PersonaMessage]
    rules: dict[str, str]
    shared_photos: list[EvalSharedPhoto] = field(default_factory=list)
    photo_viewing: bool = True


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
        """Write the details as one line for the Judge.

        Returns:
            The details, e.g. "title “Night”, source Brother Elk, tradition
            Coast".
        """
        return f"title “{self.title}”, source {self.source}, tradition {self.tradition}"


@dataclass(frozen=True)
class KnowledgeCase:
    """A made-up teaching, and the ways an Admin changes its document.

    Attributes:
        id: The case's key.
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
        id: The case's key.
        photo: The image's file name.
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
        id: The case's key.
        message: What the User sends.
        tools: The settings tools the reply must call; empty when no setting
            may change.
        memories: The Memory Items the User has before the message, by
            Memory Category name, beyond those onboarding saves.
        forgotten: Which of those Memory Items must be gone afterwards;
            every other one must stay.
    """

    id: str
    message: str
    tools: list[str]
    memories: dict[str, list[str]] = field(default_factory=dict)
    forgotten: list[str] = field(default_factory=list)

    @property
    def memory_item_contents(self) -> list[str]:
        """List the contents of the case's Memory Items, whatever their category.

        Returns:
            The contents, in the order the case lists them.
        """
        return [content for items in self.memories.values() for content in items]


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
        id: The case's key.
        now: When the first Message is sent, in UTC.
        memory: The User Memory the person has.
        earlier: Messages already in the open Conversation, oldest first.
        messages: What the person sends, in order.
        rules: Each rule its Messages name, by ID, and what the Judge checks.
    """

    id: str
    now: datetime
    memory: EvalMemory
    earlier: list[EarlierLine]
    messages: list[UnderstandingMessage]
    rules: dict[str, str] = field(default_factory=dict)


def read_safeguard_case(key: str, content: dict[str, Any]) -> SafeguardCase:
    """Read a Safeguard case.

    Args:
        key: The case's key.
        content: `kind`, and a `message`, a `photo` or both, and optionally
            `earlier`.

    Returns:
        The case.

    Raises:
        InvalidEvalCaseError: If it has neither a message nor a photo.
    """
    case = SafeguardCase(
        id=key,
        kind=SafeguardCaseKind(content["kind"]),
        message=content.get("message") or "",
        earlier=content.get("earlier") or [],
        photo=content.get("photo") or None,
    )
    if not case.message.strip() and case.photo is None:
        raise InvalidEvalCaseError(
            f"{key} needs a message or a photo",
            {"message": "Write a message, or upload a photo."},
        )
    return case


def read_rules(content: dict[str, Any]) -> dict[str, str]:
    """Read a case's rules, written as a list of `{id, check}`.

    Args:
        content: The case's content.

    Returns:
        What the Judge checks, by rule ID.
    """
    return {rule["id"]: rule["check"] for rule in content.get("rules") or []}


def to_persona_message(entry: dict[str, Any]) -> PersonaMessage:
    """Read one scripted message: `{text, photo, shows}`.

    Args:
        entry: The message as written in the case; `photo` empty for text.

    Returns:
        The message.
    """
    photo_name = entry.get("photo")
    photo = (
        EvalPhoto(file_name=photo_name, shows=entry.get("shows") or "")
        if photo_name
        else None
    )
    return PersonaMessage(text=entry.get("text") or "", photo=photo)


def require_persona_messages_complete(conversation: PersonaConversation) -> None:
    """Check each message has text or a photo, and each photo what it shows.

    Args:
        conversation: The conversation.

    Raises:
        InvalidEvalCaseError: If a message is empty or a photo doesn't say
            what it shows.
    """
    problems: dict[str, str] = {}
    for number, message in enumerate(conversation.messages):
        if message.photo is None and not message.text.strip():
            problems[f"messages.{number}.text"] = "Write the text, or upload a photo."
        if message.photo is not None and not message.photo.shows.strip():
            problems[f"messages.{number}.shows"] = "Say what the photo shows."
    if problems:
        raise InvalidEvalCaseError(
            f"{conversation.id} has incomplete messages", problems
        )


def read_persona_case(key: str, content: dict[str, Any]) -> PersonaConversation:
    """Read a Persona case: a scripted conversation and its rules.

    Args:
        key: The case's key.
        content: `messages` (each `{text, photo, shows}`), `rules` (each
            `{id, check}`), optional `shared_photos`, each with
            `description` and `note`, and optional `photo_viewing`, true
            unless set to false.

    Returns:
        The conversation.

    Raises:
        InvalidEvalCaseError: If a message is empty or a photo doesn't say
            what it shows.
    """
    photo_viewing = content.get("photo_viewing")
    conversation = PersonaConversation(
        id=key,
        messages=[to_persona_message(message) for message in content["messages"]],
        rules=read_rules(content),
        shared_photos=[
            EvalSharedPhoto(description=photo["description"], note=photo["note"])
            for photo in content.get("shared_photos") or []
        ],
        photo_viewing=True if photo_viewing is None else photo_viewing,
    )
    require_persona_messages_complete(conversation)
    return conversation


def to_knowledge_details(entry: dict[str, str]) -> KnowledgeDetails:
    """Read a document's details as written in the case.

    Args:
        entry: A mapping with `title`, `source` and `tradition`.

    Returns:
        The details.
    """
    return KnowledgeDetails(
        title=entry["title"], source=entry["source"], tradition=entry["tradition"]
    )


def read_knowledge_case(key: str, content: dict[str, Any]) -> KnowledgeCase:
    """Read a Knowledge case: a made-up teaching and how its document changes.

    Args:
        key: The case's key.
        content: `question`, `source_question`, `original` (with
            `file_name`, `text` and the details), `edited_text`,
            `edited_details` and `replacement` (with `file_name` and `text`).

    Returns:
        The case.
    """
    return KnowledgeCase(
        id=key,
        question=content["question"],
        source_question=content["source_question"],
        original_file_name=content["original"]["file_name"],
        original_text=content["original"]["text"],
        original_details=to_knowledge_details(content["original"]),
        edited_text=content["edited_text"],
        edited_details=to_knowledge_details(content["edited_details"]),
        replacement_file_name=content["replacement"]["file_name"],
        replacement_text=content["replacement"]["text"],
    )


def read_photo_description_case(
    key: str, content: dict[str, Any]
) -> PhotoDescriptionCase:
    """Read a Photo description case.

    Args:
        key: The case's key.
        content: `photo` and `must_leave_out`.

    Returns:
        The case.
    """
    return PhotoDescriptionCase(
        id=key, photo=content["photo"], must_leave_out=content["must_leave_out"]
    )


def read_settings_case(key: str, content: dict[str, Any]) -> SettingsCase:
    """Read a Settings case.

    Args:
        key: The case's key.
        content: `message` and `tools`, and optional `memories` (each
            `{category, contents}`) and `forgotten` (which of them must be
            gone afterwards).

    Returns:
        The case.

    Raises:
        InvalidEvalCaseError: If `forgotten` names a Memory Item the case
            doesn't have.
    """
    case = SettingsCase(
        id=key,
        message=content["message"],
        tools=content.get("tools") or [],
        memories=read_memory_items(content.get("memories")),
        forgotten=content.get("forgotten") or [],
    )
    unknown = [item for item in case.forgotten if item not in case.memory_item_contents]
    if unknown:
        message = "Memory Items it doesn't have: " + ", ".join(unknown)
        raise InvalidEvalCaseError(
            f"{key} forgets {message}", {"forgotten": f"Forgets {message}."}
        )
    return case


def read_memory_items(entries: list[dict[str, Any]] | None) -> dict[str, list[str]]:
    """Read Memory Items, written as a list of `{category, contents}`.

    Args:
        entries: The list; None for none.

    Returns:
        The Memory Items' contents by Memory Category name.
    """
    return {entry["category"]: entry["contents"] for entry in entries or []}


def to_utc(value: Any) -> datetime:
    """Read a case's time as UTC.

    Args:
        value: The time, as a datetime or ISO text, e.g. 2026-11-13T18:30:00.

    Returns:
        The time in UTC; a time with no zone is taken as UTC.
    """
    moment = value if isinstance(value, datetime) else datetime.fromisoformat(value)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=UTC)
    return moment.astimezone(UTC)


def to_eval_thread(entry: dict[str, Any]) -> EvalThread:
    """Read a Life Thread as written in the case.

    Args:
        entry: A mapping with `title` and `story`, and optionally `people`,
            `open`, `updated_days_ago`, `raised_days_ago`, `reaction` and
            `raised_in_this_conversation`.

    Returns:
        The Thread.
    """
    reaction = entry.get("reaction")
    is_open = entry.get("open")
    return EvalThread(
        title=entry["title"],
        story=entry["story"],
        people=entry.get("people") or [],
        is_open=True if is_open is None else is_open,
        updated_days_ago=entry.get("updated_days_ago") or 0,
        raised_days_ago=entry.get("raised_days_ago"),
        reaction=ThreadReaction(reaction) if reaction else None,
        raised_in_this_conversation=bool(entry.get("raised_in_this_conversation")),
    )


def to_eval_memory(entry: dict[str, Any]) -> EvalMemory:
    """Read a case's made-up User Memory.

    Args:
        entry: A mapping with any of `portrait`, `items` (each
            `{category, contents}`), `summaries`, `threads`, `curiosities`
            and `knowledge_documents`.

    Returns:
        The memory.
    """
    return EvalMemory(
        portrait=entry.get("portrait") or "",
        items=read_memory_items(entry.get("items")),
        summaries=[
            EvalSummary(
                days_ago=summary["days_ago"],
                summary=summary["summary"],
                mood=summary.get("mood") or "",
            )
            for summary in entry.get("summaries") or []
        ],
        threads=[to_eval_thread(thread) for thread in entry.get("threads") or []],
        curiosities=[
            EvalCuriosity(
                question=curiosity["question"],
                why=curiosity["why"],
                not_before_days_ago=curiosity.get("not_before_days_ago", 0),
                sensitivity=CuriositySensitivity(curiosity.get("sensitivity") or "low"),
            )
            for curiosity in entry.get("curiosities") or []
        ],
        knowledge_documents=[
            EvalKnowledgeDocument(
                title=document["title"],
                source=document["source"],
                tradition=document["tradition"],
                when_it_helps=document["when_it_helps"],
                text=document["text"],
            )
            for document in entry.get("knowledge_documents") or []
        ],
    )


def to_earlier_line(entry: dict[str, str]) -> EarlierLine:
    """Read a message already in the open Conversation.

    Args:
        entry: `{who, text}`, `who` being `person` or `zeph`.

    Returns:
        The message.
    """
    return EarlierLine(from_person=entry["who"] == "person", text=entry["text"])


def to_understanding_message(entry: dict[str, Any]) -> UnderstandingMessage:
    """Read one Message of an Understanding case and what it should do.

    Args:
        entry: A mapping with `text` and optionally `expect`.

    Returns:
        The Message.
    """
    expect = entry.get("expect") or {}
    return UnderstandingMessage(
        text=entry["text"],
        expect=UnderstandingExpectations(
            need=expect.get("need") or [],
            found=expect.get("found") or [],
            raised=expect.get("raised") or [],
            not_raised=expect.get("not_raised") or [],
            curiosity_raised=expect.get("curiosity_raised"),
            asked_why=expect.get("asked_why"),
            knowledge=expect.get("knowledge"),
            rules=expect.get("rules") or [],
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


def require_checkable_names(case: UnderstandingCase) -> None:
    """Check a case names only rules and Life Threads it can be checked by.

    A Thread's title may appear only in the Thread itself, so "found"
    passes only when the Companion was reminded of it.

    Args:
        case: The case.

    Raises:
        InvalidEvalCaseError: If it names an unknown rule or Thread, writes
            a Thread's title elsewhere, or has a Thread raised in its
            Conversation but no earlier lines.
    """
    titles = {thread.title for thread in case.memory.threads}
    problems: dict[str, str] = {}
    unknown_names: list[str] = []
    for number, message in enumerate(case.messages):
        expect_path = f"messages.{number}.expect"
        unknown_rules = [
            rule for rule in message.expect.rules if rule not in case.rules
        ]
        if unknown_rules:
            problems[f"{expect_path}.rules"] = "No such rule below: " + ", ".join(
                unknown_rules
            )
        unknown_names.extend(unknown_rules)
        for name in ("found", "raised", "not_raised"):
            unknown_threads = [
                title for title in getattr(message.expect, name) if title not in titles
            ]
            if unknown_threads:
                problems[f"{expect_path}.{name}"] = (
                    "No Life Thread has this title: " + ", ".join(unknown_threads)
                )
            unknown_names.extend(unknown_threads)
    if problems:
        raise InvalidEvalCaseError(
            f"{case.id} names unknown rules or Threads: " + ", ".join(unknown_names),
            problems,
        )
    other_texts = texts_besides_threads(case)
    written_elsewhere = [
        title for title in titles if any(title in text for text in other_texts)
    ]
    if written_elsewhere:
        titles_written = ", ".join(written_elsewhere)
        raise InvalidEvalCaseError(
            f"{case.id} writes Thread titles outside the Threads: {titles_written}",
            {
                "memory.threads": f"The title {titles_written} is written elsewhere "
                "in the case too. Write it only in its Thread, or the checks can't "
                "tell whether Zeph was reminded of it."
            },
        )
    raised_here = any(
        thread.raised_in_this_conversation for thread in case.memory.threads
    )
    if raised_here and not case.earlier:
        raise InvalidEvalCaseError(
            f"{case.id} has a Thread raised in this Conversation, so it needs "
            "earlier lines",
            {
                "earlier": "A Thread was raised in this Conversation, so add the "
                "earlier messages."
            },
        )


def read_understanding_case(key: str, content: dict[str, Any]) -> UnderstandingCase:
    """Read an Understanding case and check it can be checked.

    Args:
        key: The case's key.
        content: `now`, `messages`, `rules` (each `{id, check}`) and
            optionally `memory` and `earlier` (each `{who, text}`).

    Returns:
        The case.

    Raises:
        InvalidEvalCaseError: If it names an unknown rule or Life Thread,
            writes a Thread's title outside it, or has a Thread raised in
            its Conversation but no earlier lines.
    """
    case = UnderstandingCase(
        id=key,
        now=to_utc(content["now"]),
        memory=to_eval_memory(content.get("memory") or {}),
        earlier=[to_earlier_line(line) for line in content.get("earlier") or []],
        messages=[to_understanding_message(message) for message in content["messages"]],
        rules=read_rules(content),
    )
    require_checkable_names(case)
    return case


def require_unique_keys(keys: Sequence[str]) -> None:
    """Check that no two cases share a key.

    Args:
        keys: The cases' keys.

    Raises:
        InvalidEvalCaseError: If a key is used twice.
    """
    seen: set[str] = set()
    for key in keys:
        if key in seen:
            raise InvalidEvalCaseError(f"The case key {key} is used twice")
        seen.add(key)
