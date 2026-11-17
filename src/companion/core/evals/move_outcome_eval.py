from collections.abc import Sequence
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from companion.core.evals.cases import (
    ExpectedMoveOutcome,
    MoveOutcomeCase,
    MoveOutcomeMessage,
)
from companion.core.evals.judge import JudgeSettings, judge_move_outcome_rules
from companion.core.evals.models import CaseCheckResult, CaseOutcome, Check
from companion.core.evals.persona_eval import verdict_check
from companion.core.evals.ports import EvalCompanion
from companion.core.evals.understanding_eval import transcript_line
from companion.core.models import (
    Conversation,
    ConversationMessage,
    MessageDirection,
    MessageKind,
    MoodIntensity,
    MoveOutcome,
    MoveResult,
    Understanding,
    UnderstandingForm,
)
from companion.core.move_outcomes import describe_move_outcome
from companion.core.ports import ChatModel, Repositories

MESSAGE_GAP = timedelta(minutes=1)
ENDED_AFTER = timedelta(hours=1)
NOT_KEPT = "no Move Outcome kept to judge"
RESULT_NAMES = {
    MoveResult.HELPED: "helped",
    MoveResult.DIDNT_HELP: "didn't help",
    MoveResult.MIXED: "mixed",
}


def understanding_of(
    message: MoveOutcomeMessage,
    user_id: UUID,
    conversation_id: UUID,
    message_id: UUID,
    made_at: datetime,
) -> Understanding:
    """Build the Understanding Zeph made of one of the User's messages.

    Args:
        message: The message, with its Need, Moves and mood.
        user_id: The User's ID.
        conversation_id: The Conversation it is in.
        message_id: The saved message's ID.
        made_at: When the message was sent.

    Returns:
        The Understanding, its mood felt at medium strength.
    """
    return Understanding(
        id=uuid4(),
        user_id=user_id,
        conversation_id=conversation_id,
        message_id=message_id,
        form=UnderstandingForm(
            need=message.need,
            nuance="",
            mood=message.mood,
            intensity=MoodIntensity.MEDIUM,
            cause_known=False,
            lead_move=message.lead_move,
            support_move=message.support_move,
        ),
        need=message.need,
        asked_why=False,
        made_at=made_at,
        lead_move=message.lead_move or None,
        support_move=message.support_move or None,
    )


def save_finished_conversation(
    repositories: Repositories,
    user_id: UUID,
    messages: Sequence[MoveOutcomeMessage],
    started_at: datetime,
) -> UUID:
    """Save a finished Conversation and an Understanding of each User message.

    The messages are a minute apart, from `started_at`.

    Args:
        repositories: Where Conversations and Understandings are stored.
        user_id: The User's ID.
        messages: The Conversation, oldest first.
        started_at: When the first message was sent.

    Returns:
        The Conversation's ID.
    """
    conversation = Conversation(
        id=uuid4(),
        user_id=user_id,
        started_at=started_at,
        last_message_at=started_at + MESSAGE_GAP * (len(messages) - 1),
    )
    repositories.conversations.add(conversation)
    for number, message in enumerate(messages):
        sent_at = started_at + MESSAGE_GAP * number
        saved = ConversationMessage(
            id=uuid4(),
            conversation_id=conversation.id,
            direction=(
                MessageDirection.INCOMING
                if message.from_person
                else MessageDirection.OUTGOING
            ),
            kind=MessageKind.TEXT,
            content=message.text,
            sent_at=sent_at,
        )
        repositories.conversations.add_message(saved)
        if message.from_person:
            repositories.understandings.add(
                understanding_of(message, user_id, conversation.id, saved.id, sent_at)
            )
    return conversation.id


def find_kept(
    expected: ExpectedMoveOutcome, kept: Sequence[MoveOutcome]
) -> MoveOutcome | None:
    """Find the kept Move Outcome of the expected Move and role.

    Args:
        expected: The Move Outcome expected.
        kept: The Move Outcomes kept.

    Returns:
        The one with the same Move, ignoring case, and role; None if none.
    """
    return next(
        (
            outcome
            for outcome in kept
            if outcome.move.lower() == expected.move.lower()
            and outcome.role == expected.role
        ),
        None,
    )


def check_expected_outcome(
    expected: ExpectedMoveOutcome,
    kept: Sequence[MoveOutcome],
    case: MoveOutcomeCase,
    transcript: str,
    judge_chat_model: ChatModel,
    judge: JudgeSettings,
) -> list[Check]:
    """Check one expected Move Outcome was kept, with its result and rules.

    Args:
        expected: The Move Outcome expected.
        kept: The Move Outcomes kept.
        case: The case, for its rules.
        transcript: The Conversation, for the Judge.
        judge_chat_model: The model that judges.
        judge: The Judge's model, thinking and prompts.

    Returns:
        Whether it was kept, its result when one is expected, then each
        rule; with nothing kept, each rule fails without asking the Judge.
    """
    group = expected.label
    outcome = find_kept(expected, kept)
    if outcome is None:
        return [
            Check("kept", False, f"no Move Outcome kept for {group}", group),
            *(Check(rule, False, NOT_KEPT, group) for rule in expected.rules),
        ]
    checks = [Check("kept", True, f"kept {group}", group)]
    if expected.result is not None:
        kept_name = RESULT_NAMES[outcome.result]
        checks.append(
            Check("result", True, kept_name, group)
            if outcome.result == expected.result
            else Check(
                "result",
                False,
                f"expected {RESULT_NAMES[expected.result]}, kept {kept_name}",
                group,
            )
        )
    if expected.rules:
        verdicts = judge_move_outcome_rules(
            judge_chat_model,
            judge,
            transcript,
            describe_move_outcome(outcome, None),
            {rule: case.rules[rule] for rule in expected.rules},
        )
        checks += [verdict_check(verdict, group=group) for verdict in verdicts]
    return checks


def outcome_facts(outcome: MoveOutcome) -> dict[str, str]:
    """Write a kept Move Outcome for the report.

    Args:
        outcome: The Move Outcome.

    Returns:
        Its Move, role, result, situation, feeling and why.
    """
    return {
        "move": outcome.move,
        "role": outcome.role.value,
        "result": outcome.result.value,
        "situation": outcome.situation,
        "feeling": outcome.feeling,
        "why": outcome.why,
    }


def check_move_outcome_case(
    case: MoveOutcomeCase, companion: EvalCompanion, judge: JudgeSettings
) -> CaseCheckResult:
    """Keep Move Outcomes from a finished Conversation and check them.

    The made-up User's Conversation and Understandings are saved as if
    they had happened, then the real Move Outcome keeping step runs an hour
    after the last message, as the quiet gap would run it.

    Args:
        case: The finished Conversation and the Move Outcomes expected.
        companion: The app on the Eval database.
        judge: The Judge's model, thinking and prompts.

    Returns:
        Each expected Move Outcome's checks, grouped by Move and role; its
        facts hold every Move Outcome kept. A failed case notes them and
        the Conversation.
    """
    companion.move_clock(case.now - companion.now())
    user_id = companion.connect_user()
    repositories = companion.repositories
    conversation_id = save_finished_conversation(
        repositories, user_id, case.messages, companion.now()
    )
    companion.move_clock(MESSAGE_GAP * len(case.messages) + ENDED_AFTER)
    companion.keep_move_outcomes(conversation_id)

    kept = repositories.move_outcomes.list_for_user(user_id)
    transcript_lines = [
        transcript_line(message.from_person, message.text) for message in case.messages
    ]
    transcript = "\n".join(transcript_lines)
    checks = [
        check
        for expected in case.outcomes
        for check in check_expected_outcome(
            expected, kept, case, transcript, companion.judge_chat_model, judge
        )
    ]
    passed = all(check.passed for check in checks)
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks=checks,
        facts={"outcomes": [outcome_facts(outcome) for outcome in kept]},
        notes=(
            []
            if passed
            else [
                "Move Outcomes kept:",
                *(describe_move_outcome(outcome, None) for outcome in kept),
                "",
                *transcript_lines,
            ]
        ),
    )
