from dataclasses import replace
from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

import pytest

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.models import (
    ChannelPhoto,
    ConversationMessage,
    EvidenceKind,
    ExcludedEvidence,
    LifeThread,
    MessageDirection,
    MessageKind,
    ObservationDirection,
    Power,
    Relationship,
    SituationMatch,
    SituationSetting,
    SituationTags,
    Stance,
)
from companion.core.observations import (
    DroppedEntry,
    DropReason,
    TaggingContext,
    deleted_quotes_of,
    hash_of_quote,
    ignored_pattern_types,
    is_situational,
    plan_exclusion_flags,
    plan_observations,
    plan_settled,
    read_exclusions_answer,
    read_settled_answer,
    read_tagging_answer,
    users_own_texts,
)
from companion.core.pattern_catalog import read_pattern_types
from tests.conftest import PATTERN_CATALOG_DIR

CONVERSATION_ID = uuid4()
SENT_AT = datetime(2026, 11, 24, 15, 30, tzinfo=UTC)
PATTERN_TYPES = {
    pattern_type.id: pattern_type
    for pattern_type in read_pattern_types(
        read_pattern_catalog_seed(PATTERN_CATALOG_DIR)
    )
}
MEI = LifeThread(
    id=uuid4(),
    user_id=uuid4(),
    title="Falling-out with Mei",
    story="They keep agreeing with Mei and resenting it.",
    people=("Mei",),
    is_open=True,
    started_at=SENT_AT,
    updated_at=SENT_AT,
)


def message(
    content: str,
    direction: MessageDirection = MessageDirection.INCOMING,
    kind: MessageKind = MessageKind.TEXT,
    photos: tuple[ChannelPhoto, ...] = (),
) -> ConversationMessage:
    """A saved message of the Conversation."""
    return ConversationMessage(
        id=uuid4(),
        conversation_id=CONVERSATION_ID,
        direction=direction,
        kind=kind,
        content=content,
        sent_at=SENT_AT,
        photos=photos,
    )


MESSAGES = [
    message("I said yes to Mei again. It’s fine, honestly"),
    message("you always say it's fine", direction=MessageDirection.OUTGOING),
    message("and then I stewed on it all night"),
]


def context(messages: list[ConversationMessage] = MESSAGES) -> TaggingContext:
    """What the checks run against: the seed catalog and one Thread."""
    return TaggingContext(
        user_id=MEI.user_id,
        conversation_id=CONVERSATION_ID,
        pattern_types=PATTERN_TYPES,
        threads={1: MEI},
        user_texts=users_own_texts(messages),
        time_zone="Asia/Singapore",
        now=SENT_AT,
    )


def entry(**changes: Any) -> dict[str, Any]:
    """One Observation as the tagging model writes it, with some fields changed."""
    return {
        "pattern_types": ["CONF.AVOID.BELONG"],
        "sign": "I2",
        "direction": "for",
        "quote": "I said yes to Mei again",
        "context": "Agreed to help Mei move, again, then resented it.",
        "about": "Mei, their sister",
        "thread": 1,
        "relationship": "family",
        "power": "equal",
        "setting": "home",
        "stance": "neutral",
        "evidence": "real_story",
        **changes,
    }


def test_a_quote_the_user_deleted_is_dropped_and_its_record_holds_no_words() -> None:
    [kept] = plan_observations([entry()], context()).kept
    [record] = deleted_quotes_of([kept], SENT_AT)
    deleted = replace(context(), deleted_quote_hashes=frozenset({record.quote_hash}))

    planned = plan_observations(
        [entry(quote="I said  yes to Mei again"), entry(quote="It’s fine, honestly")],
        deleted,
    )

    assert (record.user_id, record.conversation_id) == (MEI.user_id, CONVERSATION_ID)
    assert record.quote_hash == hash_of_quote("I said yes to Mei again")
    assert "Mei" not in record.quote_hash
    assert [observation.quote for observation in planned.kept] == [
        "It’s fine, honestly"
    ]
    assert [dropped.reason for dropped in planned.dropped_entries] == [
        DropReason.DELETED_BY_USER
    ]


def test_a_valid_observation_is_kept_with_everything_it_needs() -> None:
    planned = plan_observations([entry()], context())

    [observation] = planned.kept
    assert planned.dropped == 0
    assert observation.pattern_type_id == "CONF.AVOID.BELONG"
    assert observation.pattern_type_version == "0.4.0"
    assert observation.sign_id == "I2"
    assert observation.direction == ObservationDirection.FOR
    assert observation.quote == "I said yes to Mei again"
    assert observation.context == "Agreed to help Mei move, again, then resented it."
    assert observation.about == "Mei, their sister"
    assert observation.thread_id == MEI.id
    assert observation.tags == SituationTags(
        relationship=Relationship.FAMILY,
        power=Power.EQUAL,
        setting=SituationSetting.HOME,
        stance=Stance.NEUTRAL,
    )
    assert observation.evidence_kind == EvidenceKind.REAL_STORY
    assert observation.day == date(2026, 11, 24)
    assert not observation.unclear
    assert not observation.situational
    assert observation.conversation_id == CONVERSATION_ID


def test_the_day_is_the_users_day_when_they_said_it() -> None:
    late = [
        ConversationMessage(
            id=uuid4(),
            conversation_id=CONVERSATION_ID,
            direction=MessageDirection.INCOMING,
            kind=MessageKind.TEXT,
            content="I said yes to Mei again",
            sent_at=datetime(2026, 11, 24, 17, 0, tzinfo=UTC),
        )
    ]

    [observation] = plan_observations([entry()], context(late)).kept

    assert observation.day == date(2026, 11, 25)


@pytest.mark.parametrize(
    "changes",
    [
        {"pattern_types": ["CONF.NOT.THERE"]},
        {"pattern_types": []},
        {"pattern_types": ["CONF.AVOID.BELONG", "ACH.WORTH.PERF", "CTRL.UNCERT.PLAN"]},
        {"pattern_types": ["CONF.AVOID.BELONG", "CONF.AVOID.BELONG"]},
        {"pattern_types": ["CONF.AVOID.BELONG", "ACH.NOT.THERE"]},
        {"sign": "I9"},
        {"sign": "D1"},
        {"direction": "against", "sign": "I2"},
        {"direction": "sideways"},
        {"quote": "I said no to Mei"},
        {"quote": "you always say it's fine"},
        {"quote": ""},
        {"relationship": "boss"},
        {"power": "over"},
        {"setting": "gym"},
        {"stance": "angry"},
        {"evidence": "rumour"},
        {"evidence": None},
        {"about": ""},
        {"context": None},
    ],
)
def test_an_observation_that_fails_a_check_is_dropped(changes: dict[str, Any]) -> None:
    planned = plan_observations([entry(**changes)], context())

    assert (planned.kept, planned.dropped) == ([], 1)


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"pattern_types": ["CONF.NOT.THERE"]}, DropReason.UNKNOWN_PATTERN_TYPE),
        ({"sign": "I9"}, DropReason.UNKNOWN_SIGN),
        ({"direction": "sideways"}, DropReason.UNKNOWN_SIGN),
        ({"quote": "I said no to Mei"}, DropReason.QUOTE_NOT_WORD_FOR_WORD),
        ({"quote": ""}, DropReason.QUOTE_NOT_WORD_FOR_WORD),
        ({"stance": "angry"}, DropReason.TAG_OFF_ITS_LIST),
        ({"evidence": "rumour"}, DropReason.TAG_OFF_ITS_LIST),
        ({"about": ""}, DropReason.MISSING_DETAILS),
        ({"context": None}, DropReason.MISSING_DETAILS),
    ],
)
def test_each_dropped_entry_comes_back_with_why_it_was_dropped(
    changes: dict[str, Any], reason: DropReason
) -> None:
    written = entry(**changes)

    planned = plan_observations([written], context())

    assert planned.dropped_entries == [DroppedEntry(written, reason)]


def test_a_repeat_and_an_entry_that_is_not_an_observation_say_why() -> None:
    planned = plan_observations([entry(), entry(), "a quote"], context())

    assert [dropped.reason for dropped in planned.dropped_entries] == [
        DropReason.REPEAT,
        DropReason.NOT_AN_OBSERVATION,
    ]
    assert planned.dropped == 2


def test_a_sign_against_counts_against() -> None:
    [observation] = plan_observations(
        [entry(direction="against", sign="D1")], context()
    ).kept

    assert observation.direction == ObservationDirection.AGAINST
    assert observation.sign_id == "D1"


def test_a_quote_is_matched_with_spaces_and_curly_quotes_evened_out() -> None:
    [observation] = plan_observations(
        [entry(quote="It's  fine,\nhonestly")], context()
    ).kept

    assert observation.quote == "It's  fine,\nhonestly"


def test_a_quote_split_across_two_texts_is_dropped() -> None:
    quote = "It’s fine, honestly and then I stewed"

    assert plan_observations([entry(quote=quote)], context()).dropped == 1


def test_a_photo_caption_is_the_users_own_words_but_its_description_is_not() -> None:
    photo = ChannelPhoto(
        file_id="file",
        file_unique_id="unique",
        description="a messy kitchen after a party",
        caption="cleaned up after everyone again",
        viewed=True,
    )
    messages = [
        message(
            "[photo: a messy kitchen after a party] cleaned up after everyone again",
            kind=MessageKind.PHOTO,
            photos=(photo,),
        )
    ]

    planned = plan_observations(
        [
            entry(quote="cleaned up after everyone again"),
            entry(quote="a messy kitchen after a party"),
        ],
        context(messages),
    )

    assert [observation.quote for observation in planned.kept] == [
        "cleaned up after everyone again"
    ]
    assert planned.dropped == 1


def test_two_pattern_types_make_an_unclear_observation() -> None:
    [observation] = plan_observations(
        [entry(pattern_types=["CONF.AVOID.BELONG", "ACH.WORTH.PERF"])], context()
    ).kept

    assert observation.unclear
    assert observation.second_pattern_type_id == "ACH.WORTH.PERF"
    assert observation.second_pattern_type_version == "0.3.0"


def test_tags_that_do_not_apply_may_be_left_empty() -> None:
    [observation] = plan_observations(
        [
            entry(
                relationship=None,
                power=None,
                setting=None,
                stance=None,
                about="themselves",
                evidence="own_opinion",
            )
        ],
        context(),
    ).kept

    assert observation.tags == SituationTags(None, None, None, None)


def test_a_thread_it_was_not_shown_leaves_the_observation_without_one() -> None:
    planned = plan_observations(
        [
            entry(thread=7),
            entry(thread=None, quote="and then I stewed on it all night"),
        ],
        context(),
    )

    assert [observation.thread_id for observation in planned.kept] == [None, None]
    assert planned.dropped == 0


def test_the_same_observation_written_twice_is_kept_once() -> None:
    planned = plan_observations([entry(), entry()], context())

    assert (len(planned.kept), planned.dropped) == (1, 1)


def test_entries_that_are_not_observations_are_dropped() -> None:
    planned = plan_observations(["a quote", 3, entry()], context())

    assert (len(planned.kept), planned.dropped) == (1, 2)


def test_an_observation_with_tags_anyone_would_act_on_is_situational() -> None:
    planned = plan_observations(
        [
            entry(relationship="stranger", quote="I said yes to Mei again"),
            entry(power="above", quote="and then I stewed on it all night"),
        ],
        context(),
    )

    assert [observation.situational for observation in planned.kept] == [True, True]


@pytest.mark.parametrize(
    ("matches", "tags", "situational"),
    [
        ((), SituationTags(Relationship.STRANGER, None, None, None), False),
        (
            (SituationMatch(relationships=(Relationship.STRANGER,)),),
            SituationTags(Relationship.STRANGER, Power.EQUAL, None, None),
            True,
        ),
        (
            (SituationMatch(relationships=(Relationship.STRANGER,)),),
            SituationTags(None, None, None, None),
            False,
        ),
        (
            (SituationMatch(powers=(Power.ABOVE,), settings=(SituationSetting.WORK,)),),
            SituationTags(None, Power.ABOVE, SituationSetting.HOME, None),
            False,
        ),
        (
            (SituationMatch(powers=(Power.ABOVE,), settings=(SituationSetting.WORK,)),),
            SituationTags(None, Power.ABOVE, SituationSetting.WORK, Stance.HOSTILE),
            True,
        ),
    ],
)
def test_situational_means_the_tags_fit_one_anyone_would_situation(
    matches: tuple[SituationMatch, ...], tags: SituationTags, situational: bool
) -> None:
    assert is_situational(tags, matches) == situational


@pytest.mark.parametrize(
    ("answer", "read"),
    [
        ('{"observations": []}', []),
        ('```json\n{"observations": [{"quote": "x"}]}\n```', [{"quote": "x"}]),
        ("no json here", None),
        ('{"observations": "none"}', None),
        ("[1, 2]", None),
    ],
)
def test_the_tagging_answer_is_read_from_its_json(
    answer: str, read: list[Any] | None
) -> None:
    assert read_tagging_answer(answer) == read


@pytest.mark.parametrize("quote", ["aid yes", "said yes to M", "ain"])
def test_a_quote_that_cuts_into_a_word_is_not_word_for_word(quote: str) -> None:
    assert plan_observations([entry(quote=quote)], context()).dropped == 1


def test_a_quote_may_start_or_end_at_punctuation() -> None:
    [observation] = plan_observations(
        [entry(quote="It’s fine, honestly")], context()
    ).kept

    assert observation.quote == "It’s fine, honestly"


def unclear_mei() -> Any:
    """Mei's story, kept unclear between belonging and self-worth."""
    [kept] = plan_observations(
        [entry(pattern_types=["CONF.AVOID.BELONG", "ACH.WORTH.PERF"])], context()
    ).kept
    return kept


@pytest.mark.parametrize(
    ("settled", "pattern_type", "sign"),
    [
        (
            {"pattern_type": "CONF.AVOID.BELONG", "sign": "I1"},
            "CONF.AVOID.BELONG",
            "I1",
        ),
        ({"pattern_type": "ACH.WORTH.PERF", "sign": "I1"}, "ACH.WORTH.PERF", "I1"),
    ],
)
def test_a_settled_unclear_story_becomes_clear_under_the_pattern_type_named(
    settled: dict[str, Any], pattern_type: str, sign: str
) -> None:
    story = unclear_mei()

    [clear] = plan_settled([{"unclear": 1, **settled}], {1: story}, PATTERN_TYPES)

    assert (clear.id, clear.pattern_type_id, clear.sign_id) == (
        story.id,
        pattern_type,
        sign,
    )
    assert clear.pattern_type_version == PATTERN_TYPES[pattern_type].version
    assert not clear.unclear
    assert clear.quote == story.quote


@pytest.mark.parametrize(
    "settled",
    [
        {"unclear": 2, "pattern_type": "CONF.AVOID.BELONG", "sign": "I2"},
        {"unclear": 1, "pattern_type": "CTRL.UNCERT.PLAN", "sign": "I1"},
        {"unclear": 1, "pattern_type": "CONF.AVOID.BELONG", "sign": "C1"},
        {"unclear": 1, "pattern_type": "CONF.AVOID.BELONG", "sign": "Z9"},
        {"unclear": True, "pattern_type": "CONF.AVOID.BELONG", "sign": "I2"},
        "settle it",
    ],
)
def test_code_keeps_a_settling_only_for_one_of_its_two_pattern_types_and_a_sign(
    settled: Any,
) -> None:
    assert plan_settled([settled], {1: unclear_mei()}, PATTERN_TYPES) == []


def test_a_story_is_settled_once_and_an_answer_with_no_settled_list_settles_none() -> (
    None
):
    story = unclear_mei()
    twice = [
        {"unclear": 1, "pattern_type": "CONF.AVOID.BELONG", "sign": "I2"},
        {"unclear": 1, "pattern_type": "ACH.WORTH.PERF", "sign": "I1"},
    ]

    [clear] = plan_settled(twice, {1: story}, PATTERN_TYPES)

    assert clear.pattern_type_id == "CONF.AVOID.BELONG"
    assert read_settled_answer('{"observations": []}') == []
    assert read_settled_answer('{"observations": [], "settled": "no"}') == []


@pytest.mark.parametrize(
    ("answered", "kind"),
    [
        (1, EvidenceKind.WHAT_IF_ANSWER),
        (2, EvidenceKind.REAL_STORY),
        (True, EvidenceKind.REAL_STORY),
        ("1", EvidenceKind.REAL_STORY),
        (None, EvidenceKind.REAL_STORY),
    ],
)
def test_an_answer_to_a_thought_experiment_shown_is_a_what_if_answer(
    answered: Any, kind: EvidenceKind
) -> None:
    shown = replace(context(), thought_experiment_numbers=frozenset({1}))

    [observation] = plan_observations([entry(thought_experiment=answered)], shown).kept

    assert observation.evidence_kind == kind


def test_a_ruled_out_topic_is_kept_only_when_it_is_on_the_admin_set_list() -> None:
    listed = replace(context(), ruled_out_topics=frozenset({"abuse"}))

    planned = plan_observations(
        [
            entry(ruled_out_topic="Abuse", raised_by_user=True),
            entry(sign="I5", quote="It’s fine", ruled_out_topic="money"),
            entry(sign="I1", quote="honestly", raised_by_user=True),
        ],
        listed,
    )

    assert [(kept.ruled_out_topic, kept.raised_by_user) for kept in planned.kept] == [
        ("abuse", True),
        (None, False),
        (None, False),
    ]


def test_an_observation_is_excluded_while_an_ignored_exclusion_applies_to_it() -> None:
    grieving = replace(
        context(), ignored_pattern_type_ids=frozenset({"ACH.WORTH.PERF"})
    )

    planned = plan_observations(
        [
            entry(),
            entry(
                sign="I5",
                quote="It’s fine",
                pattern_types=["CONF.AVOID.BELONG", "ACH.WORTH.PERF"],
            ),
        ],
        grieving,
    )

    assert [kept.excluded for kept in planned.kept] == [False, True]


def test_only_exclusions_the_catalog_lists_are_flagged_once_each() -> None:
    answer = (
        '{"observations": [], "exclusions": ['
        '{"pattern_type": "CONF.AVOID.BELONG", "exclusion": "grief"},'
        '{"pattern_type": "CONF.AVOID.BELONG", "exclusion": "Grief"},'
        '{"pattern_type": "CONF.AVOID.BELONG", "exclusion": "A bad week"},'
        '{"pattern_type": "NOT.A.TYPE", "exclusion": "Grief"}, "Grief", '
        '{"pattern_type": "REL.MOOD.FIX"}]}'
    )

    flags = plan_exclusion_flags(
        read_exclusions_answer(answer), PATTERN_TYPES, MEI.user_id, SENT_AT
    )

    assert [
        (flag.pattern_type_id, flag.exclusion, flag.evidence, flag.flagged_at)
        for flag in flags
    ] == [("CONF.AVOID.BELONG", "Grief", ExcludedEvidence.IGNORED, SENT_AT)]
    assert ignored_pattern_types(flags) == frozenset({"CONF.AVOID.BELONG"})
    assert read_exclusions_answer('{"observations": []}') == []
