from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from companion.core.evals.case_shapes import InvalidFormError
from companion.core.models import (
    CuriositySensitivity,
    HowSure,
    MoveResult,
    MoveRole,
    ThreadReaction,
)


class InvalidEvalCaseError(InvalidFormError):
    """Raised when an Eval Case doesn't fit its Eval's case shape."""


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
    """A Day Summary from before the case starts.

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
        guess: What Zeph suspects but isn't sure of; None for a plain one.
        how_sure: How sure it is of the guess; None without one.
    """

    question: str
    why: str
    not_before_days_ago: int | None = 0
    sensitivity: CuriositySensitivity = CuriositySensitivity.LOW
    guess: str | None = None
    how_sure: HowSure | None = None


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
class EvalMoveOutcome:
    """A Move Outcome the person already has when the case starts.

    Attributes:
        move: The Move's name.
        role: Whether it led a reply or supported one.
        situation: What was going on.
        feeling: How the person felt.
        result: Whether it helped, didn't or was mixed.
        why: Why it went that way.
        days_ago: How many days before the case's time the Move was made.
    """

    move: str
    role: MoveRole
    situation: str
    feeling: str
    result: MoveResult
    why: str
    days_ago: int = 1


@dataclass(frozen=True)
class EvalMemory:
    """The made-up User Memory a case starts with.

    Attributes:
        portrait: The User Portrait; "" for none.
        items: Memory Items' contents by Memory Category name.
        summaries: Day Summaries from earlier Conversations.
        threads: Life Threads.
        curiosities: Waiting Curiosities.
        knowledge_documents: Knowledge Documents on the platform.
        move_outcomes: What helped the person before, and what didn't.
    """

    portrait: str = ""
    items: dict[str, list[str]] = field(default_factory=dict)
    summaries: list[EvalSummary] = field(default_factory=list)
    threads: list[EvalThread] = field(default_factory=list)
    curiosities: list[EvalCuriosity] = field(default_factory=list)
    knowledge_documents: list[EvalKnowledgeDocument] = field(default_factory=list)
    move_outcomes: list[EvalMoveOutcome] = field(default_factory=list)


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
    """What one Message's Understanding, Recall and Reply Plan should do.

    Each field left empty, or None, isn't checked. Code decides which step
    owns each one (see `check_steps`).

    Attributes:
        struggling: Whether the Understanding must read them as struggling.
        cause_known: Whether the Understanding must know why they feel so.
        looks_up_past: Whether the Understanding must ask to look up the past.
        feelings_said: Whether the Understanding must keep feelings they said
            in their own words; False means it keeps none as said.
        wants_said: The same for what they want from Zeph.
        read_formed: Whether the Reply Plan must form a Read.
        read_said: Whether the Reply Plan must have the reply say its Read.
        need: The Needs that may be picked.
        found: Life Threads, by title, the Companion must be reminded of.
        raised: Life Threads, by title, it must bring up.
        not_raised: Life Threads, by title, it must not bring up.
        curiosity_raised: Whether it must bring up a Curiosity.
        asked_why: Whether it must gently ask why they feel as they do.
        knowledge: Whether it must choose Knowledge documents to search.
        woven_in: Whether the reply must weave in the due Check-in.
        lead_move: The Moves the reply may lead with, by name.
        support_move: The Moves that may support it, by name.
        no_move: True if the reply must make no Move; False if it must lead
            with one.
        next_move: The Moves it may have in mind to make next, by name.
        rules: The IDs of the rules the Judge checks the reply against.
    """

    struggling: bool | None = None
    cause_known: bool | None = None
    looks_up_past: bool | None = None
    feelings_said: bool | None = None
    wants_said: bool | None = None
    read_formed: bool | None = None
    read_said: bool | None = None
    need: list[str] = field(default_factory=list)
    found: list[str] = field(default_factory=list)
    raised: list[str] = field(default_factory=list)
    not_raised: list[str] = field(default_factory=list)
    curiosity_raised: bool | None = None
    asked_why: bool | None = None
    knowledge: bool | None = None
    woven_in: bool | None = None
    lead_move: list[str] = field(default_factory=list)
    support_move: list[str] = field(default_factory=list)
    no_move: bool | None = None
    next_move: list[str] = field(default_factory=list)
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
        expect: What its Understanding, Recall and Reply Plan should do.
    """

    text: str
    expect: UnderstandingExpectations


@dataclass(frozen=True)
class EvalWebResult:
    """A made-up web result the Eval's search finds, so Research costs nothing.

    Attributes:
        title: The page's title.
        url: The page's address.
        text: What the page says; the search shows it and reading the page
            gives it.
    """

    title: str
    url: str
    text: str


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
        check_in_due: Whether the person has Check-ins on, with one due when
            the first Message is sent, so a reply may weave it in.
        web_search: Whether Web Search works for the person.
        web_results: What every web search finds; none when empty.
    """

    id: str
    now: datetime
    memory: EvalMemory
    earlier: list[EarlierLine]
    messages: list[UnderstandingMessage]
    rules: dict[str, str] = field(default_factory=dict)
    check_in_due: bool = False
    web_search: bool = True
    web_results: list[EvalWebResult] = field(default_factory=list)


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


def to_eval_curiosity(entry: dict[str, Any]) -> EvalCuriosity:
    """Read a waiting Curiosity as written in the case.

    Args:
        entry: A mapping with `question` and `why`, and optionally
            `not_before_days_ago`, `sensitivity`, `guess` and `how_sure`.

    Returns:
        The Curiosity; a guess without `how_sure` is low, and `how_sure` is
        dropped without a guess.
    """
    guess = entry.get("guess") or None
    return EvalCuriosity(
        question=entry["question"],
        why=entry["why"],
        not_before_days_ago=entry.get("not_before_days_ago", 0),
        sensitivity=CuriositySensitivity(entry.get("sensitivity") or "low"),
        guess=guess,
        how_sure=HowSure(entry.get("how_sure") or "low") if guess else None,
    )


def to_eval_memory(entry: dict[str, Any]) -> EvalMemory:
    """Read a case's made-up User Memory.

    Args:
        entry: A mapping with any of `portrait`, `items` (each
            `{category, contents}`), `summaries`, `threads`, `curiosities`,
            `knowledge_documents` and `move_outcomes`.

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
            to_eval_curiosity(curiosity) for curiosity in entry.get("curiosities") or []
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
        move_outcomes=[
            to_eval_move_outcome(outcome)
            for outcome in entry.get("move_outcomes") or []
        ],
    )


def to_eval_move_outcome(entry: dict[str, Any]) -> EvalMoveOutcome:
    """Read a Move Outcome as written in the case.

    Args:
        entry: `move`, `role`, `situation`, `feeling`, `result` and `why`,
            and optionally `days_ago`.

    Returns:
        The Move Outcome.
    """
    return EvalMoveOutcome(
        move=entry["move"].strip(),
        role=MoveRole(entry["role"]),
        situation=entry["situation"],
        feeling=entry["feeling"],
        result=MoveResult(entry["result"]),
        why=entry["why"],
        days_ago=entry.get("days_ago", 1),
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
            struggling=expect.get("struggling"),
            cause_known=expect.get("cause_known"),
            looks_up_past=expect.get("looks_up_past"),
            feelings_said=expect.get("feelings_said"),
            wants_said=expect.get("wants_said"),
            read_formed=expect.get("read_formed"),
            read_said=expect.get("read_said"),
            need=expect.get("need") or [],
            found=expect.get("found") or [],
            raised=expect.get("raised") or [],
            not_raised=expect.get("not_raised") or [],
            curiosity_raised=expect.get("curiosity_raised"),
            asked_why=expect.get("asked_why"),
            knowledge=expect.get("knowledge"),
            woven_in=expect.get("woven_in"),
            lead_move=expect.get("lead_move") or [],
            support_move=expect.get("support_move") or [],
            no_move=expect.get("no_move"),
            next_move=expect.get("next_move") or [],
            rules=expect.get("rules") or [],
        ),
    )


def to_eval_web_result(entry: dict[str, str]) -> EvalWebResult:
    """Read a made-up web result.

    Args:
        entry: `{title, url, text}`.

    Returns:
        The result.
    """
    return EvalWebResult(title=entry["title"], url=entry["url"], text=entry["text"])


def require_moves_or_no_move(case: UnderstandingCase) -> None:
    """Check no Message expects both a Move and no Move.

    Args:
        case: The case.

    Raises:
        InvalidEvalCaseError: If a Message expects no Move and names Moves.
    """
    problems = {
        f"messages.{number}.expect.no_move": "Expects no Move but names Moves "
        "it may make. Leave the Moves empty, or turn this off."
        for number, message in enumerate(case.messages)
        if message.expect.no_move is True
        and (message.expect.lead_move or message.expect.support_move)
    }
    if problems:
        raise InvalidEvalCaseError(
            f"{case.id} expects no_move and names Moves on the same Message",
            problems,
        )


def texts_besides_threads(case: UnderstandingCase) -> list[str]:
    """List every text in a case the Understanding may see, except its Threads.

    Args:
        case: The case.

    Returns:
        The Portrait, Memory Items, Summaries, Curiosities, Knowledge
        Documents, Move Outcomes, earlier messages and Messages.
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
        *(
            f"{outcome.situation} {outcome.feeling} {outcome.why}"
            for outcome in memory.move_outcomes
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
            optionally `memory`, `earlier` (each `{who, text}`),
            `check_in_due`, `web_search` and `web_results` (each `{title,
            url, text}`).

    Returns:
        The case.

    Raises:
        InvalidEvalCaseError: If it names an unknown rule or Life Thread,
            writes a Thread's title outside it, has a Thread raised in its
            Conversation but no earlier lines, expects a Check-in woven
            in or not with none due, or expects no Move and names Moves on
            the same Message.
    """
    case = UnderstandingCase(
        id=key,
        now=to_utc(content["now"]),
        memory=to_eval_memory(content.get("memory") or {}),
        earlier=[to_earlier_line(line) for line in content.get("earlier") or []],
        messages=[to_understanding_message(message) for message in content["messages"]],
        rules=read_rules(content),
        check_in_due=content.get("check_in_due") is True,
        web_search=content.get("web_search") is not False,
        web_results=[
            to_eval_web_result(entry) for entry in content.get("web_results") or []
        ],
    )
    require_checkable_names(case)
    require_moves_or_no_move(case)
    expects_woven_in = any(
        message.expect.woven_in is not None for message in case.messages
    )
    if expects_woven_in and not case.check_in_due:
        raise InvalidEvalCaseError(
            f"{key} expects a Check-in woven in or not, so needs check_in_due: true"
        )
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


@dataclass(frozen=True)
class MoveOutcomeMessage:
    """One message of a finished Conversation, with how Zeph read it.

    Attributes:
        from_person: True if the User sent it; False if Zeph did.
        text: What it says.
        need: The Need Zeph picked for it; "" on Zeph's messages.
        lead_move: The Move the reply led with; "" for none.
        support_move: The Move that supported it; "" for none.
        mood: How the User seemed; "" if unclear.
    """

    from_person: bool
    text: str
    need: str = ""
    lead_move: str = ""
    support_move: str = ""
    mood: str = ""


@dataclass(frozen=True)
class ExpectedMoveOutcome:
    """A Move Outcome the keeping step must write.

    Attributes:
        move: The Move's name.
        role: Whether it led a reply or supported one.
        result: The result it must have; None to not check it.
        rules: The IDs of the rules the Judge checks it against.
    """

    move: str
    role: MoveRole
    result: MoveResult | None
    rules: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        """Name it as the Case Result groups its checks.

        Returns:
            E.g. "Research (lead)".
        """
        return f"{self.move} ({self.role.value})"


@dataclass(frozen=True)
class MoveOutcomeCase:
    """A finished Conversation and the Move Outcomes it should leave.

    Attributes:
        id: The case's key.
        now: When the first message was sent, in UTC.
        messages: The Conversation, oldest first.
        outcomes: The Move Outcomes that must be kept.
        rules: What the Judge checks, by rule ID.
    """

    id: str
    now: datetime
    messages: list[MoveOutcomeMessage]
    outcomes: list[ExpectedMoveOutcome]
    rules: dict[str, str]


def to_move_outcome_message(entry: dict[str, Any]) -> MoveOutcomeMessage:
    """Read one message of a Move Outcome case.

    Args:
        entry: `who` and `text`, and optionally `need`, `lead_move`,
            `support_move` and `mood`.

    Returns:
        The message.
    """
    return MoveOutcomeMessage(
        from_person=entry["who"] == "person",
        text=entry["text"],
        need=(entry.get("need") or "").strip(),
        lead_move=(entry.get("lead_move") or "").strip(),
        support_move=(entry.get("support_move") or "").strip(),
        mood=(entry.get("mood") or "").strip(),
    )


def move_outcome_message_problems(
    messages: Sequence[MoveOutcomeMessage],
) -> dict[str, str]:
    """Find messages whose Need and Moves don't fit who sent them.

    Args:
        messages: The case's messages.

    Returns:
        What is wrong, by field path; empty when nothing is.
    """
    problems: dict[str, str] = {}
    for number, message in enumerate(messages):
        if message.from_person and not message.need:
            problems[f"messages.{number}.need"] = (
                "Write the Need Zeph picked for this message."
            )
        if not message.from_person:
            for name in ("need", "lead_move", "support_move", "mood"):
                if getattr(message, name):
                    problems[f"messages.{number}.{name}"] = (
                        "Only the User's messages have Moves, a Need or a mood."
                    )
    return problems


def move_outcome_expectation_problems(case: MoveOutcomeCase) -> dict[str, str]:
    """Find expected Move Outcomes no message made, or naming unknown rules.

    Args:
        case: The case.

    Returns:
        What is wrong, by field path; empty when nothing is.
    """
    made = {
        (name.lower(), role)
        for message in case.messages
        for name, role in (
            (message.lead_move, MoveRole.LEAD),
            (message.support_move, MoveRole.SUPPORT),
        )
        if name
    }
    problems: dict[str, str] = {}
    for number, outcome in enumerate(case.outcomes):
        if (outcome.move.lower(), outcome.role) not in made:
            problems[f"outcomes.{number}.move"] = (
                f"No message made {outcome.move} as the {outcome.role.value} Move."
            )
        unknown_rules = [rule for rule in outcome.rules if rule not in case.rules]
        if unknown_rules:
            problems[f"outcomes.{number}.rules"] = "No such rule below: " + ", ".join(
                unknown_rules
            )
    return problems


def read_move_outcome_case(key: str, content: dict[str, Any]) -> MoveOutcomeCase:
    """Read a Move Outcome case and check it can be checked.

    Args:
        key: The case's key.
        content: `now`, `messages` (each `{who, text}`, the User's also with
            `need`, `lead_move`, `support_move` and `mood`), `outcomes` (each
            `{move, role, result, rules}`) and `rules` (each `{id, check}`).

    Returns:
        The case.

    Raises:
        InvalidEvalCaseError: If a User's message has no Need, a Zeph message
            has Moves, a Need or a mood, or an expected Move Outcome names a
            Move no message made or an unknown rule.
    """
    case = MoveOutcomeCase(
        id=key,
        now=to_utc(content["now"]),
        messages=[to_move_outcome_message(entry) for entry in content["messages"]],
        outcomes=[
            ExpectedMoveOutcome(
                move=entry["move"].strip(),
                role=MoveRole(entry["role"]),
                result=MoveResult(entry["result"]) if entry.get("result") else None,
                rules=entry.get("rules") or [],
            )
            for entry in content.get("outcomes") or []
        ],
        rules=read_rules(content),
    )
    problems = move_outcome_message_problems(case.messages)
    problems.update(move_outcome_expectation_problems(case))
    if problems:
        raise InvalidEvalCaseError(
            f"{key} can't be checked: " + "; ".join(problems.values()), problems
        )
    return case
