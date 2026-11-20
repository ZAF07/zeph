from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from companion.core.evals.cases import DaySummaryCase, DaySummaryMessage
from companion.core.evals.judge import (
    AnswerMark,
    JudgeSettings,
    judge_day_summary_answers,
    judge_day_summary_marks,
)
from companion.core.evals.models import CaseCheckResult, CaseOutcome, Check
from companion.core.evals.ports import EvalCompanion
from companion.core.evals.understanding_eval import transcript_line
from companion.core.memory_retrieval import summary_line
from companion.core.models import (
    Conversation,
    ConversationMessage,
    MessageDirection,
    MessageKind,
)
from companion.core.platform_settings import CONVERSATION_QUIET_GAP
from companion.core.ports import Repositories

MADE_UP_DAY = date(2026, 11, 19)
NO_SUMMARY = "No Day Summary was written."


def calendar_time(message: DaySummaryMessage) -> datetime:
    """Place a message of the made-up day on the calendar.

    Args:
        message: The message.

    Returns:
        Its time on the made-up day, in UTC; the made-up User has no time
        zone, so UTC is theirs too.
    """
    return datetime.combine(MADE_UP_DAY, message.sent_at, UTC)


def split_into_conversations(
    messages: Sequence[DaySummaryMessage], quiet_gap: timedelta
) -> list[list[DaySummaryMessage]]:
    """Split the day's messages into Conversations where it went quiet.

    Args:
        messages: The day's messages, in order.
        quiet_gap: How long a quiet spell ends a Conversation.

    Returns:
        Each Conversation's messages, in order; a new one starts after a gap
        at least as long as the quiet gap.
    """
    conversations: list[list[DaySummaryMessage]] = []
    for message in messages:
        if (
            conversations
            and calendar_time(message) - calendar_time(conversations[-1][-1])
            < quiet_gap
        ):
            conversations[-1].append(message)
        else:
            conversations.append([message])
    return conversations


def save_day(
    repositories: Repositories,
    user_id: UUID,
    conversations: Sequence[Sequence[DaySummaryMessage]],
) -> None:
    """Save the made-up day's Conversations as if they had happened.

    Args:
        repositories: Where Conversations are stored.
        user_id: The User's ID.
        conversations: Each Conversation's messages, in order.
    """
    for messages in conversations:
        conversation_id = uuid4()
        repositories.conversations.add(
            Conversation(
                id=conversation_id,
                user_id=user_id,
                started_at=calendar_time(messages[0]),
                last_message_at=calendar_time(messages[-1]),
            )
        )
        for message in messages:
            repositories.conversations.add_message(
                ConversationMessage(
                    id=uuid4(),
                    conversation_id=conversation_id,
                    direction=(
                        MessageDirection.INCOMING
                        if message.from_person
                        else MessageDirection.OUTGOING
                    ),
                    kind=MessageKind.TEXT,
                    content=message.text,
                    sent_at=calendar_time(message),
                )
            )


def answer_facts(
    case: DaySummaryCase, answers: Sequence[str], marks: Sequence[AnswerMark]
) -> list[dict[str, Any]]:
    """Write each question's answer and mark for the report.

    Args:
        case: The case, for its questions.
        answers: The Judge's answer to each question, in order.
        marks: The Judge's mark on each answer, in order.

    Returns:
        Each question, its expected answer, the Judge's answer, whether it
        matched and why.
    """
    return [
        {
            "question": question.question,
            "expected": question.expected,
            "answer": answer,
            "matched": mark.matched,
            "reason": mark.reason,
        }
        for question, answer, mark in zip(case.questions, answers, marks, strict=True)
    ]


def check_day_summary_case(
    case: DaySummaryCase, companion: EvalCompanion, judge: JudgeSettings
) -> CaseCheckResult:
    """Write a made-up day's Day Summary and check it answers the questions.

    The day is saved as if it had happened, split into Conversations where
    it went quiet, then the real Day Summary step runs on its last
    Conversation once the quiet gap has passed, so it reads the whole day.
    The Judge answers every question from the Summary alone, then marks
    each answer against the answer expected.

    Args:
        case: The made-up day and its questions.
        companion: The app on the Eval database.
        judge: The Judge's model, thinking and prompts.

    Returns:
        One check per question, passed when its answer matched; its facts
        hold the Summary and each answer. A failed case notes the Summary
        and the day.
    """
    user_id = companion.connect_user()
    repositories = companion.repositories
    quiet_gap = repositories.platform_settings.load().get(CONVERSATION_QUIET_GAP)
    save_day(repositories, user_id, split_into_conversations(case.messages, quiet_gap))
    companion.move_clock(calendar_time(case.messages[-1]) + quiet_gap - companion.now())
    companion.write_day_summary()

    summaries = repositories.user_memory.list_summaries(user_id, limit=1)
    summary = summary_line(summaries[0]).removeprefix("- ") if summaries else ""
    questions = [question.question for question in case.questions]
    if summary:
        answers = judge_day_summary_answers(
            companion.judge_chat_model, judge, summary, questions
        )
        marks = judge_day_summary_marks(
            companion.judge_chat_model,
            judge,
            summary,
            [
                (question.question, question.expected, answer)
                for question, answer in zip(case.questions, answers, strict=True)
            ],
        )
    else:
        answers = ["" for _ in questions]
        marks = [AnswerMark(False, NO_SUMMARY) for _ in questions]

    checks = [
        Check(question, mark.matched, mark.reason)
        for question, mark in zip(questions, marks, strict=True)
    ]
    passed = all(check.passed for check in checks)
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks=checks,
        facts={"summary": summary, "answers": answer_facts(case, answers, marks)},
        notes=(
            []
            if passed
            else [
                "Day Summary written:",
                summary or NO_SUMMARY,
                "",
                *(
                    transcript_line(message.from_person, message.text)
                    for message in case.messages
                ),
            ]
        ),
    )
