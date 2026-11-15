import time
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path, PurePosixPath
from typing import Any, Protocol
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.evals.stand_ins import (
    CountingChatModel,
    CountingPhotoViewer,
    EvalAccounts,
    IdleScheduler,
    ManualTimer,
    NoWebSearch,
    RecordingChatChannel,
    RunningClock,
    TokenCounter,
)
from companion.adapters.knowledge_seed import read_knowledge_seed
from companion.adapters.pgvector.vector_store import PgvectorKnowledgeVectorStore
from companion.adapters.postgres.eval_repositories import (
    PostgresEvalCaseRepository,
    PostgresEvalImageRepository,
    PostgresEvalRunRepository,
    PostgresJudgeSettingsRepository,
)
from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.adapters.pypdf.text_extractor import PypdfTextExtractor
from companion.app import AppDependencies, create_app
from companion.core.evals.models import EvalImage, ModelTokens, Replies
from companion.core.evals.ports import EvalSetupError
from companion.core.models import PhotoImage
from companion.core.ports import ChatModel, Embedder, PhotoViewer, Repositories

WEBHOOK_SECRET = "eval-webhook-secret"
BOT_USERNAME = "zeph_eval_bot"
DASHBOARD_URL = "http://dashboard.eval"
ADMIN_AUTH_ID = "eval-admin"
ADMIN_EMAIL = "eval-admin@example.com"
USER_AUTH_ID = "user_maya"
USER_EMAIL = "user_maya@example.com"
TELEGRAM_USER_ID = 5551001
TELEGRAM_USERNAME = "maya_l"
READY_TIMEOUT_SECONDS = 120
ONBOARDING_WITH_CHECK_INS = {
    "name": "Maya",
    "ai_notice_acknowledged": True,
    "onboarding_reasons": ["Being more present", "Relationships"],
    "onboarding_note": "New job, running on autopilot.",
    "user_memory_enabled": True,
    "country": "SG",
    "time_zone": "Asia/Singapore",
    "check_ins_enabled": True,
    "check_in_frequency": "most_days",
}


def telegram_message_update(content: dict[str, Any]) -> dict[str, Any]:
    """Build a Telegram webhook update for a private message from the User.

    Args:
        content: The message's content, e.g. `{"text": "hey"}`.

    Returns:
        The update.
    """
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "date": 1762851600,
            "from": {
                "id": TELEGRAM_USER_ID,
                "is_bot": False,
                "username": TELEGRAM_USERNAME,
            },
            "chat": {"id": TELEGRAM_USER_ID, "type": "private"},
            **content,
        },
    }


def telegram_photo_content(file_unique_id: str, caption: str) -> dict[str, Any]:
    """Build a photo message's content, in a small and a large size.

    Args:
        file_unique_id: The photo's unique file ID.
        caption: Its caption; "" for none.

    Returns:
        The content.
    """
    content: dict[str, Any] = {
        "photo": [
            {
                "file_id": f"small-{file_unique_id}",
                "file_unique_id": f"small-{file_unique_id}",
                "width": 90,
                "height": 60,
            },
            {
                "file_id": f"file-{file_unique_id}",
                "file_unique_id": file_unique_id,
                "width": 1280,
                "height": 853,
            },
        ]
    }
    if caption:
        content["caption"] = caption
    return content


class AppResponse(Protocol):
    """A response from the app, as its in-process client gives it."""

    @property
    def status_code(self) -> int:
        """The HTTP status code."""
        ...

    @property
    def text(self) -> str:
        """The body as text."""
        ...

    @property
    def content(self) -> bytes:
        """The body."""
        ...

    def json(self) -> Any:
        """Read the body as JSON."""
        ...


def require_status(response: AppResponse, expected: int, step: str) -> Any:
    """Check the app agreed to a setup step and read its answer.

    Args:
        response: The app's response.
        expected: The status code it should answer with.
        step: What was asked, for the error message.

    Returns:
        The response's JSON body; None if it has none.

    Raises:
        EvalSetupError: If the app answered with another status code.
    """
    if response.status_code != expected:
        raise EvalSetupError(
            f"{step} failed: {response.status_code} {response.text[:500]}"
        )
    return response.json() if response.content else None


class InProcessCompanion:
    """The whole app built on the Eval database, driven through its own API.

    Messages go through the real Telegram webhook, with the recording chat
    channel, no web search, no scheduler and a clock that runs with real
    time. The Model Call Log keeps full content, as in every Eval run.
    """

    def __init__(
        self,
        engine: Engine,
        chat_model: ChatModel,
        photo_viewer: PhotoViewer,
        embedder: Embedder,
        images: Sequence[EvalImage],
        knowledge_seed_file: Path,
    ) -> None:
        """Build and start the app on the Eval database.

        Args:
            engine: The Eval database.
            chat_model: The real chat model.
            photo_viewer: The real photo viewer.
            embedder: The real embedder.
            images: The test images the case sends.
            knowledge_seed_file: The starter Knowledge library's seed file.
        """
        self._engine = engine
        self._embedder = embedder
        self._images = {image.name: image for image in images}
        self._knowledge_seed_file = knowledge_seed_file
        self._counter = TokenCounter()
        self._chat_model = CountingChatModel(chat_model, self._counter)
        self._judge_chat_model = CountingChatModel(chat_model, self._counter)
        self._chat_channel = RecordingChatChannel()
        self._accounts = EvalAccounts()
        self._timer = ManualTimer()
        self._clock = RunningClock(datetime.now(UTC))
        self._repositories = build_postgres_repositories(engine)
        self._user_id: UUID | None = None
        dependencies = AppDependencies(
            repositories=self._repositories,
            eval_runs=PostgresEvalRunRepository(engine),
            eval_cases=PostgresEvalCaseRepository(engine),
            eval_images=PostgresEvalImageRepository(engine),
            judge_settings=PostgresJudgeSettingsRepository(engine),
            chat_channel=self._chat_channel,
            chat_model=self._chat_model,
            photo_viewer=CountingPhotoViewer(photo_viewer, self._counter),
            auth_verifier=self._accounts,
            auth_accounts=self._accounts,
            text_extractor=PypdfTextExtractor(),
            embedder=embedder,
            knowledge_vector_store=PgvectorKnowledgeVectorStore(engine),
            web_search=NoWebSearch(),
            clock=self._clock,
            scheduler=IdleScheduler(),
            timer=self._timer,
            telegram_webhook_secret=WEBHOOK_SECRET,
            telegram_bot_username=BOT_USERNAME,
            dashboard_url=DASHBOARD_URL,
            initial_admin_emails=frozenset({ADMIN_EMAIL}),
            model_call_content_for_everyone=True,
        )
        self._client = TestClient(create_app(dependencies))
        self._client.__enter__()

    @property
    def repositories(self) -> Repositories:
        """The Eval database's repositories, to set up and read data."""
        return self._repositories

    @property
    def embedder(self) -> Embedder:
        """Embeds made-up memory the way the Companion does."""
        return self._embedder

    @property
    def judge_chat_model(self) -> ChatModel:
        """The chat model the Judge asks, counted with the app's tokens."""
        return self._judge_chat_model

    def tokens_used(self) -> tuple[int, int]:
        """Add up the tokens the LLM read and wrote since the case started.

        Returns:
            Tokens in and tokens out, the app's and the Judge's.
        """
        return self._counter.tokens_in, self._counter.tokens_out

    def tokens_by_model(self) -> dict[str, ModelTokens]:
        """Add up the same tokens by the model that used them.

        Returns:
            Each model's tokens, the app's and the Judge's.
        """
        return dict(self._counter.by_model)

    def called_tools(self) -> list[str]:
        """List the tools the reply model called since the case started.

        Returns:
            Their names, in order.
        """
        return list(self._chat_model.called_tools)

    def clear_called_tools(self) -> None:
        """Forget the tools called so far."""
        self._chat_model.called_tools.clear()

    def now(self) -> datetime:
        """Tell the app's time.

        Returns:
            The current time, as the app sees it.
        """
        return self._clock.now()

    def move_clock(self, by: timedelta) -> None:
        """Move the app's clock on, or back for a negative amount.

        Args:
            by: How far to move it.
        """
        self._clock.move(by)

    def connect_user(
        self, check_ins: bool = False, onboarding_reasons: bool = True
    ) -> UUID:
        """Sign up the made-up User, onboard them and connect their Telegram.

        Only the onboarding times are set, so the User has no name, answers
        or Memory Items, unless they answer onboarding with Check-ins on.

        Args:
            check_ins: Whether they answer onboarding with Check-ins on
                "most days" in Singapore.
            onboarding_reasons: Whether that onboarding says what brings
                them here, which saves Memory Items.

        Returns:
            The User's ID.
        """
        headers = self._user_headers()
        me = require_status(
            self._client.get("/api/me", headers=headers), 200, "Signing up"
        )
        user_id = UUID(me["id"])
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "UPDATE users SET onboarding_completed_at = now(), "
                    "ai_notice_acknowledged_at = now() WHERE id = :user_id"
                ),
                {"user_id": user_id},
            )
        token = require_status(
            self._client.post("/api/telegram-connection/tokens", headers=headers),
            201,
            "Asking for a connection token",
        )["token"]
        self.send_text(f"/start {token}")
        if check_ins:
            require_status(
                self._client.put(
                    "/api/onboarding",
                    json=(
                        ONBOARDING_WITH_CHECK_INS
                        if onboarding_reasons
                        else {
                            **ONBOARDING_WITH_CHECK_INS,
                            "onboarding_reasons": [],
                            "onboarding_note": None,
                        }
                    ),
                    headers=headers,
                ),
                200,
                "Onboarding with Check-ins",
            )
        self._user_id = user_id
        return user_id

    def send_text(self, text: str) -> Replies:
        """Send a text from the User and wait for the reply.

        Args:
            text: What they send.

        Returns:
            What the Companion sent back.
        """
        return self._send(telegram_message_update({"text": text}))

    def send_photo(self, image_name: str, caption: str) -> Replies:
        """Send one of the case's test images from the User as a photo.

        Args:
            image_name: The test image's name.
            caption: The photo's caption; "" for none.

        Returns:
            What the Companion sent back.

        Raises:
            EvalSetupError: If the case has no image by that name.
        """
        image = self._images.get(image_name)
        if image is None:
            raise EvalSetupError(f"The image {image_name} isn't stored")
        stem = PurePosixPath(image_name).stem
        self._chat_channel.photos[f"file-{stem}"] = PhotoImage(
            content=image.content, media_type=image.media_type
        )
        content = telegram_photo_content(stem, caption)
        return self._send(telegram_message_update(content))

    def memory_item_contents(self) -> list[str]:
        """List the contents of the User's Memory Items, as the Dashboard does.

        Returns:
            The contents, whatever their category.
        """
        groups = require_status(
            self._client.get("/api/memory-items", headers=self._user_headers()),
            200,
            "Listing Memory Items",
        )["groups"]
        return [str(item["content"]) for group in groups for item in group["items"]]

    def turn_photo_viewing_off(self) -> None:
        """Turn Photo Viewing off for the User."""
        require_status(
            self._client.patch(
                "/api/me",
                json={"photo_viewing_enabled": False},
                headers=self._user_headers(),
            ),
            200,
            "Turning Photo Viewing off",
        )

    def add_shared_photo(self, file_id: str, description: str, note: str) -> None:
        """Keep a Shared Photo for the User, as memory processing would.

        Args:
            file_id: The photo's file ID.
            description: What it shows.
            note: Why it matters to them.

        Raises:
            EvalSetupError: If the User isn't connected yet.
        """
        if self._user_id is None:
            raise EvalSetupError("Connect the User before adding Shared Photos")
        with self._engine.begin() as connection:
            connection.execute(
                text(
                    "INSERT INTO shared_photos (id, user_id, file_id, file_unique_id, "
                    "description, note, caption, sent_at) VALUES (:id, :user_id, "
                    ":file_id, :file_id, :description, :note, '', :sent_at)"
                ),
                {
                    "id": uuid4(),
                    "user_id": self._user_id,
                    "file_id": file_id,
                    "description": description,
                    "note": note,
                    "sent_at": self._clock.now() - timedelta(days=5),
                },
            )

    def safeguard_risk_types(self) -> list[str]:
        """List the risk types of the Safeguard Events, newest first.

        Returns:
            One risk type per event.
        """
        events = require_status(
            self._client.get(
                "/api/admin/safeguard-events", headers=self._admin_headers()
            ),
            200,
            "Listing Safeguard Events",
        )["events"]
        return [str(event["risk_type"]) for event in events]

    def upload_starter_library(self) -> None:
        """Upload the starter Knowledge library as an Admin."""
        for upload in read_knowledge_seed(self._knowledge_seed_file):
            self.upload_knowledge(
                upload.file_name,
                upload.content,
                title=upload.title,
                source=upload.source,
                tradition=upload.tradition,
            )

    def upload_knowledge(
        self, file_name: str, content: bytes, title: str, source: str, tradition: str
    ) -> str:
        """Upload a Knowledge Document as an Admin.

        Args:
            file_name: The file's name.
            content: The file.
            title: Its title.
            source: Where it comes from.
            tradition: Its tradition.

        Returns:
            The document's ID.
        """
        document = require_status(
            self._client.post(
                "/api/admin/knowledge-documents",
                files={"file": (file_name, content)},
                data={"title": title, "source": source, "tradition": tradition},
                headers=self._admin_headers(),
            ),
            201,
            f"Uploading {file_name}",
        )
        return str(document["id"])

    def wait_until_knowledge_ready(self, document_id: str) -> None:
        """Wait until a Knowledge Document is Ready.

        Args:
            document_id: The document.

        Raises:
            EvalSetupError: If it failed or wasn't Ready in time.
        """
        deadline = time.monotonic() + READY_TIMEOUT_SECONDS
        while time.monotonic() < deadline:
            document = require_status(
                self._client.get(
                    f"/api/admin/knowledge-documents/{document_id}",
                    headers=self._admin_headers(),
                ),
                200,
                "Reading a Knowledge Document",
            )
            if document["status"] == "ready":
                return
            if document["status"] == "failed":
                raise EvalSetupError(
                    f"Knowledge Document failed: {document['failure_reason']}"
                )
            time.sleep(1)
        raise EvalSetupError(f"Knowledge Document {document_id} was not Ready in time")

    def edit_knowledge_text(self, document_id: str, text: str) -> None:
        """Edit a Knowledge Document's text as an Admin.

        Args:
            document_id: The document.
            text: The new text.
        """
        require_status(
            self._client.put(
                f"/api/admin/knowledge-documents/{document_id}/text",
                json={"text": text},
                headers=self._admin_headers(),
            ),
            200,
            "Editing a Knowledge Document's text",
        )

    def edit_knowledge_details(self, document_id: str, details: dict[str, str]) -> None:
        """Edit a Knowledge Document's details as an Admin.

        Args:
            document_id: The document.
            details: The details to change, e.g. `title` or `when_it_helps`.
        """
        require_status(
            self._client.patch(
                f"/api/admin/knowledge-documents/{document_id}",
                json=details,
                headers=self._admin_headers(),
            ),
            200,
            "Editing a Knowledge Document's details",
        )

    def replace_knowledge_file(
        self, document_id: str, file_name: str, content: bytes
    ) -> None:
        """Replace a Knowledge Document's file as an Admin.

        Args:
            document_id: The document.
            file_name: The new file's name.
            content: The new file.
        """
        require_status(
            self._client.put(
                f"/api/admin/knowledge-documents/{document_id}/file",
                files={"file": (file_name, content)},
                headers=self._admin_headers(),
            ),
            200,
            "Replacing a Knowledge Document's file",
        )

    def close(self) -> None:
        """Stop the app."""
        self._client.__exit__(None, None, None)

    def _send(self, update: dict[str, Any]) -> Replies:
        """Post an update to the webhook, then end the wait as if the User paused.

        Args:
            update: The Telegram update.

        Returns:
            What the Companion sent back.
        """
        texts_before = len(self._chat_channel.sent_texts)
        photos_before = len(self._chat_channel.sent_photo_file_ids)
        require_status(
            self._client.post(
                "/telegram/webhook",
                json=update,
                headers={"X-Telegram-Bot-Api-Secret-Token": WEBHOOK_SECRET},
            ),
            200,
            "Sending a message",
        )
        self._timer.end_message_waits()
        return Replies(
            texts=self._chat_channel.sent_texts[texts_before:],
            photo_file_ids=self._chat_channel.sent_photo_file_ids[photos_before:],
        )

    def _user_headers(self) -> dict[str, str]:
        """Build the made-up User's Dashboard API headers.

        Returns:
            The headers.
        """
        token = self._accounts.token_for(USER_AUTH_ID, USER_EMAIL)
        return {"Authorization": f"Bearer {token}"}

    def _admin_headers(self) -> dict[str, str]:
        """Sign in as the Eval's Admin and build their Dashboard API headers.

        Returns:
            The headers.

        Raises:
            EvalSetupError: If the account isn't an Admin.
        """
        token = self._accounts.token_for(ADMIN_AUTH_ID, ADMIN_EMAIL)
        headers = {"Authorization": f"Bearer {token}"}
        me = require_status(
            self._client.get("/api/me", headers=headers), 200, "Signing in the Admin"
        )
        if me["role"] != "admin":
            raise EvalSetupError("The Eval's Admin isn't an Admin")
        return headers
