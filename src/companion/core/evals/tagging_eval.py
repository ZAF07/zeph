import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID, uuid4

from companion.core.agenda import OpenNeed, aimed_question
from companion.core.evals.case_shapes import MUST_BE_EMPTY
from companion.core.evals.cases import (
    ExpectedObservation,
    TaggingCase,
    TaggingMessage,
    UnclearStory,
)
from companion.core.evals.made_up_memory import (
    add_ended_conversation,
    to_thread_to_save,
)
from companion.core.evals.made_up_patterns import (
    catalog_pattern_types,
    pattern_type_in_catalog,
    thread_ids_by_title,
    to_observation,
)
from companion.core.evals.models import CaseCheckResult, CaseOutcome, Check
from companion.core.evals.move_outcome_eval import last_call_facts
from companion.core.evals.ports import EvalCompanion, EvalSetupError
from companion.core.evals.understanding_eval import (
    calls_in_new_traces,
    transcript_line,
)
from companion.core.models import (
    Conversation,
    ConversationMessage,
    Curiosity,
    CuriosityAim,
    CuriosityChanges,
    CuriositySensitivity,
    CuriosityState,
    ExplorationApproach,
    ExplorationNeed,
    MessageDirection,
    MessageKind,
    ModelStep,
    Observation,
)
from companion.core.observations import DroppedEntry, PlannedObservations
from companion.core.ports import Repositories

MESSAGE_GAP = timedelta(minutes=1)
ENDED_AFTER = timedelta(hours=1)
NOT_EXPECTED = "Kept but not expected"
CONTEXT_LINE_GROUP = "Context lines"
UNCLEAR_STORIES_GROUP = "Unclear stories"
GENDERED_WORDS = re.compile(
    r"\b(he|she|him|her|his|hers|himself|herself)\b", re.IGNORECASE
)


def save_ended_conversation(
    repositories: Repositories,
    user_id: UUID,
    messages: Sequence[TaggingMessage],
    started_at: datetime,
) -> UUID:
    """Save an ended Conversation, its messages a minute apart from `started_at`.

    Args:
        repositories: Where Conversations are stored.
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
        repositories.conversations.add_message(
            ConversationMessage(
                id=uuid4(),
                conversation_id=conversation.id,
                direction=(
                    MessageDirection.INCOMING
                    if message.from_person
                    else MessageDirection.OUTGOING
                ),
                kind=MessageKind.TEXT,
                content=message.text,
                sent_at=started_at + MESSAGE_GAP * number,
            )
        )
    return conversation.id


def save_unclear_stories(
    repositories: Repositories,
    user_id: UUID,
    stories: Sequence[UnclearStory],
    now: datetime,
) -> list[Observation]:
    """Save the unclear Observations the made-up User already has.

    Each is saved in an ended Conversation of its day, as the tagging step
    would have kept it. A story Zeph asked about gets a waiting aimed
    Curiosity that goes back to it, worded by the Agenda's own code.

    Args:
        repositories: Where Observations and Curiosities are stored.
        user_id: The made-up User's ID; their Life Threads are saved.
        stories: The unclear stories.
        now: When the case's Conversation starts.

    Returns:
        The saved Observations, in the stories' order.

    Raises:
        EvalSetupError: If a Pattern Type or sign isn't in the catalog.
    """
    pattern_types = catalog_pattern_types(repositories)
    thread_ids = thread_ids_by_title(repositories, user_id)
    saved: list[Observation] = []
    asking: list[Curiosity] = []
    for story in stories:
        said_at = now - timedelta(days=story.observation.days_ago)
        pattern_type = pattern_type_in_catalog(pattern_types, story.pattern_type)
        observation = to_observation(
            user_id,
            pattern_type,
            story.observation,
            pattern_types,
            thread_ids,
            add_ended_conversation(repositories, user_id, said_at),
            said_at,
        )
        saved.append(observation)
        if story.asked:
            question, why = aimed_question(
                OpenNeed(ExplorationNeed.UNCLEAR, observation=observation),
                ExplorationApproach.STORY_FOLLOW_UP,
                pattern_type,
            )
            asking.append(
                Curiosity(
                    id=uuid4(),
                    user_id=user_id,
                    question=question,
                    why=why,
                    not_before=None,
                    sensitivity=CuriositySensitivity.MEDIUM,
                    state=CuriosityState.WAITING,
                    created_at=said_at,
                    aim=CuriosityAim.EXPLORATION,
                    source_observation_id=observation.id,
                )
            )
    repositories.observations.add_many(saved)
    repositories.curiosities.save_changes(
        CuriosityChanges(added=asking, updated=[], reactions={})
    )
    return saved


def describe_ending(pattern_type: str | None) -> str:
    """Say how an unclear story ended, or must end.

    Args:
        pattern_type: The Pattern Type it is clear for; None while unclear.

    Returns:
        E.g. "clear for CONF.AVOID.BELONG" or "unclear".
    """
    return f"clear for {pattern_type}" if pattern_type else "unclear"


def unclear_story_facts(
    story: UnclearStory, after: Observation | None
) -> dict[str, Any]:
    """Write how an unclear story ended, for the result.

    Args:
        story: The unclear story and how it must end.
        after: Its Observation after tagging; None if it is gone, which
            reads as still unclear (the tagging step deletes none).

    Returns:
        Its quote, its two Pattern Types, whether Zeph asked about it, the
        Pattern Type and sign it ended clear for (None while unclear), the
        Pattern Type expected (None to stay unclear) and whether they agree.
    """
    settled = after is not None and not after.unclear
    ended_clear_for = after.pattern_type_id if after and settled else None
    return {
        "quote": story.observation.quote,
        "pattern_types": story.pattern_types,
        "direction": story.observation.direction.value,
        "asked": story.asked,
        "ended_clear_for": ended_clear_for,
        "sign": after.sign_id if after and settled else None,
        "expected_clear_for": story.ends_clear_for,
        "matched": ended_clear_for == story.ends_clear_for,
    }


def check_unclear_stories(facts: Sequence[Mapping[str, Any]]) -> list[Check]:
    """Check each unclear story ended clear or stayed unclear, as expected.

    Args:
        facts: How each story ended (see `unclear_story_facts`).

    Returns:
        One check per story, named by its quote.
    """
    return [
        Check(
            f'"{story["quote"]}"',
            story["matched"],
            f"ended {describe_ending(story['ended_clear_for'])}"
            + (
                ""
                if story["matched"]
                else f", expected {describe_ending(story['expected_clear_for'])}"
            ),
            UNCLEAR_STORIES_GROUP,
        )
        for story in facts
    ]


def named_pattern_types(observation: Observation) -> list[str]:
    """List the Pattern Types an Observation names.

    Args:
        observation: The kept Observation.

    Returns:
        Its Pattern Type's ID, then, when unclear, the second one's.
    """
    second = observation.second_pattern_type_id
    return [observation.pattern_type_id, *([second] if second else [])]


def observation_label(observation: Observation) -> str:
    """Name a kept Observation the way expected ones are named.

    Args:
        observation: The kept Observation.

    Returns:
        E.g. "CONF.AVOID.BELONG · for · situational".
    """
    return ExpectedObservation(
        pattern_type=observation.pattern_type_id,
        direction=observation.direction,
        unclear=observation.unclear,
        situational=observation.situational,
    ).label


def kept_conditions(observation: Observation) -> dict[str, str | None]:
    """List the Conditions a kept Observation holds that a case can expect.

    Args:
        observation: The kept Observation.

    Returns:
        Its audience, stakes and state going in, by name; None for one
        left empty.
    """
    tags = observation.tags
    return {
        "audience": tags.audience.value if tags.audience else None,
        "stakes": tags.stakes.value if tags.stakes else None,
        "state_going_in": tags.state_going_in.value if tags.state_going_in else None,
    }


def conditions_match(expected: ExpectedObservation, observation: Observation) -> bool:
    """Say whether a kept Observation holds the Conditions a case states.

    Args:
        expected: The Observation expected.
        observation: One kept.

    Returns:
        True when every Condition the case states is the one kept, or is
        empty where the case says it must be; one it doesn't state may
        hold anything.
    """
    kept = kept_conditions(observation)
    return all(
        kept[name] == (None if value == MUST_BE_EMPTY else value)
        for name, value in expected.conditions.items()
    )


def matches(expected: ExpectedObservation, observation: Observation) -> bool:
    """Say whether a kept Observation is the one expected.

    Args:
        expected: The Observation expected.
        observation: One kept.

    Returns:
        True when they agree on for or against, unclear and situational,
        the expected Pattern Type is the one kept, or, when unclear, either
        of its two, and it holds the Conditions the case states.
    """
    return (
        expected.pattern_type in named_pattern_types(observation)
        and expected.direction == observation.direction
        and expected.unclear == observation.unclear
        and expected.situational == observation.situational
        and conditions_match(expected, observation)
    )


def check_kept(
    expected: Sequence[ExpectedObservation], kept: Sequence[Observation]
) -> list[Check]:
    """Check the Observations kept are exactly the kinds expected.

    Args:
        expected: The Observations expected.
        kept: The Observations kept.

    Returns:
        One check per expected Observation, whether one like it was kept;
        then a failed check per kept one that matches none expected. With
        none expected and none kept, one passed "nothing kept" check.
    """
    checks = []
    for expectation in expected:
        quotes = [
            observation.quote
            for observation in kept
            if matches(expectation, observation)
        ]
        checks.append(
            Check(
                "kept",
                bool(quotes),
                f"kept {len(quotes)}: " + " / ".join(f'"{quote}"' for quote in quotes)
                if quotes
                else "nothing kept like it",
                expectation.label,
            )
        )
    checks += [
        Check(
            observation_label(observation),
            False,
            f'"{observation.quote}"',
            NOT_EXPECTED,
        )
        for observation in kept
        if not any(matches(expectation, observation) for expectation in expected)
    ]
    if not checks:
        checks.append(Check("nothing kept", True, "nothing to tag, and nothing kept"))
    return checks


def gendered_words(context: str) -> list[str]:
    """Find the he or she words in a context line.

    Context lines are shown to Users, so they never guess anyone's gender.
    Code can't tell who a pronoun means, so any of them counts.

    Args:
        context: The context line.

    Returns:
        Each he or she word in it, lowercased, once, in the order found.
    """
    return list(dict.fromkeys(word.lower() for word in GENDERED_WORDS.findall(context)))


def check_context_lines(kept: Sequence[Observation]) -> list[Check]:
    """Check no kept Observation's context line says he or she.

    Args:
        kept: The Observations kept.

    Returns:
        A failed check per context line that does, naming the words.
    """
    checks = []
    for observation in kept:
        words = gendered_words(observation.context)
        if words:
            checks.append(
                Check(
                    "no he or she",
                    False,
                    f'"{observation.context}" says {", ".join(words)}',
                    CONTEXT_LINE_GROUP,
                )
            )
    return checks


def kept_facts(
    observation: Observation,
    expected: Sequence[ExpectedObservation],
    thread_titles: Mapping[UUID, str],
) -> dict[str, Any]:
    """Write a kept Observation for the result.

    Args:
        observation: The kept Observation.
        expected: The Observations expected.
        thread_titles: The touched Life Threads' titles, by ID.

    Returns:
        Its Pattern Types, sign, direction, unclear, situational, quote,
        context, who it is about, its Thread's title (None for none), its
        audience, stakes and state going in, and whether it matches one
        expected.
    """
    return {
        "pattern_types": named_pattern_types(observation),
        "sign": observation.sign_id,
        "direction": observation.direction.value,
        "unclear": observation.unclear,
        "situational": observation.situational,
        "quote": observation.quote,
        "context": observation.context,
        "about": observation.about,
        "thread": (
            thread_titles.get(observation.thread_id) if observation.thread_id else None
        ),
        "conditions": kept_conditions(observation),
        "expected": any(matches(expectation, observation) for expectation in expected),
    }


def written_text(entry: Mapping[str, Any], key: str) -> str:
    """Read one value of a dropped entry as text, whatever the model wrote.

    Args:
        entry: The entry, as the model wrote it.
        key: The value's name.

    Returns:
        The value as text; "" when missing.
    """
    value = entry.get(key)
    return "" if value is None else str(value)


def dropped_facts(dropped: DroppedEntry) -> dict[str, Any]:
    """Write a dropped entry for the result.

    Args:
        dropped: The entry the model wrote and why code dropped it.

    Returns:
        Its Pattern Types, sign, direction and quote as written, and why.
    """
    entry = dropped.entry if isinstance(dropped.entry, Mapping) else {}
    pattern_types = entry.get("pattern_types")
    return {
        "pattern_types": (
            [str(name) for name in pattern_types]
            if isinstance(pattern_types, list)
            else []
        ),
        "sign": written_text(entry, "sign"),
        "direction": written_text(entry, "direction"),
        "quote": written_text(entry, "quote") or ("" if entry else str(dropped.entry)),
        "reason": dropped.reason.value,
    }


def tagging_facts(
    planned: PlannedObservations | None,
    expected: Sequence[ExpectedObservation],
    thread_titles: Mapping[UUID, str],
    unclear: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Write what the tagging step kept and dropped, against what was expected.

    Args:
        planned: What the step kept and dropped; None if its answer
            couldn't be read.
        expected: The Observations expected.
        thread_titles: The touched Life Threads' titles, by ID.
        unclear: How each unclear story the User already had ended.

    Returns:
        `answered`, `kept`, `dropped`, `expected` (each with `matched`) and
        `unclear`.
    """
    kept = planned.kept if planned else []
    return {
        "answered": planned is not None,
        "kept": [kept_facts(item, expected, thread_titles) for item in kept],
        "dropped": [dropped_facts(item) for item in planned.dropped_entries]
        if planned
        else [],
        "expected": [
            {
                "pattern_type": expectation.pattern_type,
                "direction": expectation.direction.value,
                "unclear": expectation.unclear,
                "situational": expectation.situational,
                "conditions": expectation.conditions,
                "matched": any(matches(expectation, item) for item in kept),
            }
            for expectation in expected
        ],
        "unclear": list(unclear),
    }


def check_tagging_case(case: TaggingCase, companion: EvalCompanion) -> CaseCheckResult:
    """Tag Observations from an ended Conversation and check those kept.

    The made-up User has Pattern noticing on and has been told. Their Life
    Threads, the unclear stories they already have and the Conversation are
    saved as if they had happened, with each story Zeph asked about raised
    in the Conversation by an aimed Curiosity. Then the real tagging step
    runs alone an hour after the last message, with the Threads as the ones
    the Conversation touched.

    Args:
        case: The ended Conversation and the Observations expected.
        companion: The app on the Eval database.

    Returns:
        A check per expected Observation, per one kept but not expected, per
        kept context line that says he or she and per unclear story;
        a failed "answer read" check alone if the answer couldn't be read.
        Its facts hold what was kept and dropped and the tagging call's
        time and tokens. A failed case notes the Observations and the
        Conversation.

    Raises:
        EvalSetupError: If the tagging step didn't run at all, e.g. with an
            empty Pattern Catalog, or an unclear story names a Pattern Type
            or sign the catalog doesn't have, so the case is an Error, not
            a Fail.
    """
    companion.move_clock(case.now - companion.now())
    user_id = companion.connect_user()
    companion.turn_pattern_noticing_on()
    repositories = companion.repositories
    now = companion.now()
    threads = [
        to_thread_to_save(companion.embedder, user_id, thread, now, None)
        for thread in case.threads
    ]
    repositories.life_threads.save_many(added=threads, changed=[])
    touched = [saved.thread for saved in threads]
    stories = save_unclear_stories(repositories, user_id, case.unclear, now)
    conversation_id = save_ended_conversation(repositories, user_id, case.messages, now)
    repositories.curiosities.mark_raised(
        [
            curiosity.id
            for curiosity in repositories.curiosities.list_waiting(user_id)
            if curiosity.aim == CuriosityAim.EXPLORATION
        ],
        conversation_id,
        now,
    )
    companion.move_clock(MESSAGE_GAP * len(case.messages) + ENDED_AFTER)
    seen_trace_ids: set[UUID] = set()
    calls_in_new_traces(repositories, user_id, seen_trace_ids)
    planned = companion.tag_observations(conversation_id, touched)
    tagging_calls = calls_in_new_traces(repositories, user_id, seen_trace_ids)
    if planned is None and not any(
        call.step == ModelStep.PATTERN_TAGGING for call in tagging_calls
    ):
        raise EvalSetupError("The tagging step didn't run for the made-up User")

    after = {
        observation.id: observation
        for observation in repositories.observations.list_for_user(user_id)
    }
    unclear = [
        unclear_story_facts(story, after.get(saved.id))
        for story, saved in zip(case.unclear, stories, strict=True)
    ]
    checks = (
        check_kept(case.observations, planned.kept)
        + check_context_lines(planned.kept)
        + check_unclear_stories(unclear)
        if planned is not None
        else [
            Check("answer read", False, "the tagging model's answer couldn't be read")
        ]
    )
    passed = all(check.passed for check in checks)
    facts = tagging_facts(
        planned,
        case.observations,
        {thread.id: thread.title for thread in touched},
        unclear,
    )
    return CaseCheckResult(
        outcome=CaseOutcome.PASS if passed else CaseOutcome.FAIL,
        checks=checks,
        facts={
            "tagging": facts,
            "call": last_call_facts(tagging_calls, ModelStep.PATTERN_TAGGING),
        },
        notes=(
            []
            if passed
            else [
                "Observations kept:",
                *(
                    f"{' + '.join(item['pattern_types'])} {item['sign']} "
                    f'{item["direction"]}: "{item["quote"]}"'
                    for item in facts["kept"]
                ),
                "Dropped:",
                *(f'"{item["quote"]}": {item["reason"]}' for item in facts["dropped"]),
                *(["Unclear stories:"] if unclear else []),
                *(
                    f'"{item["quote"]}": ended '
                    f"{describe_ending(item['ended_clear_for'])}"
                    for item in unclear
                ),
                "",
                *(
                    transcript_line(message.from_person, message.text)
                    for message in case.messages
                ),
            ]
        ),
    )
