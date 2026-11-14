import time
from concurrent.futures import Future, ThreadPoolExecutor
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.repositories import build_postgres_repositories
from companion.core.admin_users import (
    AdminUserService,
    LastAdminError,
    refuse_if_last_admin,
)
from companion.core.models import User, UserRole
from tests.conftest import INITIAL_ADMIN_EMAIL
from tests.fakes import FakeAuthVerifier, FakeChatChannel, ScriptedChatModel
from tests.telegram_helpers import (
    OWNER_AUTH_ID,
    auth_headers,
    connect_telegram,
    owner_headers,
    send_to_webhook,
    telegram_text_update,
)


def test_signing_in_with_an_initial_admin_email_gives_the_admin_role(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner = client.get("/api/me", headers=auth_headers(auth_verifier, OWNER_AUTH_ID))
    maya = client.get("/api/me", headers=auth_headers(auth_verifier, "user_maya"))

    assert owner.json()["role"] == "admin"
    assert maya.json()["role"] == "user"


def test_initial_admin_email_matches_whatever_the_case(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    token = auth_verifier.token_for("owner_2", INITIAL_ADMIN_EMAIL.upper())

    me = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})

    assert me.json()["role"] == "admin"


def test_existing_user_with_an_initial_admin_email_becomes_admin_while_there_is_none(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    signed_up_before = auth_verifier.token_for("owner", "owner@old.example.com")
    client.get("/api/me", headers={"Authorization": f"Bearer {signed_up_before}"})
    now_listed = auth_verifier.token_for("owner", INITIAL_ADMIN_EMAIL)

    me = client.get("/api/me", headers={"Authorization": f"Bearer {now_listed}"})

    assert me.json()["role"] == "admin"


def test_admin_sees_every_user_with_counts_but_no_message_text(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    chat_channel: FakeChatChannel,
    chat_model: ScriptedChatModel,
) -> None:
    headers = owner_headers(client, auth_verifier)
    connect_telegram(client, auth_verifier, chat_channel)
    chat_model.script("hey you", "glad to hear it")
    send_to_webhook(client, telegram_text_update("hi zeph, a secret thing"))
    send_to_webhook(client, telegram_text_update("feeling better today"))
    client.get("/api/me", headers=auth_headers(auth_verifier, "user_ren"))

    response = client.get("/api/admin/users", headers=headers)

    assert response.status_code == 200
    rows = {row["email"]: row for row in response.json()["users"]}
    assert rows["user_maya@example.com"] == {
        "id": rows["user_maya@example.com"]["id"],
        "name": None,
        "email": "user_maya@example.com",
        "role": "user",
        "signed_up_at": "2026-11-11T09:00:00Z",
        "telegram_connected": True,
        "conversation_count": 1,
        "messages_sent": 2,
    }
    assert rows["user_ren@example.com"]["telegram_connected"] is False
    assert rows["user_ren@example.com"]["messages_sent"] == 0
    assert rows[INITIAL_ADMIN_EMAIL]["role"] == "admin"
    assert "secret" not in response.text
    assert "better" not in response.text


def test_admin_api_refuses_users_who_are_not_admins(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "user_maya")

    assert client.get("/api/admin/users", headers=maya).status_code == 403
    assert client.get("/api/admin/users").status_code == 401


def user_id_for(client: TestClient, headers: dict[str, str]) -> str:
    """Sign in with the given headers and return that User's ID."""
    user_id: str = client.get("/api/me", headers=headers).json()["id"]
    return user_id


def test_admin_can_promote_and_demote_a_user(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner = owner_headers(client, auth_verifier)
    maya = auth_headers(auth_verifier, "user_maya")
    maya_id = user_id_for(client, maya)

    promoted = client.put(
        f"/api/admin/users/{maya_id}/role", json={"role": "admin"}, headers=owner
    )

    assert promoted.status_code == 200
    assert promoted.json()["role"] == "admin"
    assert client.get("/api/admin/users", headers=maya).status_code == 200

    demoted = client.put(
        f"/api/admin/users/{maya_id}/role", json={"role": "user"}, headers=owner
    )

    assert demoted.json()["role"] == "user"
    assert client.get("/api/admin/users", headers=maya).status_code == 403


def test_demoting_the_last_admin_is_refused(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner = owner_headers(client, auth_verifier)
    owner_id = user_id_for(client, owner)

    response = client.put(
        f"/api/admin/users/{owner_id}/role", json={"role": "user"}, headers=owner
    )

    assert response.status_code == 409
    assert "last Admin" in response.json()["detail"]
    assert client.get("/api/me", headers=owner).json()["role"] == "admin"


def test_an_admin_can_step_down_while_another_admin_remains(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner = owner_headers(client, auth_verifier)
    owner_id = user_id_for(client, owner)
    maya_id = user_id_for(client, auth_headers(auth_verifier, "user_maya"))
    client.put(
        f"/api/admin/users/{maya_id}/role", json={"role": "admin"}, headers=owner
    )

    response = client.put(
        f"/api/admin/users/{owner_id}/role", json={"role": "user"}, headers=owner
    )

    assert response.json()["role"] == "user"
    assert client.get("/api/admin/users", headers=owner).status_code == 403


def test_changing_the_role_of_an_unknown_user_is_not_found(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner = owner_headers(client, auth_verifier)

    response = client.put(
        "/api/admin/users/00000000-0000-0000-0000-000000000000/role",
        json={"role": "admin"},
        headers=owner,
    )

    assert response.status_code == 404


def test_two_admins_demoting_each_other_at_once_leave_one_admin(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    owner = owner_headers(client, auth_verifier)
    owner_id = user_id_for(client, owner)
    maya = auth_headers(auth_verifier, "user_maya")
    maya_id = user_id_for(client, maya)
    client.put(
        f"/api/admin/users/{maya_id}/role", json={"role": "admin"}, headers=owner
    )

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(
                lambda request: (
                    client.put(
                        f"/api/admin/users/{request[0]}/role",
                        json={"role": "user"},
                        headers=request[1],
                    ).status_code
                ),
                [(maya_id, owner), (owner_id, maya)],
            )
        )

    assert sorted(results) in ([200, 403], [200, 409])
    roles = [
        row["role"]
        for row in client.get(
            "/api/admin/users", headers=maya if results[1] == 200 else owner
        ).json()["users"]
    ]
    assert roles.count("admin") == 1


def wait_until_a_query_waits_on_a_lock(engine: Engine) -> None:
    """Wait until another database session is blocked locking the Admin rows."""
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            waiting = connection.execute(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE wait_event_type = 'Lock' "
                    "AND datname = current_database() "
                    "AND query ILIKE '%FOR UPDATE%'"
                )
            ).scalar_one()
        if waiting:
            return
        time.sleep(0.01)
    raise AssertionError("No query started waiting on the Admin lock")


def two_admins(client: TestClient, auth_verifier: FakeAuthVerifier) -> list[UUID]:
    """Make the owner and Maya Admins, and return their User IDs."""
    owner = owner_headers(client, auth_verifier)
    maya_id = user_id_for(client, auth_headers(auth_verifier, "user_maya"))
    client.put(
        f"/api/admin/users/{maya_id}/role", json={"role": "admin"}, headers=owner
    )
    return [UUID(user_id_for(client, owner)), UUID(maya_id)]


def test_two_admins_demoting_each_other_at_the_same_moment_leave_one_admin(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    owner_id, maya_id = two_admins(client, auth_verifier)
    repositories = build_postgres_repositories(engine)
    admin_users = AdminUserService(repositories)

    with ThreadPoolExecutor(max_workers=1) as pool:
        with repositories.transaction() as transaction:
            refuse_if_last_admin(transaction, maya_id)
            demoting_the_owner: Future[User] = pool.submit(
                admin_users.change_role, owner_id, UserRole.USER
            )
            wait_until_a_query_waits_on_a_lock(engine)
            transaction.repositories.users.demote_to_user(maya_id)

        with pytest.raises(LastAdminError):
            demoting_the_owner.result()

    roles = {
        user.id: user.role for user in repositories.users.get_many([owner_id, maya_id])
    }
    assert roles == {owner_id: UserRole.ADMIN, maya_id: UserRole.USER}


def test_a_failed_transaction_changes_nothing(
    client: TestClient, engine: Engine, auth_verifier: FakeAuthVerifier
) -> None:
    _, maya_id = two_admins(client, auth_verifier)
    repositories = build_postgres_repositories(engine)

    with pytest.raises(RuntimeError), repositories.transaction() as transaction:
        transaction.repositories.users.demote_to_user(maya_id)
        raise RuntimeError

    maya = repositories.users.get(maya_id)
    assert maya is not None
    assert maya.role == UserRole.ADMIN
