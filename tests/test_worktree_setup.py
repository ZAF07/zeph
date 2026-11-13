from scripts.worktree_setup import (
    Ports,
    build_worktree_env,
    choose_ports,
    compose_project_name,
    read_env_value,
)

MAIN_ENV = """COMPOSE_PROFILES=local
POSTGRES_USER=companion
NEXT_PUBLIC_API_URL=http://localhost:8000
DASHBOARD_URL=http://localhost:3000
TELEGRAM_BOT_TOKEN=123:abc
"""


def test_first_free_slot_after_the_main_ports_is_chosen() -> None:
    ports = choose_ports(is_port_free=lambda port: True, taken_web_ports=set())

    assert ports == Ports(web=3010, backend=8010, postgres=5442)


def test_slot_with_a_busy_port_is_skipped() -> None:
    ports = choose_ports(is_port_free=lambda port: port != 8010, taken_web_ports=set())

    assert ports == Ports(web=3020, backend=8020, postgres=5452)


def test_slot_claimed_by_another_worktree_is_skipped_even_when_stopped() -> None:
    ports = choose_ports(is_port_free=lambda port: True, taken_web_ports={3010})

    assert ports == Ports(web=3020, backend=8020, postgres=5452)


def test_worktree_env_keeps_secrets_and_sets_its_own_ports_and_project() -> None:
    env = build_worktree_env(
        MAIN_ENV, Ports(web=3010, backend=8010, postgres=5442), "zeph-photos-04"
    )

    assert read_env_value(env, "TELEGRAM_BOT_TOKEN") == "123:abc"
    assert read_env_value(env, "POSTGRES_USER") == "companion"
    assert read_env_value(env, "WEB_PORT") == "3010"
    assert read_env_value(env, "BACKEND_PORT") == "8010"
    assert read_env_value(env, "POSTGRES_PORT") == "5442"
    assert read_env_value(env, "NEXT_PUBLIC_API_URL") == "http://localhost:8010"
    assert read_env_value(env, "DASHBOARD_URL") == "http://localhost:3010"
    assert read_env_value(env, "COMPOSE_PROJECT_NAME") == "zeph-photos-04"


def test_worktree_env_turns_off_telegram_webhook_and_ngrok() -> None:
    env = build_worktree_env(
        MAIN_ENV, Ports(web=3010, backend=8010, postgres=5442), "zeph"
    )

    assert read_env_value(env, "TELEGRAM_WEBHOOK_REGISTER") == "false"
    assert read_env_value(env, "COMPOSE_PROFILES") == ""


def test_worktree_env_sets_each_key_only_once() -> None:
    env = build_worktree_env(
        MAIN_ENV, Ports(web=3010, backend=8010, postgres=5442), "zeph"
    )

    assert env.count("DASHBOARD_URL=") == 1
    assert env.count("COMPOSE_PROFILES=") == 1


def test_missing_env_value_reads_as_none() -> None:
    assert read_env_value(MAIN_ENV, "WEB_PORT") is None


def test_compose_project_name_is_lower_case_with_only_safe_characters() -> None:
    assert compose_project_name("AI-Chat Companion.photos_04") == (
        "ai-chat-companion-photos_04"
    )
