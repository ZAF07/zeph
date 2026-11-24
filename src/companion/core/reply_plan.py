import json
import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from typing import Any
from uuid import UUID, uuid4

from companion.core.curiosities import (
    DueCuriosities,
    NumberedCuriosity,
    describe_curiosity_treatments,
    describe_due_curiosities,
    format_curiosities_for_reply,
    offered_under,
    why_none_asked,
)
from companion.core.life_threads import (
    RemindedThread,
    describe_reminded_threads,
    format_threads_for_reply,
    format_threads_left_alone,
)
from companion.core.memory_retrieval import SavedMemory, summary_line
from companion.core.model_call_log import ModelCallLog
from companion.core.models import (
    BringUpWay,
    ChatLine,
    ChatRole,
    CheckInKind,
    ChosenCheckIn,
    ChosenKnowledgeDocument,
    CuriosityToRaise,
    Feature,
    KnowledgeDocument,
    KnowledgeLookup,
    KnowledgeStatus,
    ModelStep,
    MoodIntensity,
    Move,
    MoveOutcome,
    Need,
    PatternPicked,
    ReplyPlan,
    ReplyPlanForm,
    ReplyPlanShape,
    ThreadLeftAlone,
    ThreadToBringUp,
    Understanding,
    UnderstandingForm,
    UserSnapshot,
)
from companion.core.move_outcomes import describe_move_outcome
from companion.core.past_day import PastDayTool
from companion.core.patterns import RemindedPattern, describe_patterns_in_mind
from companion.core.platform_settings import (
    HOME_GOALS_MEMORY_CATEGORY,
    PERSONA_OUTLOOK,
    REPLY_ASK_WHY_NOTE,
    REPLY_PLAN_MODEL,
    REPLY_PLAN_PROMPT,
    REPLY_PLAN_THINKING,
)
from companion.core.ports import Clock, Repositories
from companion.core.recent_messages import RecentMessages, describe_recent_messages
from companion.core.reply_tools import ReplyGuidance
from companion.core.understanding import (
    describe_understanding,
    format_local_time,
    newest_incoming_message_id,
    read_form_text,
    read_text_list,
)
from companion.core.usage import UsageRecordingChatModel
from companion.core.web_search import web_search_limit_used_up
from companion.core.woven_check_ins import WovenCheckIn

logger = logging.getLogger(__name__)

MOST_CURIOSITIES_PER_REPLY = 1
ASKS_WHY_INSTEAD = "The reply asks why they feel as they do instead."
NO_REPLY_PLAN = "The Reply Plan couldn't be made."


@dataclass(frozen=True)
class PickedMoves:
    """The Moves a reply makes, once checked against what its Need allows.

    Attributes:
        lead: The Move the reply leads with; None for none.
        support: The Move that supports it; None for none.
        next: The Move the Companion means to make later in the
            Conversation; None for none.
    """

    lead: Move | None = None
    support: Move | None = None
    next: Move | None = None

    @property
    def lead_name(self) -> str | None:
        """The lead Move's name; None for none."""
        return self.lead.name if self.lead else None

    @property
    def support_name(self) -> str | None:
        """The supporting Move's name; None for none."""
        return self.support.name if self.support else None

    @property
    def next_name(self) -> str | None:
        """The next Move's name; None for none."""
        return self.next.name if self.next else None

    @property
    def asks_a_question(self) -> bool:
        """Whether the lead or supporting Move asks the User a question."""
        return any(move.asks_a_question for move in (self.lead, self.support) if move)


@dataclass(frozen=True)
class PlannedReply:
    """A Message's saved Reply Plan, and what it tells the reply.

    Attributes:
        reply_plan: The Reply Plan, as saved.
        reply_guidance: What it adds to the reply's instructions, by
            priority: the Life Threads to leave alone; the Need's "how to
            reply", the Moves' "how to do it", the guidance and mood, the
            "ask why" note when it applies, the Life Threads to bring up and
            the Curiosity to ask.
        asks_a_question: Whether the reply already asks the User a question:
            through a Move that asks one, asking why or a Curiosity.
        may_send_photo: Whether the reply may send one of the User's Shared
            Photos.
        check_in: The due Check-in it chose to offer the reply; None for
            none.
    """

    reply_plan: ReplyPlan
    reply_guidance: ReplyGuidance
    asks_a_question: bool = False
    may_send_photo: bool = True
    check_in: WovenCheckIn | None = None


def format_earlier_reply_plan(reply_plan: ReplyPlan) -> str:
    """Write one earlier Reply Plan as the next Reply Plan reads it.

    Args:
        reply_plan: The earlier Reply Plan.

    Returns:
        E.g. "- Where we were: venting, just started. Read (not said): It's
        less the work than the proving. Need: Be heard; lead Move: Mirror;
        supporting Move: none; asked why: no. Let them vent. Next Move in
        mind: Plan steps, once they've let it out."
    """
    asked_why = "yes" if reply_plan.asked_why else "no"
    form = reply_plan.form
    parts = ["-"]
    if form.where_we_are:
        parts.append(f"Where we were: {form.where_we_are}.")
    if form.read:
        said = "said" if form.say_read else "not said"
        parts.append(f"Read ({said}): {form.read}")
    parts.append(
        f"Need: {reply_plan.need}; lead Move: {reply_plan.lead_move or 'none'}; "
        f"supporting Move: {reply_plan.support_move or 'none'}; "
        f"asked why: {asked_why}."
    )
    if form.guidance:
        parts.append(form.guidance)
    if reply_plan.next_move:
        why = f", {reply_plan.next_move_why}" if reply_plan.next_move_why else ""
        parts.append(f"Next Move in mind: {reply_plan.next_move}{why}.")
    return " ".join(parts)


def allowed_moves(need: Need, moves: Sequence[Move]) -> list[Move]:
    """List the Moves a Need allows: every Move it doesn't rule out.

    Args:
        need: The Need.
        moves: Every Move, in order.

    Returns:
        The allowed Moves, in order.
    """
    return [move for move in moves if move.id not in need.ruled_out_move_ids]


def moves_that_work(moves: Sequence[Move], working: set[Feature]) -> list[Move]:
    """List the Moves the Companion can make for the User right now.

    A Move that needs a Feature is left out unless that Feature works.

    Args:
        moves: Every Move, in order.
        working: The Features that work for the User right now.

    Returns:
        The Moves it can make, in order.
    """
    return [
        move
        for move in moves
        if move.needed_feature is None or move.needed_feature in working
    ]


def moves_without_repeat_questions(
    moves: Sequence[Move], earlier: Sequence[ReplyPlan]
) -> list[Move]:
    """List the Moves, leaving out a question-asking one made in the previous reply.

    A Move that asks a question is left out when the previous Reply Plan in
    the Conversation made it, as lead or supporting, so it is never made in
    two replies in a row.

    Args:
        moves: Every Move, in order.
        earlier: This Conversation's earlier Reply Plans, oldest first.

    Returns:
        The Moves still offered, in order.
    """
    if not earlier:
        return list(moves)
    previous = earlier[-1]
    made_last_time = {
        name.lower() for name in (previous.lead_move, previous.support_move) if name
    }
    return [
        move
        for move in moves
        if not (move.asks_a_question and move.name.lower() in made_last_time)
    ]


def format_allowed_moves(need: Need, moves: Sequence[Move]) -> str:
    """Write which Moves a Need allows, as the Reply Plan reads it.

    Args:
        need: The Need.
        moves: Every Move, in order.

    Returns:
        E.g. "- Be heard: Calm, Ground, Mirror", or "- Get it done: none".
    """
    names = ", ".join(move.name for move in allowed_moves(need, moves))
    return f"- {need.name}: {names or 'none'}"


def number_knowledge_documents(
    documents: Sequence[KnowledgeDocument],
) -> dict[int, KnowledgeDocument]:
    """Number the Knowledge documents the Reply Plan may choose from.

    The numbers hold for one Reply Plan call only, since the documents can
    change between calls.

    Args:
        documents: The documents, in the order they are listed.

    Returns:
        The documents by number, from 1.
    """
    return dict(enumerate(documents, start=1))


def format_knowledge_document(number: int, document: KnowledgeDocument) -> str:
    """Write one Knowledge document as the Reply Plan reads it.

    Args:
        number: The number the Reply Plan chooses it by.
        document: The document.

    Returns:
        E.g. "[1] “On the breath” (Owner's notes, Mindfulness): When their
        attention keeps drifting."
    """
    line = f"[{number}] {document.title_with_source}"
    return f"{line}: {document.when_it_helps}" if document.when_it_helps else line


def describe_message_for_reply_plan(
    snapshot: UserSnapshot,
    understanding: UnderstandingForm,
    needs: Sequence[Need],
    moves: Sequence[Move],
    saved: SavedMemory,
    earlier: Sequence[ReplyPlan],
    recent: RecentMessages,
    reminded: Sequence[RemindedThread],
    due: DueCuriosities,
    knowledge_documents: dict[int, KnowledgeDocument],
    move_outcomes: Sequence[MoveOutcome],
    check_in_kinds: Sequence[CheckInKind] = (),
    last_conversation_where: str = "",
    patterns: Sequence[RemindedPattern] = (),
) -> str:
    """Write what the Reply Plan model is given about the Message.

    Args:
        snapshot: The User being answered.
        understanding: How the Companion understood the Message.
        needs: Every Need, in order.
        moves: Every Move the reply may make, in order.
        saved: The User's saved memory, read for this reply.
        earlier: This Conversation's earlier Reply Plans, oldest first.
        recent: The Recent Messages: every message from the last hours,
            across Conversations, ending with the Message being answered.
        reminded: The Life Threads in mind: those the Message reminds the
            Companion of, then those that came to mind earlier in the
            Conversation.
        due: The Curiosities it may bring up.
        knowledge_documents: The Knowledge documents it may choose from, by
            number.
        move_outcomes: The User's past Move Outcomes closest to the Message,
            closest first.
        check_in_kinds: The Check-in Kinds it may weave in when a Check-in
            is due; empty when none is.
        last_conversation_where: Where the previous Conversation among the
            Recent Messages was when its last Reply Plan was made; "" if
            none.
        patterns: The Patterns in mind, numbered.

    Returns:
        The time, the Understanding, Needs, Moves and which each Need
        allows, past Move Outcomes with their days, User Portrait, Goals,
        Memory Categories, recent Conversations, reminded Life Threads, the
        Patterns in mind, due Curiosities and how each Need treats them,
        Knowledge documents, the due
        Check-in's Kinds when one is due, where the previous Conversation
        was, earlier Reply Plans, earlier messages across Conversations and
        latest message.
    """
    fallback = fallback_need(needs)
    need_lines = "\n".join(f"- {need.name}: {need.when_it_fits}" for need in needs)
    move_lines = "\n".join(f"- {move.name}: {move.when_it_fits}" for move in moves)
    allowed_lines = "\n".join(format_allowed_moves(need, moves) for need in needs)
    outcome_lines = "\n".join(
        f"- {describe_move_outcome(outcome, snapshot.user.time_zone)}"
        for outcome in move_outcomes
    )
    goals = saved.items_in(snapshot.settings.get(HOME_GOALS_MEMORY_CATEGORY))
    goal_lines = "\n".join(f"- {item.content}" for item in goals)
    category_lines = "\n".join(
        f"- {category.name}: {category.description}" for category in saved.pickable
    )
    summary_lines = "\n".join(summary_line(summary) for summary in saved.summaries)
    earlier_lines = "\n".join(
        format_earlier_reply_plan(reply_plan) for reply_plan in earlier
    )
    knowledge_lines = "\n".join(
        format_knowledge_document(number, document)
        for number, document in knowledge_documents.items()
    )
    check_in_section = (
        "\n\nA Check-in with them is due. Check-in Kinds you may weave in:\n"
        + "\n".join(f"- {kind.name}: {kind.description}" for kind in check_in_kinds)
        if check_in_kinds
        else ""
    )
    last_conversation_line = (
        f"Where the previous Conversation was when it ended: "
        f"{last_conversation_where}\n\n"
        if last_conversation_where
        else ""
    )
    return (
        f"Time where they are: {format_local_time(snapshot.local_now)}\n\n"
        f"How you understood their latest message:\n"
        f"{describe_understanding(understanding)}\n\n"
        f"Needs:\n{need_lines}\n"
        f"Fallback Need: {fallback.name}\n\n"
        f"Moves:\n{move_lines or 'None.'}\n\n"
        f"Moves each Need allows:\n{allowed_lines}\n\n"
        f"How Moves went for them before in moments like this, closest first:\n"
        f"{outcome_lines or 'None found.'}\n\n"
        f"Their User Portrait:\n{saved.portrait or 'Not written yet.'}\n\n"
        f"Their Goals:\n{goal_lines or 'None saved.'}\n\n"
        f"Memory Categories with something saved:\n{category_lines or 'None yet.'}"
        f"\n\nRecent days, newest first:\n{summary_lines or 'None yet.'}"
        f"\n\nLife Threads in mind: those this message reminds you of, open "
        f"ones first, then those from earlier in this Conversation:\n"
        f"{describe_reminded_threads(reminded, snapshot.user.time_zone)}"
        f"\n\nPatterns in mind: what you've noticed keeps showing up across "
        f"their life. A suspected one is only your guess:\n"
        f"{describe_patterns_in_mind(patterns, snapshot.user.time_zone)}"
        f"\n\nThings you've been wondering about them, whose time has come "
        f"{describe_due_curiosities(due, snapshot.user.time_zone)}"
        f"\n\nHow each Need treats them:\n{describe_curiosity_treatments(needs)}"
        f"\n\nKnowledge documents, with when each helps:\n"
        f"{knowledge_lines or 'None.'}"
        f"{check_in_section}"
        f"\n\n{last_conversation_line}"
        f"Earlier Reply Plans in this Conversation, oldest first:\n"
        f"{earlier_lines or 'None yet.'}\n\n"
        f"{describe_recent_messages(recent, snapshot.user.time_zone)}"
    )


def read_number(value: Any) -> int | None:
    """Read a number the form uses to name something from a numbered list.

    Args:
        value: The number, as the model wrote it.

    Returns:
        The number; None if the value isn't a whole number, e.g. a title,
        a number written as text, or true/false.
    """
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def read_bring_up_way(value: Any) -> BringUpWay:
    """Read how to bring something up, where an odd value reads as weaving it in.

    Args:
        value: The `how` field's value.

    Returns:
        The way.
    """
    return (
        BringUpWay(value)
        if value in {way.value for way in BringUpWay}
        else BringUpWay.WEAVE
    )


def read_thread(
    value: Any, by_number: dict[int, RemindedThread]
) -> RemindedThread | None:
    """Find the reminded Thread a number in the form names.

    Args:
        value: The number, as the model wrote it.
        by_number: The reminded Threads, by number.

    Returns:
        The Thread; None if the value isn't one of their numbers.
    """
    number = read_number(value)
    return None if number is None else by_number.get(number)


def read_threads_touched(
    value: Any, by_number: dict[int, RemindedThread]
) -> tuple[str, ...]:
    """Read the Threads the form says the Message touches.

    Args:
        value: The field's value: a list of Thread numbers.
        by_number: The reminded Threads, by number.

    Returns:
        Their titles, each once; unknown numbers are skipped.
    """
    if not isinstance(value, list):
        return ()
    found = (read_thread(number, by_number) for number in value)
    return tuple(dict.fromkeys(item.thread.title for item in found if item))


def read_bring_up(
    value: Any, by_number: dict[int, RemindedThread]
) -> tuple[ThreadToBringUp, ...]:
    """Read the Threads the form says to bring up, how and why.

    Args:
        value: The field's value: a list of {"thread", "how", "why"} entries.
        by_number: The reminded Threads, by number.

    Returns:
        The Threads, each once; an unknown number is skipped and an odd
        "how" reads as weaving it in.
    """
    if not isinstance(value, list):
        return ()
    chosen: dict[UUID, ThreadToBringUp] = {}
    for entry in value:
        if not isinstance(entry, dict):
            continue
        item = read_thread(entry.get("thread"), by_number)
        if item is None or item.thread.id in chosen:
            continue
        chosen[item.thread.id] = ThreadToBringUp(
            thread_id=item.thread.id,
            title=item.thread.title,
            how=read_bring_up_way(entry.get("how")),
            why=read_form_text(entry.get("why")),
        )
    return tuple(chosen.values())


def read_left_alone(
    value: Any, by_number: dict[int, RemindedThread]
) -> tuple[ThreadLeftAlone, ...]:
    """Read the Threads the form says to leave alone, and why.

    Args:
        value: The field's value: a list of {"thread", "reason"} entries.
        by_number: The reminded Threads, by number.

    Returns:
        The Threads, each once; an unknown number is skipped.
    """
    if not isinstance(value, list):
        return ()
    chosen: dict[UUID, ThreadLeftAlone] = {}
    for entry in value:
        if not isinstance(entry, dict):
            continue
        item = read_thread(entry.get("thread"), by_number)
        if item is None or item.thread.id in chosen:
            continue
        chosen[item.thread.id] = ThreadLeftAlone(
            thread_id=item.thread.id,
            title=item.thread.title,
            reason=read_form_text(entry.get("reason")),
        )
    return tuple(chosen.values())


def read_pattern_picked(
    value: Any, by_number: dict[int, RemindedPattern]
) -> PatternPicked | None:
    """Find the Pattern in mind a number in the form names.

    Args:
        value: The number, as the model wrote it.
        by_number: The Patterns in mind, by number.

    Returns:
        The Pattern; None if the value isn't one of their numbers.
    """
    number = read_number(value)
    item = None if number is None else by_number.get(number)
    if item is None:
        return None
    return PatternPicked(pattern_id=item.pattern.id, pattern=item.pattern.pattern)


def read_patterns_picked(
    value: Any, by_number: dict[int, RemindedPattern]
) -> tuple[PatternPicked, ...]:
    """Find the Patterns in mind a list of numbers in the form names.

    Args:
        value: The field's value: a list of Pattern numbers.
        by_number: The Patterns in mind, by number.

    Returns:
        The Patterns, each once; unknown numbers are skipped.
    """
    if not isinstance(value, list):
        return ()
    found = (read_pattern_picked(number, by_number) for number in value)
    return tuple(dict.fromkeys(item for item in found if item))


def read_curiosities_to_raise(
    value: Any, due: DueCuriosities
) -> tuple[CuriosityToRaise, ...]:
    """Read the Curiosities the form says to bring up, and how.

    Args:
        value: The `bring_up` field's value: a list of entries, those for a
            Curiosity written as {"curiosity", "how"}.
        due: The Curiosities the model was shown, numbered, and how many
            more the Conversation may raise.

    Returns:
        The Curiosities, each once, no more than one per reply and no more
        than the Conversation may still raise; an unknown number is skipped
        and an odd "how" reads as weaving it in.
    """
    if not isinstance(value, list):
        return ()
    by_number: dict[int, NumberedCuriosity] = {
        item.number: item for item in due.offered
    }
    chosen: dict[UUID, CuriosityToRaise] = {}
    for entry in value:
        if not isinstance(entry, dict):
            continue
        number = read_number(entry.get("curiosity"))
        if number is None:
            continue
        item = by_number.get(number)
        if item is None or item.curiosity.id in chosen:
            continue
        chosen[item.curiosity.id] = CuriosityToRaise(
            curiosity_id=item.curiosity.id,
            question=item.curiosity.question,
            why=item.curiosity.why,
            how=read_bring_up_way(entry.get("how")),
            guess=item.curiosity.guess,
            how_sure=item.curiosity.how_sure,
        )
    return tuple(chosen.values())[: min(due.left, MOST_CURIOSITIES_PER_REPLY)]


def keep_held_back_threads_alone(
    form: ReplyPlanForm, reminded: Sequence[RemindedThread]
) -> ReplyPlanForm:
    """Make sure the form brings up no Thread that must be left alone.

    A held-back Thread the form chose to bring up is left alone instead,
    with the reason it is held back. One the form chose both to bring up and
    to leave alone is left alone.

    Args:
        form: The form, as read.
        reminded: The reminded Threads, with why any is held back.

    Returns:
        The form, bringing up only Threads that may be.
    """
    held_back = {item.thread.id: item.hold_back for item in reminded if item.hold_back}
    left_alone_ids = {item.thread_id for item in form.left_alone}
    newly_left_alone = tuple(
        ThreadLeftAlone(item.thread_id, item.title, held_back[item.thread_id])
        for item in form.bring_up
        if item.thread_id in held_back and item.thread_id not in left_alone_ids
    )
    return replace(
        form,
        bring_up=tuple(
            item
            for item in form.bring_up
            if item.thread_id not in held_back and item.thread_id not in left_alone_ids
        ),
        left_alone=form.left_alone + newly_left_alone,
    )


def read_knowledge_lookup(
    value: Any, by_number: dict[int, KnowledgeDocument]
) -> KnowledgeLookup | None:
    """Read the form's `knowledge` field: documents to search and a phrase.

    Args:
        value: The field's value, e.g. {"documents": [1], "search":
            "letting sorrow pass"}.
        by_number: The Knowledge documents the model was shown, by number.

    Returns:
        The lookup, each document once; None if it names no listed number
        or gives no phrase, so no Knowledge is searched.
    """
    if not isinstance(value, dict):
        return None
    numbers = value.get("documents")
    search = value.get("search")
    if not isinstance(numbers, list) or not isinstance(search, str):
        return None
    documents: dict[UUID, ChosenKnowledgeDocument] = {}
    for listed in numbers:
        number = read_number(listed)
        document = None if number is None else by_number.get(number)
        if document is None:
            continue
        documents[document.id] = ChosenKnowledgeDocument(
            document_id=document.id, title=document.title
        )
    if not documents or not search.strip():
        return None
    return KnowledgeLookup(documents=tuple(documents.values()), search=search.strip())


def read_check_in_choice(
    value: Any, kinds: Sequence[CheckInKind]
) -> ChosenCheckIn | None:
    """Read the form's `check_in` field: the Kind to weave in and a note.

    Args:
        value: The field's value, e.g. {"kind": "A follow-up", "note": "Ask
            how the board presentation went."}.
        kinds: The Check-in Kinds the model was offered.

    Returns:
        The choice, with the Kind's name as Admins wrote it; None when it
        names no offered Kind, in any case, or gives no note.
    """
    if not isinstance(value, dict):
        return None
    kind_name, note = value.get("kind"), read_form_text(value.get("note"))
    if not isinstance(kind_name, str) or not note:
        return None
    kinds_by_name = {kind.name.lower(): kind for kind in kinds}
    kind = kinds_by_name.get(kind_name.strip().lower())
    return ChosenCheckIn(kind=kind.name, note=note) if kind else None


def read_reply_plan_form(
    answer: str,
    reminded: Sequence[RemindedThread],
    due: DueCuriosities,
    knowledge_documents: dict[int, KnowledgeDocument],
    check_in_kinds: Sequence[CheckInKind] = (),
    patterns: Sequence[RemindedPattern] = (),
) -> ReplyPlanForm | None:
    """Read the Reply Plan model's JSON form.

    Text around the JSON object, such as a code fence, is ignored. Life
    Threads are named by their numbers in the reminded list; no held-back
    Thread is ever brought up. Curiosities are named by their numbers in the
    due list; at most one is brought up per reply, and no more than the
    Conversation may still raise. Knowledge documents are named by their
    numbers in the Knowledge list. A missing or odd "send_photo" reads as
    allowed, and a missing or odd "ask_why" as not said. The Read is said
    only when there is one and "say_read" is true. A Check-in is chosen only
    from the Kinds offered. Patterns are named by their numbers in the
    Patterns in mind; one is offered only when the Read is said, and an
    offered one counts as used.

    Args:
        answer: The model's answer.
        reminded: The Life Threads the model was shown, numbered.
        due: The Curiosities the model was shown, numbered.
        knowledge_documents: The Knowledge documents the model was shown,
            by number.
        check_in_kinds: The Check-in Kinds it was offered; empty when no
            Check-in was due.
        patterns: The Patterns in mind the model was shown, numbered.

    Returns:
        The form, or None if it has no JSON object naming a Need.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict):
        return None
    need = read_form_text(parsed.get("need"))
    if not need:
        return None
    ask_why = parsed.get("ask_why")
    read = read_form_text(parsed.get("read"))
    say_read = bool(read) and parsed.get("say_read") is True
    by_number = {item.number: item for item in reminded}
    patterns_by_number = {item.number: item for item in patterns}
    offered = (
        read_pattern_picked(parsed.get("offer_pattern"), patterns_by_number)
        if say_read
        else None
    )
    used = read_patterns_picked(parsed.get("patterns_used"), patterns_by_number)
    form = ReplyPlanForm(
        need=need,
        guidance=read_form_text(parsed.get("guidance")),
        lead_move=read_form_text(parsed.get("lead_move")),
        lead_move_why=read_form_text(parsed.get("lead_move_why")),
        support_move=read_form_text(parsed.get("support_move")),
        support_move_why=read_form_text(parsed.get("support_move_why")),
        next_move=read_form_text(parsed.get("next_move")),
        next_move_why=read_form_text(parsed.get("next_move_why")),
        memory_categories=read_text_list(parsed.get("memory_categories")),
        threads_touched=read_threads_touched(parsed.get("threads_touched"), by_number),
        bring_up=read_bring_up(parsed.get("bring_up"), by_number),
        left_alone=read_left_alone(parsed.get("left_alone"), by_number),
        curiosities=read_curiosities_to_raise(parsed.get("bring_up"), due),
        knowledge=read_knowledge_lookup(parsed.get("knowledge"), knowledge_documents),
        photo_fits=parsed.get("send_photo") is not False,
        ask_why=ask_why if isinstance(ask_why, bool) else None,
        where_we_are=read_form_text(parsed.get("where_we_are")),
        read=read,
        say_read=say_read,
        check_in=read_check_in_choice(parsed.get("check_in"), check_in_kinds),
        patterns_used=tuple(dict.fromkeys([*used, *([offered] if offered else [])])),
        pattern_offered=offered,
        curiosity_not_asked_why=read_form_text(parsed.get("no_curiosity_why")),
    )
    return keep_held_back_threads_alone(form, reminded)


def settle_curiosities(
    form: ReplyPlanForm, need: Need, due: DueCuriosities, asked_why: bool
) -> ReplyPlanForm:
    """Hold the form's Curiosities to what the picked Need and the reply allow.

    A reply that asks why asks no Curiosity too: one question per reply.
    Under a Need that asks Curiosities by default, a reply that asks none of
    those offered keeps the reason.

    Args:
        form: The form, as read.
        need: The Need the reply follows.
        due: The Curiosities the reply may ask under that Need.
        asked_why: Whether the reply asks why they feel as they do.

    Returns:
        The form, asking a Curiosity only when one was offered under the
        Need and the reply doesn't ask why, with why none is asked when the
        Need asks by default.
    """
    chosen = form.curiosities if due.offered and not asked_why else ()
    reason = ASKS_WHY_INSTEAD if asked_why else form.curiosity_not_asked_why
    return replace(
        form,
        curiosities=chosen,
        curiosity_not_asked_why=why_none_asked(need, due, chosen, reason),
    )


def may_send_photo(understanding: UnderstandingForm, plan: ReplyPlanForm) -> bool:
    """Decide whether the reply may send the User one of their Shared Photos.

    The Reply Plan may rule a photo out. Whatever it says, a struggling User
    is never sent a photo back unless they asked for one: a photo can sting,
    or read as "cheer up" instead of listening.

    Args:
        understanding: How the Companion understood the Message.
        plan: What the Reply Plan decided.

    Returns:
        True if the plan allows it, unless the User is struggling and didn't
        ask for a photo.
    """
    return plan.photo_fits and (
        not understanding.struggling or understanding.asked_for_photo
    )


def woven_check_in_from_plan(
    snapshot: UserSnapshot, form: ReplyPlanForm, kinds: Sequence[CheckInKind]
) -> WovenCheckIn | None:
    """Make the Woven-in Check-in the Reply Plan chose, ready to save.

    Args:
        snapshot: The User being answered, as read for the reply.
        form: This Message's Reply Plan form.
        kinds: The Check-in Kinds it was offered.

    Returns:
        The Check-in, for the User's Due Time and any Check in Now waiting;
        None when the plan chose none, its Kind is no longer offered or the
        User has no Due Time.
    """
    settings = snapshot.user.check_ins
    if form.check_in is None or settings.next_due_at is None:
        return None
    kind = next((kind for kind in kinds if kind.name == form.check_in.kind), None)
    if kind is None:
        return None
    return WovenCheckIn(
        kind=kind,
        note=form.check_in.note,
        due_at=settings.next_due_at,
        check_in_now=settings.check_in_now,
    )


def fallback_form(fallback: Need) -> ReplyPlanForm:
    """Make the form used when the Reply Plan call fails or can't be read.

    Args:
        fallback: The fallback Need.

    Returns:
        A form with the fallback Need, no Moves, no Memory Categories, and
        no asking why, as the old combined call's fallback never asked. It
        says why it asks no Curiosity, kept only when the Need owes a reason.
    """
    return ReplyPlanForm(
        need=fallback.name, ask_why=False, curiosity_not_asked_why=NO_REPLY_PLAN
    )


def fallback_need(needs: Sequence[Need]) -> Need:
    """Find the fallback Need, used when it isn't clear what the User needs.

    Args:
        needs: Every Need; exactly one is the fallback.

    Returns:
        The fallback Need.
    """
    return next(need for need in needs if need.is_fallback)


def find_need(needs: Sequence[Need], name: str) -> Need:
    """Find the Need the form named, or the fallback Need if there is none.

    Args:
        needs: Every Need.
        name: The name the form gave, in any case.

    Returns:
        The Need.
    """
    for need in needs:
        if need.name.lower() == name.lower():
            return need
    return fallback_need(needs)


def pick_moves(
    need: Need, needs: Sequence[Need], moves: Sequence[Move], form: ReplyPlanForm
) -> PickedMoves:
    """Find the Moves the form named, keeping only those that may be made.

    The lead and supporting Moves must be ones the Need allows. The next
    Move must be one some Need allows, since the User may need something
    else by then. An unknown Move, or one ruled out, is dropped rather than
    failing the Reply Plan. A supporting Move the same as the lead is
    dropped too, and one left without a lead becomes the lead.

    Args:
        need: The Need the reply follows.
        needs: Every Need.
        moves: Every Move that can be made for the User.
        form: This Message's form.

    Returns:
        The lead, supporting and next Moves.
    """
    allowed = {move.name.lower(): move for move in allowed_moves(need, moves)}
    allowed_by_any_need = {
        move.name.lower(): move
        for some_need in needs
        for move in allowed_moves(some_need, moves)
    }
    lead = allowed.get(form.lead_move.lower())
    support = allowed.get(form.support_move.lower())
    next_move = allowed_by_any_need.get(form.next_move.lower())
    if lead is None:
        return PickedMoves(lead=support, next=next_move)
    return PickedMoves(
        lead=lead, support=None if support == lead else support, next=next_move
    )


def should_ask_why(
    understanding: UnderstandingForm,
    plan: ReplyPlanForm,
    earlier: Sequence[ReplyPlan],
) -> bool:
    """Say whether the reply should gently ask why the User feels as they do.

    The Reply Plan decides; when it doesn't say, the reply asks when their
    mood stands out (high intensity). Either way it never asks when the
    Companion knows why, or when the previous reply in the Conversation
    already asked.

    Args:
        understanding: How the Companion understood the Message.
        plan: This Message's Reply Plan form.
        earlier: This Conversation's earlier Reply Plans, oldest first.

    Returns:
        True if the reply should ask.
    """
    asked_last_time = bool(earlier) and earlier[-1].asked_why
    if understanding.cause_known or asked_last_time:
        return False
    if plan.ask_why is None:
        return understanding.intensity == MoodIntensity.HIGH
    return plan.ask_why


def drop_moves_that_ask(picked: PickedMoves) -> PickedMoves:
    """Drop the lead and supporting Moves that ask the User a question.

    Used when the reply already asks another question, which wins. A
    dropped lead Move leaves no lead: the supporting Move doesn't move up.

    Args:
        picked: The Moves the reply was to make.

    Returns:
        The Moves it makes; the next Move stays.
    """
    return PickedMoves(
        lead=None if picked.lead and picked.lead.asks_a_question else picked.lead,
        support=(
            None
            if picked.support and picked.support.asks_a_question
            else picked.support
        ),
        next=picked.next,
    )


def format_reply_guidance(
    need: Need,
    picked: PickedMoves,
    plan: ReplyPlanForm,
    understanding: UnderstandingForm,
    ask_why_note: str,
    threads_section: str,
    left_alone_section: str,
    curiosities_section: str,
    past_days: Sequence[str] = (),
) -> ReplyGuidance:
    """Write what the Reply Plan adds to the reply's instructions.

    Args:
        need: The Need the reply follows.
        picked: The Moves the reply makes.
        plan: This Message's Reply Plan form.
        understanding: How the Companion understood the Message, for the
            mood.
        ask_why_note: The "ask why" note; "" when the reply shouldn't ask.
        threads_section: The Life Threads that matter and those to bring up;
            "" if none matter.
        left_alone_section: The Life Threads to leave alone; "" if none.
        curiosities_section: The Curiosity to ask; "" if none.
        past_days: What each call of the past-day tool read, in order.

    Returns:
        The Threads to leave alone as a boundary; the Need and how to reply,
        the Read when the plan says to give it now with the Pattern it
        offers, if any, the lead and supporting
        Moves and how to make them, the guidance, the mood, the note, the
        Threads to bring up and the Curiosity to ask as the plan; and the
        past days it read, with what the reply remembers.
    """
    lines = [f"What they need from you right now: {need.name}.", need.how_to_reply]
    if plan.say_read:
        lines.append(
            "Your Read of what is really going on, to give in this reply as your "
            f"view, never as fact: {plan.read}"
        )
    if plan.pattern_offered:
        lines.append(
            "It comes from something you've noticed keeps showing up in their "
            f"life: {plan.pattern_offered.pattern} Offer it as what you notice "
            '("here\'s what I notice…"), never as fact, and let them say '
            "whether it fits."
        )
    if picked.lead:
        lines.append(f"Lead with: {picked.lead.name}. {picked.lead.how_to_do_it}")
    if picked.support:
        lines.append(
            f"Support it with: {picked.support.name}. {picked.support.how_to_do_it}"
        )
    if plan.guidance:
        lines.append(plan.guidance)
    if understanding.mood:
        lines.append(
            f"How they seem: {understanding.mood} ({understanding.intensity.value})."
        )
    if ask_why_note:
        lines.append(ask_why_note)
    reply_plan = "\n".join(lines)
    for section in (threads_section, curiosities_section):
        if section:
            reply_plan += f"\n\n{section}"
    past_days_section = (
        "Past days you looked up for this reply:\n\n" + "\n\n".join(past_days)
        if past_days
        else ""
    )
    return ReplyGuidance(
        boundaries=left_alone_section,
        plan=reply_plan,
        past_days=past_days_section,
    )


def describe_reply_plan_shape(
    need: Need,
    picked: PickedMoves,
    form: ReplyPlanForm,
    reminded: Sequence[RemindedThread],
    check_in_kinds_offered: int = 0,
    curiosities_offered: int = 0,
) -> ReplyPlanShape:
    """Describe the shape of a Reply Plan for the Model Call Log.

    Args:
        need: The Need the reply follows.
        picked: The Moves the reply makes.
        form: The form the reply follows.
        reminded: The Life Threads the Message reminded the Companion of.
        check_in_kinds_offered: How many Check-in Kinds it could weave in.
        curiosities_offered: How many Curiosities it could ask under the
            Need.

    Returns:
        The Need, the lead, supporting and next Moves' names, how many Life
        Threads were reminded, brought up, left alone and held back,
        whether a Read was formed and said, how many Check-in Kinds were
        offered and which it chose, whether a Pattern was used and
        offered, and how many Curiosities were offered and whether one is
        asked; never any words.
    """
    ways = [item.how for item in form.bring_up]
    held_back = [item for item in reminded if item.hold_back]
    return ReplyPlanShape(
        need=need.name,
        threads_reminded=len(reminded),
        threads_led_with=ways.count(BringUpWay.LEAD),
        threads_woven_in=ways.count(BringUpWay.WEAVE),
        threads_left_alone=len(form.left_alone),
        threads_held_back=len(held_back),
        lead_move=picked.lead_name,
        support_move=picked.support_name,
        next_move=picked.next_name,
        read_formed=bool(form.read),
        read_said=form.say_read,
        check_in_kinds_offered=check_in_kinds_offered,
        check_in_kind=form.check_in.kind if form.check_in else None,
        pattern_used=bool(form.patterns_used),
        pattern_offered=form.pattern_offered is not None,
        curiosities_offered=curiosities_offered,
        curiosity_asked=bool(form.curiosities),
    )


class ReplyPlanService:
    """Makes the Reply Plan of each Message, after the Understanding.

    One model call, given the Persona's Outlook in front of its prompt,
    decides what the reply does: where the Conversation is now, Zeph's Read
    of what is really going on and whether to say it now, which Need fits,
    which Moves the reply makes from those the Need allows (leaving out any
    whose needed Feature doesn't work for the User right now, and any that
    asks a question and was made in the previous reply), which Move it means
    to make next and why, which Memory Categories and Knowledge matter,
    which Life Threads to bring up or leave alone, which Curiosity to ask
    (as the picked Need treats them), which
    Patterns in mind its Read is built on and whether to offer one, whether a
    Shared Photo may be sent, whether to ask why and, when a Check-in is
    due, whether one of its Kinds fits this reply. It sees this
    Conversation's earlier Reply Plans with where the Conversation was, the
    Reads formed and their Moves, so it knows whether it already asked why,
    gave a Read and which Move it had in mind next. It sees the Recent Messages
    (every message from the last hours, across Conversations) and where the
    previous Conversation in it was when it ended, and may call the past-day
    tool to read an older day's messages word for word.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        model_call_log: ModelCallLog,
        clock: Clock,
        past_day: PastDayTool,
    ) -> None:
        """Set up the service.

        Args:
            repositories: Where Needs, Moves, Conversations and Reply Plans
                are stored.
            chat_model: Fills in the form and records the tokens used.
            model_call_log: Records the shape of each Reply Plan.
            clock: Tells the current time.
            past_day: Lets the model read a past day's messages.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._model_call_log = model_call_log
        self._clock = clock
        self._past_day = past_day

    def plan(
        self,
        snapshot: UserSnapshot,
        understanding: Understanding,
        recent: RecentMessages,
        saved: SavedMemory,
        reminded: Sequence[RemindedThread],
        due: DueCuriosities,
        move_outcomes: Sequence[MoveOutcome],
        check_in_kinds: Sequence[CheckInKind] = (),
        patterns: Sequence[RemindedPattern] = (),
    ) -> PlannedReply:
        """Make and save the Reply Plan of the Conversation's newest Message.

        Its shape goes into the Model Call Log, for every User. An unknown
        Need falls back to the fallback Need; an unknown Move, one the Need
        rules out (for the next Move, one every Need rules out), one whose
        needed Feature doesn't work for the User (Research once Web Search
        is off or its daily limit is used up), or one that asks a question
        and was made in the previous reply, is dropped, with the next
        Move's why. A lead or supporting Move that asks a question is dropped
        too, and not saved as made, when the reply asks why or raises a
        Curiosity: only one question per reply. No Curiosity is raised
        under a Need that never asks one, or in a reply that asks why;
        under a Need that asks by default, why none was asked is saved
        with the form. An unreadable form or a
        failed call falls back to the fallback Need with no Moves and no
        Memory Categories, so the reply still goes, with no Life Thread,
        no Curiosity brought up and no Check-in.

        Args:
            snapshot: The User being answered.
            understanding: The Message's Understanding, just made.
            recent: The Recent Messages, ending with the Message.
            saved: The User's saved memory, read for this reply.
            reminded: The Life Threads in mind: those the Message reminds the
                Companion of, then those that came to mind earlier in the
                Conversation.
            due: The Curiosities it may bring up.
            move_outcomes: The User's past Move Outcomes closest to the
                Message, closest first.
            check_in_kinds: The Check-in Kinds it may weave in, when code
                allows a due Check-in; empty when none is.
            patterns: The Patterns in mind, numbered.

        Returns:
            The saved Reply Plan, what it adds to the reply and the
            Check-in it chose.
        """
        conversation_id = recent.conversation_id
        needs = self._repositories.needs.list_all()
        earlier = self._repositories.reply_plans.list_for_conversation(conversation_id)
        moves = moves_without_repeat_questions(
            moves_that_work(
                self._repositories.moves.list_all(), self._working_features(snapshot)
            ),
            earlier,
        )
        knowledge_documents = number_knowledge_documents(
            self._knowledge_documents(snapshot)
        )
        past_days: list[str] = []
        model_form = self._ask(
            snapshot,
            describe_message_for_reply_plan(
                snapshot,
                understanding.form,
                needs,
                moves,
                saved,
                earlier,
                recent,
                reminded,
                due,
                knowledge_documents,
                move_outcomes,
                check_in_kinds,
                self._last_conversation_where(recent),
                patterns,
            ),
            reminded,
            due,
            knowledge_documents,
            check_in_kinds,
            past_days.append,
            patterns,
        )
        if model_form is None:
            need = fallback_need(needs)
            form = fallback_form(need)
        else:
            form = model_form
            need = find_need(needs, form.need)
        asked_why = should_ask_why(understanding.form, form, earlier)
        due_under_need = offered_under(need, due)
        form = settle_curiosities(form, need, due_under_need, asked_why)
        asks_another_question = asked_why or bool(form.curiosities)
        picked = pick_moves(need, needs, moves, form)
        if asks_another_question:
            picked = drop_moves_that_ask(picked)
        reply_plan = ReplyPlan(
            id=uuid4(),
            user_id=snapshot.user.id,
            conversation_id=conversation_id,
            message_id=newest_incoming_message_id(recent.messages),
            form=form,
            need=need.name,
            asked_why=asked_why,
            made_at=self._clock.now(),
            lead_move=picked.lead_name,
            support_move=picked.support_name,
            next_move=picked.next_name,
            next_move_why=(form.next_move_why or None) if picked.next else None,
            is_fallback=model_form is None,
        )
        self._repositories.reply_plans.add(reply_plan)
        self._model_call_log.record_reply_plan_shape(
            snapshot,
            describe_reply_plan_shape(
                need,
                picked,
                form,
                reminded,
                len(check_in_kinds),
                len(due_under_need.offered),
            ),
        )
        ask_why_note = snapshot.settings.get(REPLY_ASK_WHY_NOTE) if asked_why else ""
        return PlannedReply(
            reply_plan=reply_plan,
            reply_guidance=format_reply_guidance(
                need,
                picked,
                form,
                understanding.form,
                ask_why_note,
                format_threads_for_reply(reminded, model_form, snapshot.user.time_zone),
                format_threads_left_alone(model_form),
                format_curiosities_for_reply(form.curiosities),
                past_days,
            ),
            asks_a_question=asks_another_question or picked.asks_a_question,
            may_send_photo=may_send_photo(understanding.form, form),
            check_in=woven_check_in_from_plan(snapshot, form, check_in_kinds),
        )

    def _last_conversation_where(self, recent: RecentMessages) -> str:
        """Find where the previous Conversation among the Recent Messages ended up.

        Args:
            recent: The Recent Messages.

        Returns:
            The where-we-are line of the previous Conversation's last Reply
            Plan; "" if no earlier Conversation is among them, or it has no
            Reply Plan.
        """
        earlier_conversation_ids = [
            message.conversation_id
            for message in recent.messages
            if message.conversation_id != recent.conversation_id
        ]
        if not earlier_conversation_ids:
            return ""
        reply_plans = self._repositories.reply_plans.list_for_conversation(
            earlier_conversation_ids[-1]
        )
        return reply_plans[-1].form.where_we_are if reply_plans else ""

    def _working_features(self, snapshot: UserSnapshot) -> set[Feature]:
        """List the Features that work for the User right now.

        Web Search counts as not working once its daily limit is used up.

        Args:
            snapshot: The User being answered.

        Returns:
            The Features.
        """
        working = {feature for feature in Feature if snapshot.works(feature)}
        if Feature.WEB_SEARCH in working and web_search_limit_used_up(
            self._repositories, snapshot
        ):
            working.discard(Feature.WEB_SEARCH)
        return working

    def _knowledge_documents(self, snapshot: UserSnapshot) -> list[KnowledgeDocument]:
        """List the Knowledge documents the Reply Plan may choose from.

        Args:
            snapshot: The User being answered.

        Returns:
            Every Ready document; none when Knowledge doesn't work for them.
        """
        if not snapshot.works(Feature.KNOWLEDGE):
            return []
        return [
            document
            for document in self._repositories.knowledge_documents.list_all()
            if document.status == KnowledgeStatus.READY
        ]

    def _ask(
        self,
        snapshot: UserSnapshot,
        description: str,
        reminded: Sequence[RemindedThread],
        due: DueCuriosities,
        knowledge_documents: dict[int, KnowledgeDocument],
        check_in_kinds: Sequence[CheckInKind],
        on_past_day_read: Callable[[str], None],
        patterns: Sequence[RemindedPattern] = (),
    ) -> ReplyPlanForm | None:
        """Ask the model to fill in the form, with the Outlook before the prompt.

        The model may call the past-day tool before it answers.

        Args:
            snapshot: The User being answered.
            description: What the model is given about the Message.
            reminded: The Life Threads it was shown, numbered.
            due: The Curiosities it was shown, numbered.
            knowledge_documents: The Knowledge documents it was shown, by
                number.
            check_in_kinds: The Check-in Kinds it was offered.
            on_past_day_read: Called with what each call of the past-day
                tool read.
            patterns: The Patterns in mind it was shown, numbered.

        Returns:
            The form; None if the call failed or the answer can't be read.
        """
        settings = snapshot.settings
        try:
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.REPLY_PLAN,
                model=settings.get(REPLY_PLAN_MODEL),
                thinking=settings.get(REPLY_PLAN_THINKING),
                instructions=(
                    f"{settings.get(PERSONA_OUTLOOK)}\n\n"
                    f"{settings.get(REPLY_PLAN_PROMPT)}"
                ),
                history=[ChatLine(role=ChatRole.USER, text=description)],
                tools=[self._past_day.tool_for(snapshot, on_past_day_read)],
            )
        except Exception:
            logger.exception("The Reply Plan call failed; using the fallback Need")
            return None
        form = read_reply_plan_form(
            answer, reminded, due, knowledge_documents, check_in_kinds, patterns
        )
        if form is None:
            logger.warning(
                "The Reply Plan form couldn't be read; using the fallback Need"
            )
        return form
