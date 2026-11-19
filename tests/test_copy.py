import json
from datetime import timedelta
from pathlib import Path
from typing import Any

import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine

from companion.adapters.postgres.database import seed_copy
from tests.conftest import COPY_SEED_FILE
from tests.fakes import FakeAuthVerifier, FakeClock
from tests.telegram_helpers import auth_headers, owner_headers

DESIGN_FIXTURE_COPY_FILE = (
    Path(__file__).parent.parent / "web/src/lib/design-fixtures/seed-copy.json"
)

TEST_SEED: list[dict[str, Any]] = [
    {
        "tab": "landing",
        "name": "Landing",
        "slots": [
            {
                "key": "landing.heading",
                "name": "Main heading",
                "max_length": 30,
                "text": "Think Deeper.",
            },
            {
                "key": "landing.count",
                "name": "Memory count",
                "max_length": 40,
                "placeholders": ["count"],
                "text": "{count} Memory Items",
            },
        ],
    },
    {
        "tab": "pricing",
        "name": "Pricing",
        "slots": [
            {
                "key": "pricing.heading",
                "name": "Main heading",
                "max_length": 30,
                "text": "Simple plans.",
            }
        ],
    },
]


def reseed(engine: Engine, tmp_path: Path, seed: list[dict[str, Any]]) -> None:
    """Load a Copy seed into the test database, as prestart does on start."""
    seed_file = tmp_path / "copy.yaml"
    seed_file.write_text(yaml.safe_dump(seed))
    seed_copy(engine, seed_file)


def seed_texts() -> dict[str, str]:
    """Every slot's text in the real seed file, by key."""
    tabs = yaml.safe_load(COPY_SEED_FILE.read_text())
    return {slot["key"]: slot["text"] for tab in tabs for slot in tab["slots"]}


def landing_slots(client: TestClient, headers: dict[str, str]) -> list[Any]:
    """The Landing tab's slots as an Admin reads them."""
    tabs = client.get("/api/admin/copy", headers=headers).json()["tabs"]
    landing = next(tab for tab in tabs if tab["tab"] == "landing")
    slots: list[Any] = landing["slots"]
    return slots


def test_signed_out_visitors_read_every_slot_from_the_seed(
    client: TestClient,
) -> None:
    response = client.get("/api/copy")

    assert response.status_code == 200
    assert response.json() == {"texts": seed_texts()}


def test_admin_sees_each_tab_with_slots_in_page_order(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    tabs = client.get("/api/admin/copy", headers=headers).json()["tabs"]

    assert [(tab["tab"], tab["name"]) for tab in tabs] == [
        ("landing", "Landing"),
        ("pricing", "Pricing"),
        ("how_it_works", "How it works"),
        ("auth", "Sign in and sign up"),
        ("onboarding", "Onboarding"),
        ("home", "Home"),
        ("memories", "Memories"),
        ("connect_telegram", "Connect Telegram"),
        ("shared", "Shared"),
    ]
    seed = yaml.safe_load(COPY_SEED_FILE.read_text())
    for tab, seed_tab in zip(tabs, seed, strict=True):
        assert [slot["key"] for slot in tab["slots"]] == [
            slot["key"] for slot in seed_tab["slots"]
        ]
    slots = tabs[0]["slots"]
    heading = slots[3]
    del heading["updated_at"]
    assert heading == {
        "key": "landing.hero.heading_first_line",
        "name": "Main heading, first line",
        "text": "Think Deeper,",
        "max_length": 40,
        "placeholders": [],
        "updated_by": None,
    }


def test_onboarding_and_sign_in_slots_carry_their_seed_name_text_and_placeholders(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    tabs = client.get("/api/admin/copy", headers=headers).json()["tabs"]

    slots = {slot["key"]: slot for tab in tabs for slot in tab["slots"]}
    question = slots["onboarding.intentions.heading"]
    assert (question["name"], question["text"]) == (
        "What brings you here: heading",
        "What brings you here?",
    )
    assert slots["onboarding.progress.step_count"]["placeholders"] == [
        "step",
        "count",
    ]
    assert slots["auth.terms_line"]["placeholders"] == ["terms", "privacy"]


def test_home_connect_telegram_and_dashboard_menu_slots_carry_their_seed_text(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    tabs = client.get("/api/admin/copy", headers=headers).json()["tabs"]

    slots_by_tab = {tab["tab"]: tab["slots"] for tab in tabs}
    home = {slot["key"]: slot for slot in slots_by_tab["home"]}
    assert home["home.hero.greeting_evening"]["text"] == "Good evening, {name}."
    assert home["home.hero.greeting_evening"]["placeholders"] == ["name"]
    assert home["home.check_ins.quiet_hours"]["placeholders"] == ["start", "end"]
    connect_telegram_keys = [slot["key"] for slot in slots_by_tab["connect_telegram"]]
    assert connect_telegram_keys.index("connect_telegram.heading") < (
        connect_telegram_keys.index("connect_telegram.card.loading")
    )
    shared = {slot["key"]: slot for slot in slots_by_tab["shared"]}
    assert (
        shared["shared.dashboard.account"]["name"],
        shared["shared.dashboard.account"]["text"],
    ) == ("Dashboard menu: Account link", "Account & privacy")


def test_a_tab_save_applies_every_change_and_shows_on_the_next_read(
    client: TestClient, auth_verifier: FakeAuthVerifier, clock: FakeClock
) -> None:
    headers = owner_headers(client, auth_verifier)
    clock.advance(timedelta(hours=1))

    response = client.put(
        "/api/admin/copy/landing",
        json={
            "texts": {
                "landing.hero.heading_first_line": "Think Slower,",
                "landing.hero.sign_up_button": "Start Free",
            }
        },
        headers=headers,
    )

    assert response.status_code == 200
    saved = {slot["key"]: slot for slot in response.json()["tabs"][0]["slots"]}
    assert saved["landing.hero.heading_first_line"]["text"] == "Think Slower,"
    assert saved["landing.hero.heading_first_line"]["updated_at"] == (
        "2026-11-11T10:00:00Z"
    )
    assert saved["landing.hero.heading_first_line"]["updated_by"] == (
        "owner@example.com"
    )
    assert saved["landing.hero.lead"]["updated_by"] is None
    public = client.get("/api/copy").json()["texts"]
    assert public["landing.hero.heading_first_line"] == "Think Slower,"
    assert public["landing.hero.sign_up_button"] == "Start Free"


def test_the_shared_tab_saves_on_its_own_and_turns_away_a_pricing_slot(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    turned_away = client.put(
        "/api/admin/copy/shared",
        json={
            "texts": {
                "shared.footer.copyright": "© 2027 Zeph",
                "pricing.plus.button": "Try Plus",
            }
        },
        headers=headers,
    )
    saved = client.put(
        "/api/admin/copy/shared",
        json={"texts": {"shared.footer.copyright": "© 2027 Zeph"}},
        headers=headers,
    )

    assert turned_away.status_code == 422
    assert saved.status_code == 200
    public = client.get("/api/copy").json()["texts"]
    assert public["shared.footer.copyright"] == "© 2027 Zeph"
    assert public["pricing.plus.button"] == "Start Plus"


def test_each_bad_text_turns_away_the_whole_save_with_a_reason_on_its_slot(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    tmp_path: Path,
) -> None:
    reseed(engine, tmp_path, TEST_SEED)
    headers = owner_headers(client, auth_verifier)

    response = client.put(
        "/api/admin/copy/landing",
        json={
            "texts": {
                "landing.heading": "x" * 31,
                "landing.count": "Memory Items",
                "pricing.heading": "Plans.",
            }
        },
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["fields"] == {
        "landing.heading": "Keep it to 30 characters or fewer.",
        "landing.count": "Keep {count} in the text.",
        "pricing.heading": "This text isn’t on this tab.",
    }
    assert client.get("/api/copy").json()["texts"] == {
        "landing.heading": "Think Deeper.",
        "landing.count": "{count} Memory Items",
        "pricing.heading": "Simple plans.",
    }


def test_empty_text_and_unknown_placeholders_are_turned_away(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    tmp_path: Path,
) -> None:
    reseed(engine, tmp_path, TEST_SEED)
    headers = owner_headers(client, auth_verifier)

    response = client.put(
        "/api/admin/copy/landing",
        json={"texts": {"landing.heading": "   ", "landing.count": "{nmae} {count}"}},
        headers=headers,
    )

    assert response.status_code == 422
    assert response.json()["fields"] == {
        "landing.heading": "This text can’t be empty.",
        "landing.count": "{nmae} isn’t a placeholder this text takes.",
    }


def test_placeholders_can_move_anywhere_in_the_text(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    tmp_path: Path,
) -> None:
    reseed(engine, tmp_path, TEST_SEED)
    headers = owner_headers(client, auth_verifier)

    response = client.put(
        "/api/admin/copy/landing",
        json={"texts": {"landing.count": "Memory Items: {count}"}},
        headers=headers,
    )

    assert response.status_code == 200
    assert client.get("/api/copy").json()["texts"]["landing.count"] == (
        "Memory Items: {count}"
    )


def test_a_save_to_a_tab_that_does_not_exist_is_not_found(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    response = client.put(
        "/api/admin/copy/nowhere", json={"texts": {}}, headers=headers
    )

    assert response.status_code == 404


def test_reseeding_keeps_an_edited_text_and_follows_the_seed_for_the_rest(
    client: TestClient,
    engine: Engine,
    auth_verifier: FakeAuthVerifier,
    tmp_path: Path,
) -> None:
    reseed(engine, tmp_path, TEST_SEED)
    headers = owner_headers(client, auth_verifier)
    client.put(
        "/api/admin/copy/landing",
        json={"texts": {"landing.count": "{count} things remembered"}},
        headers=headers,
    )
    changed_seed: list[dict[str, Any]] = [
        {
            "tab": "landing",
            "name": "Landing",
            "slots": [
                {
                    "key": "landing.lead",
                    "name": "Lead",
                    "max_length": 90,
                    "text": "A thinking partner.",
                },
                {
                    "key": "landing.count",
                    "name": "Memory Item count",
                    "max_length": 50,
                    "placeholders": ["count", "name"],
                    "text": "{name} has {count} Memory Items",
                },
            ],
        }
    ]

    reseed(engine, tmp_path, changed_seed)

    slots = landing_slots(client, headers)
    assert [
        (slot["key"], slot["name"], slot["text"], slot["max_length"]) for slot in slots
    ] == [
        ("landing.lead", "Lead", "A thinking partner.", 90),
        ("landing.count", "Memory Item count", "{count} things remembered", 50),
    ]
    assert slots[1]["placeholders"] == ["count", "name"]
    assert slots[1]["updated_by"] == "owner@example.com"
    assert client.get("/api/copy").json()["texts"] == {
        "landing.lead": "A thinking partner.",
        "landing.count": "{count} things remembered",
    }


def test_a_plain_user_cannot_read_the_copy_page_or_save(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "maya")

    read = client.get("/api/admin/copy", headers=maya)
    save = client.put(
        "/api/admin/copy/landing",
        json={"texts": {"landing.hero.heading_first_line": "Hi"}},
        headers=maya,
    )

    assert read.status_code == 403
    assert save.status_code == 403
    assert client.get("/api/copy").json()["texts"][
        "landing.hero.heading_first_line"
    ] == ("Think Deeper,")


def test_the_design_fixture_copy_is_the_seed_copy() -> None:
    fixture = json.loads(DESIGN_FIXTURE_COPY_FILE.read_text())

    assert fixture == yaml.safe_load(COPY_SEED_FILE.read_text())
