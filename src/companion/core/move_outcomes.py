import json
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from companion.core.life_threads import (
    read_text,
    recent_texts_to_search,
)
from companion.core.memory_retrieval import format_day, format_time
from companion.core.models import (
    ChatLine,
    ChatRole,
    ConversationMessage,
    ModelStep,
    MoveOutcome,
    MoveOutcomeToSave,
    MoveResult,
    MoveRole,
    ReplyPlan,
    Understanding,
    UserSnapshot,
)
from companion.core.platform_settings import (
    MOVE_OUTCOME_KEEPING_MODEL,
    MOVE_OUTCOME_KEEPING_PROMPT,
    MOVE_OUTCOME_KEEPING_THINKING,
    MOVE_OUTCOMES_CLOSENESS_PERCENT,
    MOVE_OUTCOMES_PER_UNDERSTANDING,
    thinking_to_use,
)
from companion.core.ports import Clock, Embedder, Repositories
from companion.core.transcripts import to_transcript_lines
from companion.core.usage import UsageRecordingChatModel

logger = logging.getLogger(__name__)

RESULT_WORDS = {
    MoveResult.HELPED: "helped",
    MoveResult.DIDNT_HELP: "didn't help",
    MoveResult.MIXED: "had mixed results",
}


@dataclass(frozen=True)
class MoveMade:
    """A Move made in a Conversation, as the keeping model is shown it.

    Attributes:
        name: The Move's name.
        role: Whether it led a reply or supported one.
        first_made_at: When it was first made in the Conversation.
    """

    name: str
    role: MoveRole
    first_made_at: datetime


def list_moves_made(reply_plans: Sequence[ReplyPlan]) -> list[MoveMade]:
    """List the Moves a Conversation's Reply Plans made, each once.

    The same Move in the same role is listed once, at the first time it was
    made; names are matched ignoring case.

    Args:
        reply_plans: The Conversation's Reply Plans, oldest first.

    Returns:
        The Moves made, in the order first made, lead before support.
    """
    made: dict[tuple[str, MoveRole], MoveMade] = {}
    for reply_plan in reply_plans:
        for name, role in (
            (reply_plan.lead_move, MoveRole.LEAD),
            (reply_plan.support_move, MoveRole.SUPPORT),
        ):
            if name and (name.lower(), role) not in made:
                made[(name.lower(), role)] = MoveMade(
                    name=name, role=role, first_made_at=reply_plan.made_at
                )
    return list(made.values())


def describe_reply_plan(
    reply_plan: ReplyPlan, understanding: Understanding | None, time_zone: str | None
) -> str:
    """Write how Zeph read and answered one message, as the keeping model sees it.

    Args:
        reply_plan: The message's Reply Plan.
        understanding: The message's Understanding, for the mood; None if
            there is none.
        time_zone: The User's IANA time zone, for the time.

    Returns:
        E.g. "- 09:00: Accountability; lead Push, support Plan steps; mood
        frustrated (medium)".
    """
    moves = ", ".join(
        f"{role} {name}"
        for role, name in (
            ("lead", reply_plan.lead_move),
            ("support", reply_plan.support_move),
        )
        if name
    )
    mood = (
        f"{understanding.form.mood or 'unclear'} ({understanding.form.intensity.value})"
        if understanding
        else "unclear"
    )
    return (
        f"- {format_time(reply_plan.made_at, time_zone)}: {reply_plan.need}; "
        f"{moves or 'no Move'}; mood {mood}"
    )


def describe_moves_to_judge(
    moves_by_number: dict[int, MoveMade],
    reply_plans: Sequence[ReplyPlan],
    understandings: Sequence[Understanding],
    messages: list[ConversationMessage],
    now: datetime,
    time_zone: str | None,
) -> str:
    """Write what the Move Outcome keeping model is given.

    Args:
        moves_by_number: The Moves made, by the number the model is shown.
        reply_plans: The Conversation's Reply Plans, oldest first.
        understandings: The Conversation's Understandings, each matched to
            its Reply Plan by message.
        messages: The Conversation's messages, oldest first.
        now: The current time.
        time_zone: The User's IANA time zone, for the days and times.

    Returns:
        Today's date, the Moves made, how each message was read and the
        Conversation.
    """
    move_lines = "\n".join(
        f"[{number}] {move.name} ({move.role.value}), first at "
        f"{format_time(move.first_made_at, time_zone)}"
        for number, move in moves_by_number.items()
    )
    understanding_by_message = {
        understanding.message_id: understanding for understanding in understandings
    }
    read_lines = "\n".join(
        describe_reply_plan(
            reply_plan,
            understanding_by_message.get(reply_plan.message_id),
            time_zone,
        )
        for reply_plan in reply_plans
    )
    return (
        f"Today: {format_day(now, time_zone)}\n\n"
        f"Moves Zeph made:\n{move_lines}\n\n"
        f"How Zeph read each message:\n{read_lines}\n\n"
        f"The Conversation:\n{to_transcript_lines(messages, time_zone)}"
    )


def describe_move_outcome(outcome: MoveOutcome, time_zone: str | None) -> str:
    """Write one Move Outcome as the models that read User Memory see it.

    Args:
        outcome: The Move Outcome.
        time_zone: The User's IANA time zone, for the day.

    Returns:
        E.g. "11 Nov 2026: Push (lead) helped. Their launch kept slipping.
        Felt: frustrated. Why: It gave them a next step."
    """
    return (
        f"{format_day(outcome.made_at, time_zone)}: {outcome.move} "
        f"({outcome.role.value}) {RESULT_WORDS[outcome.result]}. "
        f"{outcome.situation} Felt: {outcome.feeling}. Why: {outcome.why}"
    )


def text_to_embed(outcome: MoveOutcome) -> str:
    """Write what a Move Outcome is found by: its situation and feeling.

    Args:
        outcome: The Move Outcome.

    Returns:
        Its situation, then its feeling.
    """
    return f"{outcome.situation} {outcome.feeling}"


def read_move_outcome_keeping_answer(answer: str) -> list[Any] | None:
    """Read the Move Outcomes the keeping model wrote from its JSON answer.

    Text around the JSON object, such as a code fence, is ignored.

    Args:
        answer: The model's answer.

    Returns:
        The Move Outcomes, as the model wrote them; None if it can't be read.
    """
    start, end = answer.find("{"), answer.rfind("}")
    if start == -1 or end < start:
        return None
    try:
        parsed = json.loads(answer[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(parsed, dict) or not isinstance(
        parsed.get("move_outcomes"), list
    ):
        return None
    entries: list[Any] = parsed["move_outcomes"]
    return entries


def plan_move_outcomes(
    entries: list[Any], moves_by_number: dict[int, MoveMade], user_id: UUID
) -> list[MoveOutcome]:
    """Turn the Move Outcomes the model wrote into ones that are safe to save.

    An entry is skipped when it names an unknown Move or one already used,
    has an unknown result, or is missing its situation, feeling or why.

    Args:
        entries: The Move Outcomes, as the model wrote them.
        moves_by_number: The Moves made, by the number the model was shown.
        user_id: The User they are about.

    Returns:
        The Move Outcomes to save.
    """
    planned: list[MoveOutcome] = []
    used_numbers: set[int] = set()
    results = {result.value for result in MoveResult}
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        number = entry.get("move")
        if isinstance(number, bool) or not isinstance(number, int):
            continue
        move = moves_by_number.get(number)
        situation = read_text(entry, "situation")
        feeling = read_text(entry, "feeling")
        why = read_text(entry, "why")
        result = entry.get("result")
        if (
            move is None
            or number in used_numbers
            or result not in results
            or situation is None
            or feeling is None
            or why is None
        ):
            continue
        used_numbers.add(number)
        planned.append(
            MoveOutcome(
                id=uuid4(),
                user_id=user_id,
                move=move.name,
                role=move.role,
                situation=situation,
                feeling=feeling,
                result=MoveResult(result),
                why=why,
                made_at=move.first_made_at,
            )
        )
    return planned


class MoveOutcomeKeeper:
    """Keeps what the Companion learned about each Move when a Conversation ends.

    Each Move Outcome is embedded by its situation and feeling, so it can be
    found by meaning.
    """

    def __init__(
        self,
        repositories: Repositories,
        chat_model: UsageRecordingChatModel,
        embedder: Embedder,
        clock: Clock,
    ) -> None:
        """Set up the keeper.

        Args:
            repositories: Where Reply Plans, Understandings and Move Outcomes are
                stored.
            chat_model: Writes the Move Outcomes and records the tokens used.
            embedder: Embeds each new Move Outcome.
            clock: Tells the current time.
        """
        self._repositories = repositories
        self._chat_model = chat_model
        self._embedder = embedder
        self._clock = clock

    def keep_from(
        self,
        snapshot: UserSnapshot,
        conversation_id: UUID,
        messages: list[ConversationMessage],
    ) -> None:
        """Keep the Move Outcomes of an ended Conversation.

        Nothing is asked when no Move was made. An unreadable answer is asked
        again once; if it is still unreadable nothing is kept. A Move Outcome
        that can't be embedded is still kept.

        Args:
            snapshot: The User whose Conversation it was; User Memory works
                for them.
            conversation_id: The ended Conversation.
            messages: Its messages, oldest first.
        """
        reply_plans = self._repositories.reply_plans.list_for_conversation(
            conversation_id
        )
        moves_by_number = dict(enumerate(list_moves_made(reply_plans), start=1))
        if not moves_by_number:
            return
        entries = self._ask(
            snapshot,
            describe_moves_to_judge(
                moves_by_number,
                reply_plans,
                self._repositories.understandings.list_for_conversation(
                    conversation_id
                ),
                messages,
                self._clock.now(),
                snapshot.user.time_zone,
            ),
        )
        if entries is None:
            logger.warning("Move Outcome keeping gave no readable answer")
            return
        outcomes = plan_move_outcomes(entries, moves_by_number, snapshot.user.id)
        self._repositories.move_outcomes.add_many(self._to_save(outcomes))

    def _to_save(self, outcomes: list[MoveOutcome]) -> list[MoveOutcomeToSave]:
        """Add each Move Outcome's embedding, so it can be found by meaning.

        Args:
            outcomes: The new Move Outcomes.

        Returns:
            Them with their embeddings; none if embedding failed.
        """
        if not outcomes:
            return []
        embeddings: Sequence[list[float] | None]
        try:
            embeddings = self._embedder.embed_passages(
                [text_to_embed(outcome) for outcome in outcomes]
            )
        except Exception:
            logger.exception("Could not embed Move Outcomes")
            embeddings = [None] * len(outcomes)
        return [
            MoveOutcomeToSave(outcome=outcome, embedding=embedding)
            for outcome, embedding in zip(outcomes, embeddings, strict=True)
        ]

    def _ask(self, snapshot: UserSnapshot, description: str) -> list[Any] | None:
        """Ask the model about the Moves, once more if it can't be read.

        Args:
            snapshot: The User whose Conversation it was.
            description: The Moves made and the Conversation.

        Returns:
            The Move Outcomes it wrote, or None if both answers were unreadable.
        """
        settings = snapshot.settings
        for _ in range(2):
            answer = self._chat_model.generate(
                snapshot=snapshot,
                step=ModelStep.MOVE_OUTCOMES,
                model=settings.get(MOVE_OUTCOME_KEEPING_MODEL),
                thinking=thinking_to_use(
                    settings, MOVE_OUTCOME_KEEPING_MODEL, MOVE_OUTCOME_KEEPING_THINKING
                ),
                instructions=settings.get(MOVE_OUTCOME_KEEPING_PROMPT),
                history=[ChatLine(role=ChatRole.USER, text=description)],
            )
            entries = read_move_outcome_keeping_answer(answer)
            if entries is not None:
                return entries
        return None


class MoveOutcomeFinder:
    """Finds the User's past Move Outcomes that fit the Message being answered.

    No model call: one search compares the User's last few texts with the
    situation and feeling of each of their own Move Outcomes. They are used
    even while User Memory is off, since off only stops learning.
    """

    def __init__(self, repositories: Repositories, embedder: Embedder) -> None:
        """Set up the finder.

        Args:
            repositories: Where Conversations and Move Outcomes are stored.
            embedder: Embeds the User's last few texts.
        """
        self._repositories = repositories
        self._embedder = embedder

    def find(self, snapshot: UserSnapshot, conversation_id: UUID) -> list[MoveOutcome]:
        """Find the User's Move Outcomes closest to the Message being answered.

        Only those at least as close as the Admin-set bar count, up to the
        Admin-set number. If the search fails the reply goes ahead without
        them.

        Args:
            snapshot: The User being answered.
            conversation_id: The Conversation the Message is in.

        Returns:
            The Move Outcomes, closest first.
        """
        settings = snapshot.settings
        limit = settings.get(MOVE_OUTCOMES_PER_UNDERSTANDING)
        messages = self._repositories.conversations.list_messages(conversation_id)
        recent_texts = recent_texts_to_search(messages)
        if limit < 1 or not recent_texts:
            return []
        try:
            return self._repositories.move_outcomes.find_by_meaning(
                snapshot.user.id,
                self._embedder.embed_query("\n".join(recent_texts)),
                min_closeness=settings.get(MOVE_OUTCOMES_CLOSENESS_PERCENT) / 100,
                limit=limit,
            )
        except Exception:
            logger.exception("Could not search Move Outcomes")
            return []
