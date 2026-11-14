from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

import pytest
from sqlalchemy import Engine, text

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.chat_settings import (
    DELETE_DATA_INSTRUCTIONS_SETTING,
    DELETE_DATA_TOOL,
    INSTRUCTIONS_SETTING,
    ChatDataDeletion,
    SettingsTools,
)
from companion.core.check_ins import CheckInService
from companion.core.features import FeatureService
from companion.core.models import (
    ChannelPhoto,
    ChannelSticker,
    Conversation,
    ConversationMessage,
    Feature,
    FeatureReason,
    FeatureStatus,
    LibrarySticker,
    MessageDirection,
    MessageKind,
    PersonalSticker,
    SharedPhoto,
    User,
    UserFeatureSwitch,
    UserRole,
    UserSnapshot,
)
from companion.core.photos import PhotoService, PhotoTools, SendPhotoTools
from companion.core.ports import ChatTool, Repositories
from companion.core.reply_tools import Attachment, ReplyContext, ReplyOffer
from companion.core.response_composition import EmptyReplyError, ResponseComposer
from companion.core.sticker_adding import ADDING_TOOL, StickerAdding
from companion.core.stickers import StickerLibraryService, StickerTools
from companion.core.usage import UsageLimiter, UsageRecordingChatModel
from companion.core.user_memory import UserMemoryService
from companion.core.user_snapshot import UserSnapshotLoader
from companion.core.users import UserService
from companion.core.web_search import WebSearchTools
from tests.fakes import (
    FakeChatChannel,
    FakeClock,
    FakePhotoViewer,
    FakeTimer,
    FakeWebSearch,
    ScriptedChatModel,
    ToolCall,
)

NOW = datetime(2026, 11, 14, 9, tzinfo=UTC)
DASHBOARD_URL = "http://dashboard.test"


@pytest.fixture
def repositories(engine: Engine) -> Repositories:
    """The real repositories on the freshly seeded test database."""
    return build_postgres_repositories(engine)


def add_user(repositories: Repositories, role: UserRole = UserRole.USER) -> User:
    """Add a User to the database."""
    user = User(
        id=uuid4(), auth_id=f"user_{uuid4()}", email=None, created_at=NOW, role=role
    )
    return repositories.users.add(user)


def snapshot_for(user: User, *working: Feature) -> UserSnapshot:
    """Make a snapshot in which only the given Features work for the User."""
    statuses = tuple(
        FeatureStatus(
            feature=feature,
            available=feature in working,
            works=feature in working,
            reason=FeatureReason.ON_FOR_EVERYONE
            if feature in working
            else FeatureReason.OFF_FOR_EVERYONE,
            switch=UserFeatureSwitch.DEFAULT,
            changed_by_email=None,
            changed_at=None,
        )
        for feature in Feature
    )
    return UserSnapshot(user=user, local_now=NOW, today=NOW.date(), features=statuses)


def tool_names(offer: ReplyOffer) -> list[str]:
    """List the names of the tools an offer holds."""
    return [tool.name for tool in offer.tools]


def no_context() -> ReplyContext:
    """A reply context with a new Conversation and no Shared Photos."""
    return ReplyContext(conversation_id=uuid4())


class FakeProvider:
    """A reply tool provider that makes a set offer and records each ask."""

    def __init__(self, offer: ReplyOffer) -> None:
        """Remember the offer to make."""
        self._offer = offer
        self.asked: list[tuple[UserSnapshot, ReplyContext]] = []

    def offer(self, snapshot: UserSnapshot, context: ReplyContext) -> ReplyOffer:
        """Record the ask and make the offer."""
        self.asked.append((snapshot, context))
        return self._offer


def picking_offer(name: str, attachment: Attachment) -> ReplyOffer:
    """Make an offer with one tool that picks the attachment when called."""
    offer = ReplyOffer(tools=[])

    def pick(arguments: dict[str, Any]) -> str:
        offer.picked = attachment
        return "picked"

    offer.tools.append(ChatTool(name=name, description="", parameters={}, run=pick))
    return offer


def plain_tool(name: str) -> ChatTool:
    """Make a tool that does nothing."""
    return ChatTool(name=name, description="", parameters={}, run=lambda _: "")


def build_composer(
    repositories: Repositories,
    chat_model: ScriptedChatModel,
    providers: list[FakeProvider],
) -> ResponseComposer:
    """Build a composer with the scripted chat model and the given providers."""
    clock = FakeClock(NOW)
    usage_limiter = UsageLimiter(repositories, clock)
    return ResponseComposer(
        repositories=repositories,
        chat_model=UsageRecordingChatModel(chat_model, usage_limiter),
        features=FeatureService(repositories, clock, DASHBOARD_URL),
        tool_providers=providers,
    )


def a_sticker() -> LibrarySticker:
    """A Sticker Library sticker."""
    return LibrarySticker(
        id=uuid4(),
        file_id="sticker-file",
        file_unique_id="sticker-unique",
        emoji="🌱",
        set_name=None,
        preview_file_id=None,
        note="For small steps",
        added_at=NOW,
    )


def a_shared_photo(user_id: UUID) -> SharedPhoto:
    """A Shared Photo of the User's."""
    return SharedPhoto(
        id=uuid4(),
        user_id=user_id,
        file_id="photo-file",
        file_unique_id="photo-unique",
        description="A ginger cat",
        note="Their cat",
        caption="",
        sent_at=NOW,
        conversation_id=None,
    )


def test_the_composer_offers_every_providers_tools_and_instructions_in_order(
    repositories: Repositories,
) -> None:
    user = add_user(repositories)
    snapshot = snapshot_for(user)
    first = FakeProvider(ReplyOffer(tools=[plain_tool("one")], instructions="Use one."))
    second = FakeProvider(ReplyOffer(tools=[plain_tool("two"), plain_tool("three")]))
    third = FakeProvider(ReplyOffer(tools=[], instructions="Use none."))
    chat_model = ScriptedChatModel()
    chat_model.script("Hello there")
    composer = build_composer(repositories, chat_model, [first, second, third])
    conversation_id = uuid4()
    shared_photo_ids = [uuid4()]

    reply = composer.compose(
        conversation_id,
        snapshot,
        memory="They like tea.",
        knowledge="Breathing helps.",
        shared_photo_ids=shared_photo_ids,
    )

    assert reply.parts == ["Hello there"]
    [call] = chat_model.calls
    assert [tool.name for tool in call.tools] == ["one", "two", "three"]
    assert (
        "They like tea.\n\nBreathing helps.\n\nUse one.\n\nUse none."
        in call.instructions
    )
    expected_context = ReplyContext(
        conversation_id=conversation_id, shared_photo_ids=tuple(shared_photo_ids)
    )
    for provider in (first, second, third):
        assert provider.asked == [(snapshot, expected_context)]


def test_what_a_providers_tool_picks_is_sent_as_the_sticker_or_shared_photo(
    repositories: Repositories,
) -> None:
    user = add_user(repositories)
    sticker = a_sticker()
    shared_photo = a_shared_photo(user.id)
    chat_model = ScriptedChatModel()
    chat_model.script(
        ToolCall("pick_photo", {}), ToolCall("pick_sticker", {}), "Look at Miso"
    )
    composer = build_composer(
        repositories,
        chat_model,
        [
            FakeProvider(picking_offer("pick_sticker", sticker)),
            FakeProvider(picking_offer("pick_photo", shared_photo)),
        ],
    )

    reply = composer.compose(uuid4(), snapshot_for(user))

    assert reply.parts == ["Look at Miso"]
    assert reply.sticker == sticker
    assert reply.shared_photo == shared_photo


def test_a_reply_with_only_a_pick_is_sent_but_one_with_nothing_is_empty(
    repositories: Repositories,
) -> None:
    user = add_user(repositories)
    sticker = a_sticker()
    chat_model = ScriptedChatModel()
    chat_model.script(ToolCall("pick_sticker", {}), "", "  ")
    composer = build_composer(
        repositories,
        chat_model,
        [FakeProvider(picking_offer("pick_sticker", sticker))],
    )

    reply = composer.compose(uuid4(), snapshot_for(user))
    assert reply.parts == []
    assert reply.sticker == sticker

    nothing_picked = build_composer(
        repositories, chat_model, [FakeProvider(ReplyOffer(tools=[]))]
    )
    with pytest.raises(EmptyReplyError):
        nothing_picked.compose(uuid4(), snapshot_for(user))


def test_web_search_offers_its_tools_until_the_daily_limit(
    repositories: Repositories,
) -> None:
    user = add_user(repositories)
    provider = WebSearchTools(repositories, FakeWebSearch())
    settings = repositories.platform_settings

    assert provider.offer(snapshot_for(user), no_context()) == ReplyOffer(tools=[])

    snapshot = snapshot_for(user, Feature.WEB_SEARCH)
    offer = provider.offer(snapshot, no_context())
    assert tool_names(offer) == ["web_search", "fetch_page"]
    assert offer.instructions == settings.get("reply_web_search_instructions")
    assert offer.picked is None

    daily_limit = settings.get("web_search_daily_limit")
    for _ in range(daily_limit):
        repositories.usage.claim_web_search(user.id, snapshot.today, daily_limit)
    assert provider.offer(snapshot, no_context()) == ReplyOffer(
        tools=[], instructions=settings.get("reply_web_search_limit_note")
    )


def build_settings_tools(repositories: Repositories) -> SettingsTools:
    """Build the settings tools with real services, as the app wires them."""
    clock = FakeClock(NOW)
    chat_channel = FakeChatChannel()
    features = FeatureService(repositories, clock, DASHBOARD_URL)
    user_memory = UserMemoryService(repositories, features, clock)
    usage_limiter = UsageLimiter(repositories, clock)
    check_ins = CheckInService(
        repositories=repositories,
        features=features,
        user_snapshots=UserSnapshotLoader(repositories, clock),
        chat_model=UsageRecordingChatModel(ScriptedChatModel(), usage_limiter),
        usage_limiter=usage_limiter,
        chat_channel=chat_channel,
        clock=clock,
    )
    users = UserService(
        repositories.users, features, user_memory, check_ins, clock, frozenset()
    )
    return SettingsTools(
        repositories,
        users,
        check_ins,
        user_memory,
        ChatDataDeletion(repositories, chat_channel, clock),
    )


def test_settings_in_chat_offers_every_settings_tool_or_only_deleting_data(
    repositories: Repositories,
) -> None:
    user = add_user(repositories)
    provider = build_settings_tools(repositories)
    settings = repositories.platform_settings

    on = provider.offer(snapshot_for(user, Feature.SETTINGS_IN_CHAT), no_context())
    assert DELETE_DATA_TOOL in tool_names(on)
    assert len(on.tools) > 1
    assert on.instructions == settings.get(INSTRUCTIONS_SETTING)

    off = provider.offer(snapshot_for(user), no_context())
    assert tool_names(off) == [DELETE_DATA_TOOL]
    assert off.instructions == settings.get(DELETE_DATA_INSTRUCTIONS_SETTING)


def test_stickers_offer_their_own_first_and_pick_only_one(
    repositories: Repositories,
) -> None:
    user = add_user(repositories)
    repositories.stickers.add_new(
        [
            ChannelSticker("library-file", "library-unique", "🌱", None, None),
            ChannelSticker("no-note-file", "no-note-unique", "🙂", None, None),
        ],
        NOW,
    )
    [noted, _] = repositories.stickers.list_all()
    repositories.stickers.save_note(noted.id, "For small steps")
    theirs = PersonalSticker(
        id=uuid4(),
        user_id=user.id,
        file_id="their-file",
        file_unique_id="their-unique",
        emoji="😂",
        set_name=None,
        preview_file_id=None,
        note="For laughing along",
        kept_at=NOW,
        last_used_at=NOW,
    )
    repositories.personal_stickers.save_many([theirs])
    provider = StickerTools(repositories)

    assert provider.offer(snapshot_for(user), no_context()) == ReplyOffer(tools=[])

    offer = provider.offer(
        snapshot_for(user, Feature.STICKERS, Feature.PERSONAL_STICKERS), no_context()
    )
    [tool] = offer.tools
    assert tool.name == "send_sticker"
    assert tool.description.endswith(
        "1. 😂 (theirs) For laughing along\n2. 🌱 For small steps"
    )
    tool.run({"number": 2})
    tool.run({"number": 1})
    assert isinstance(offer.picked, LibrarySticker)
    assert offer.picked.file_unique_id == "library-unique"


def test_sticker_adding_is_offered_to_admins_only(
    repositories: Repositories,
) -> None:
    chat_channel = FakeChatChannel()
    provider = StickerAdding(
        repositories=repositories,
        sticker_library=StickerLibraryService(
            repositories, chat_channel, FakeClock(NOW)
        ),
        chat_channel=chat_channel,
        deliver_notice=lambda user_id, chat_id, text: None,
        timer=FakeTimer(),
        dashboard_url=DASHBOARD_URL,
    )
    admin = snapshot_for(add_user(repositories, UserRole.ADMIN))
    user = snapshot_for(add_user(repositories))

    assert tool_names(provider.offer(admin, no_context())) == [ADDING_TOOL]
    assert provider.offer(user, no_context()) == ReplyOffer(tools=[])


def test_photo_viewing_offers_a_look_again_at_viewed_photos_only(
    repositories: Repositories,
) -> None:
    user = add_user(repositories)
    clock = FakeClock(NOW)
    provider = PhotoTools(
        repositories,
        PhotoService(
            repositories=repositories,
            chat_channel=FakeChatChannel(),
            photo_viewer=FakePhotoViewer(),
            usage_limiter=UsageLimiter(repositories, clock),
            clock=clock,
        ),
    )
    conversation_id = uuid4()
    repositories.conversations.add(
        Conversation(
            id=conversation_id, user_id=user.id, started_at=NOW, last_message_at=NOW
        )
    )
    repositories.conversations.add_message(
        ConversationMessage(
            id=uuid4(),
            conversation_id=conversation_id,
            direction=MessageDirection.INCOMING,
            kind=MessageKind.PHOTO,
            content="[photo]",
            sent_at=NOW,
            photos=(
                ChannelPhoto(
                    "seen-file", "seen-unique", viewed=True, description="A cat"
                ),
                ChannelPhoto("unseen-file", "unseen-unique"),
            ),
        )
    )
    context = ReplyContext(conversation_id=conversation_id)

    assert provider.offer(snapshot_for(user), context) == ReplyOffer(tools=[])
    assert provider.offer(
        snapshot_for(user, Feature.PHOTO_VIEWING), no_context()
    ) == ReplyOffer(tools=[])

    offer = provider.offer(snapshot_for(user, Feature.PHOTO_VIEWING), context)
    [tool] = offer.tools
    assert tool.name == "ask_about_photo"
    assert tool.description.endswith("\n\n1. A cat")


def add_shared_photo_row(engine: Engine, photo: SharedPhoto) -> None:
    """Save a Shared Photo straight to the database."""
    with engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO shared_photos (id, user_id, file_id, file_unique_id, "
                "description, note, caption, sent_at) VALUES (:id, :user_id, "
                ":file_id, :file_unique_id, :description, :note, '', :sent_at)"
            ),
            {
                "id": photo.id,
                "user_id": photo.user_id,
                "file_id": photo.file_id,
                "file_unique_id": photo.file_unique_id,
                "description": photo.description,
                "note": photo.note,
                "sent_at": photo.sent_at,
            },
        )


def test_send_photo_offers_only_the_users_own_shared_photos_and_picks_one(
    engine: Engine, repositories: Repositories
) -> None:
    user = add_user(repositories)
    someone_else = add_user(repositories)
    theirs = a_shared_photo(user.id)
    not_theirs = a_shared_photo(someone_else.id)
    add_shared_photo_row(engine, theirs)
    add_shared_photo_row(engine, not_theirs)
    provider = SendPhotoTools(repositories)
    snapshot = snapshot_for(user)

    assert provider.offer(snapshot, no_context()) == ReplyOffer(tools=[])

    offer = provider.offer(
        snapshot,
        ReplyContext(
            conversation_id=uuid4(), shared_photo_ids=(not_theirs.id, theirs.id)
        ),
    )
    [tool] = offer.tools
    assert tool.name == "send_photo"
    assert tool.description.endswith("\n\n1. A ginger cat")
    tool.run({"photo": 1})
    assert offer.picked is not None
    assert offer.picked.id == theirs.id
