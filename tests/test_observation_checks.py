from datetime import UTC, date, datetime
from typing import Any
from uuid import uuid4

import pytest

from companion.adapters.pattern_catalog_seed import read_pattern_catalog_seed
from companion.core.models import (
    ChannelPhoto,
    ConversationMessage,
    EvidenceKind,
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
    TaggingContext,
    is_situational,
    plan_observations,
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


def test_a_valid_observation_is_kept_with_everything_it_needs() -> None:
    planned = plan_observations([entry()], context())

    [observation] = planned.kept
    assert planned.dropped == 0
    assert observation.pattern_type_id == "CONF.AVOID.BELONG"
    assert observation.pattern_type_version == "0.2.0"
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
    assert observation.second_pattern_type_version == "0.1.0"


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
