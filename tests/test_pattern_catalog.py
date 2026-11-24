import copy
import json
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from companion.adapters.postgres.database import load_pattern_catalog
from companion.core.pattern_catalog import InvalidPatternCatalogError
from companion.prestart import load_pattern_catalog_or_keep_last
from tests.fakes import FakeAuthVerifier
from tests.telegram_helpers import auth_headers, owner_headers
from tests.test_pattern_catalog_reader import VALID

DESIGN_FIXTURE_CATALOG_FILE = (
    Path(__file__).parent.parent
    / "web/src/lib/design-fixtures/seed-pattern-catalog.json"
)
TEST_ONE_ROWS = "SELECT * FROM pattern_types WHERE pattern_type_id = 'TEST.ONE'"


def load_catalog(engine: Engine, folder: Path, *contents: dict[str, Any]) -> None:
    """Load a catalog of the given Pattern Types, as prestart does on start."""
    folder.mkdir(exist_ok=True)
    for old_file in folder.glob("*.yaml"):
        old_file.unlink()
    for content in contents:
        (folder / f"{content['id']}.yaml").write_text(yaml.safe_dump(content))
    load_pattern_catalog(engine, folder)


def catalog(client: TestClient, headers: dict[str, str]) -> list[dict[str, Any]]:
    """The Pattern Types as an Admin reads them."""
    response = client.get("/api/admin/pattern-catalog", headers=headers)
    assert response.status_code == 200
    pattern_types: list[dict[str, Any]] = response.json()["pattern_types"]
    return pattern_types


def stored_versions(engine: Engine) -> list[tuple[str, str, bool]]:
    """Every stored row: Pattern Type ID, version and whether it is current."""
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                "SELECT pattern_type_id, version, is_current FROM pattern_types "
                "ORDER BY pattern_type_id, version"
            )
        ).all()
    return [(row.pattern_type_id, row.version, row.is_current) for row in rows]


def test_the_fifteen_pattern_types_are_loaded_on_start(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    pattern_types = catalog(client, headers)

    assert [
        (pattern_type["id"], pattern_type["area"], pattern_type["status"])
        for pattern_type in pattern_types
    ] == [
        ("CONF.AVOID.BELONG", "conflict", "draft"),
        ("CONF.DEFEND.SELF", "conflict", "draft"),
        ("CONF.WITHDRAW.HURT", "conflict", "draft"),
        ("APPR.CONFIRM.CHOICE", "approval", "draft"),
        ("APPR.GIVE.NEEDED", "approval", "draft"),
        ("APPR.HIDE.BURDEN", "approval", "draft"),
        ("CTRL.OPEN.FREEDOM", "control", "draft"),
        ("CTRL.SELF.RELY", "control", "draft"),
        ("CTRL.UNCERT.PLAN", "control", "draft"),
        ("ACH.ABSORB.PULL", "achievement", "draft"),
        ("ACH.GOAL.MOVE", "achievement", "draft"),
        ("ACH.WORTH.PERF", "achievement", "draft"),
        ("REL.CHECK.SECURE", "relationships", "draft"),
        ("REL.DISTANCE.INDEP", "relationships", "draft"),
        ("REL.MOOD.FIX", "relationships", "draft"),
    ]


def test_admin_reads_a_pattern_type_with_all_its_details(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    conflict = catalog(client, headers)[0]

    del conflict["loaded_at"]
    assert conflict.pop("definition").startswith("When disagreement arises")
    assert len(conflict.pop("frameworks")) == 4
    assert conflict.pop("signs")[1] == {
        "id": "I2",
        "text": "Reports agreeing in the moment, then resenting it later",
        "strength": "strong",
        "part": "inside",
    }
    assert [sign["id"] for sign in conflict.pop("signs_against")] == ["D1", "D2"]
    assert conflict == {
        "id": "CONF.AVOID.BELONG",
        "version": "0.3.0",
        "area": "conflict",
        "name": "Conflict avoidance to preserve belonging",
        "if_situation": "Disagreement with a valued other",
        "then_behaviour": "Withholds or softens own view",
        "function": "To protect belonging",
        "look_alikes": [
            {
                "pattern_type_id": "ACH.WORTH.PERF",
                "name": "Performance-contingent self-worth",
                "tells_apart": "Keeps quiet to protect the relationship; the other "
                "fears criticism as a verdict on their competence",
            },
            {
                "pattern_type_id": "CTRL.UNCERT.PLAN",
                "name": "Control-seeking under uncertainty",
                "tells_apart": "Keeps quiet because closeness is at stake; the "
                "other is uneasy about any unknown outcome, closeness or not",
            },
            {
                "pattern_type_id": "APPR.GIVE.NEEDED",
                "name": "Saying yes and over-giving to feel needed",
                "tells_apart": "Says yes to avoid the friction of saying no; "
                "the other says yes to be needed and keep a place",
            },
            {
                "pattern_type_id": "REL.MOOD.FIX",
                "name": "Taking on other people's moods as theirs to fix",
                "tells_apart": "Stays quiet about their own view; the other acts "
                "to fix the other's mood",
            },
        ],
        "anyone_would": "Low-stakes avoidance with strangers or authority only",
        "exclusions": [
            {"text": "Active relationship crisis", "evidence": "ignored"},
            {"text": "Grief", "evidence": "ignored"},
        ],
        "approved_wording": "You seem to protect closeness by keeping "
        "disagreements small, even when they matter to you.",
        "prediction_wording": "Next time {person} asks for something you'd "
        "rather not do, notice whether you say yes before you've decided.",
        "numbers": {"situations_needed": 3, "base_rate": 0.2},
        "status": "draft",
        "approved_by": None,
        "approved_on": None,
        "other_versions": [],
    }


def test_a_look_alike_that_is_not_a_pattern_type_keeps_its_own_name(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    achievement = next(
        pattern_type
        for pattern_type in catalog(client, headers)
        if pattern_type["id"] == "ACH.WORTH.PERF"
    )

    assert achievement["look_alikes"][0] == {
        "pattern_type_id": None,
        "name": "High standards (healthy)",
        "tells_apart": "A miss brings disappointment in the work, not in the self",
    }
    assert achievement["anyone_would"].startswith("Disappointment after a real")
    assert achievement["exclusions"] == [
        {
            "text": "Active burnout or job loss in the last month",
            "evidence": "counted_not_shared",
        }
    ]


def test_an_approved_pattern_type_shows_who_approved_it_and_when(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    tmp_path: Path,
) -> None:
    headers = owner_headers(client, auth_verifier)
    approved = {
        **VALID,
        "status": "approved",
        "approved_by": "Zaf",
        "approved_on": "2026-11-24",
    }

    load_catalog(engine, tmp_path, approved)

    (pattern_type,) = catalog(client, headers)
    assert (
        pattern_type["status"],
        pattern_type["approved_by"],
        pattern_type["approved_on"],
    ) == ("approved", "Zaf", "2026-11-24")


def test_a_new_version_becomes_current_and_the_old_version_row_is_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    tmp_path: Path,
) -> None:
    headers = owner_headers(client, auth_verifier)
    load_catalog(engine, tmp_path, VALID)
    with engine.connect() as connection:
        old_row = connection.execute(text(TEST_ONE_ROWS)).one()

    load_catalog(engine, tmp_path, {**VALID, "version": "1.1.0", "name": "Renamed"})

    (pattern_type,) = catalog(client, headers)
    assert (pattern_type["version"], pattern_type["name"]) == ("1.1.0", "Renamed")
    assert pattern_type["other_versions"] == ["1.0.0"]
    assert stored_versions(engine)[-2:] == [
        ("TEST.ONE", "1.0.0", False),
        ("TEST.ONE", "1.1.0", True),
    ]
    with engine.connect() as connection:
        kept_row = connection.execute(
            text(f"{TEST_ONE_ROWS} AND version = '1.0.0'")
        ).one()
    assert (kept_row.content, kept_row.loaded_at) == (
        old_row.content,
        old_row.loaded_at,
    )
    assert kept_row.content["name"] == "Test one"


def test_loading_the_same_files_again_changes_nothing(
    engine: Engine, tmp_path: Path
) -> None:
    load_catalog(engine, tmp_path, VALID)
    with engine.connect() as connection:
        first = connection.execute(text("SELECT * FROM pattern_types")).all()

    load_catalog(engine, tmp_path, VALID)

    with engine.connect() as connection:
        assert connection.execute(text("SELECT * FROM pattern_types")).all() == first


def test_going_back_to_an_earlier_version_makes_it_current_again(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    tmp_path: Path,
) -> None:
    headers = owner_headers(client, auth_verifier)
    load_catalog(engine, tmp_path, VALID)
    load_catalog(engine, tmp_path, {**VALID, "version": "1.1.0", "name": "Renamed"})

    load_catalog(engine, tmp_path, VALID)

    (pattern_type,) = catalog(client, headers)
    assert (pattern_type["version"], pattern_type["name"]) == ("1.0.0", "Test one")
    assert pattern_type["other_versions"] == ["1.1.0"]


def test_a_change_under_a_version_already_stored_is_refused(
    engine: Engine, tmp_path: Path
) -> None:
    load_catalog(engine, tmp_path, VALID)

    with pytest.raises(InvalidPatternCatalogError) as raised:
        load_catalog(engine, tmp_path, {**VALID, "name": "Renamed"})

    assert raised.value.problems == [
        "TEST.ONE.yaml: TEST.ONE has changed but its version is still 1.0.0. "
        "Give it a new version; a stored version never changes."
    ]
    with engine.connect() as connection:
        row = connection.execute(text(TEST_ONE_ROWS)).one()
    assert row.content["name"] == "Test one"


def test_a_malformed_pattern_type_stops_the_whole_load(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    tmp_path: Path,
) -> None:
    headers = owner_headers(client, auth_verifier)
    before = stored_versions(engine)
    malformed = copy.deepcopy(VALID)
    del malformed["definition"]

    with pytest.raises(InvalidPatternCatalogError) as raised:
        load_catalog(
            engine, tmp_path, {**VALID, "id": "TEST.GOOD"}, {**malformed, "area": "x"}
        )

    assert str(raised.value) == (
        "The Pattern Catalog can't be loaded. Nothing was changed.\n"
        "- TEST.ONE.yaml: area is x; it must be one of conflict, approval, "
        "control, achievement, relationships.\n"
        "- TEST.ONE.yaml: definition is missing."
    )
    assert stored_versions(engine) == before
    assert len(catalog(client, headers)) == 15


def test_on_start_a_catalog_that_cannot_be_loaded_is_reported_and_the_last_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    headers = owner_headers(client, auth_verifier)
    (tmp_path / "bad.yaml").write_text(yaml.safe_dump({**VALID, "area": "money"}))

    load_pattern_catalog_or_keep_last(engine, tmp_path)

    assert capsys.readouterr().err == (
        "The Pattern Catalog can't be loaded. Nothing was changed.\n"
        "- bad.yaml: area is money; it must be one of conflict, approval, "
        "control, achievement, relationships.\n"
        "The backend starts with the catalog as it was last loaded.\n"
    )
    assert len(catalog(client, headers)) == 15


def test_a_pattern_type_taken_out_of_the_files_leaves_the_catalog_but_is_kept(
    client: TestClient,
    auth_verifier: FakeAuthVerifier,
    engine: Engine,
    tmp_path: Path,
) -> None:
    headers = owner_headers(client, auth_verifier)

    load_catalog(engine, tmp_path, VALID)

    assert [pattern_type["id"] for pattern_type in catalog(client, headers)] == [
        "TEST.ONE"
    ]
    assert ("CONF.AVOID.BELONG", "0.3.0", False) in stored_versions(engine)


def test_a_plain_user_cannot_read_the_pattern_catalog(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    maya = auth_headers(auth_verifier, "maya")

    response = client.get("/api/admin/pattern-catalog", headers=maya)

    assert response.status_code == 403
    assert "pattern_types" not in response.json()


def test_a_signed_out_visitor_cannot_read_the_pattern_catalog(
    client: TestClient,
) -> None:
    assert client.get("/api/admin/pattern-catalog").status_code == 401


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_the_pattern_catalog_cannot_be_changed_through_the_api(
    client: TestClient, auth_verifier: FakeAuthVerifier, method: str
) -> None:
    headers = owner_headers(client, auth_verifier)

    on_catalog = client.request(method, "/api/admin/pattern-catalog", headers=headers)
    on_pattern_type = client.request(
        method, "/api/admin/pattern-catalog/CONF.AVOID.BELONG", headers=headers
    )

    assert (on_catalog.status_code, on_pattern_type.status_code) == (405, 404)


def test_the_design_fixture_is_the_catalog_admins_read(
    client: TestClient, auth_verifier: FakeAuthVerifier
) -> None:
    headers = owner_headers(client, auth_verifier)

    pattern_types = catalog(client, headers)

    for pattern_type in pattern_types:
        pattern_type["loaded_at"] = "2026-11-24T09:00:00Z"
    assert json.loads(DESIGN_FIXTURE_CATALOG_FILE.read_text()) == {
        "pattern_types": pattern_types
    }
