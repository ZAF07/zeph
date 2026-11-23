from pathlib import Path
from typing import Any

import yaml

COMPOSE_FILE = Path(__file__).resolve().parent.parent / "docker-compose.yml"
SERVICES: dict[str, Any] = yaml.safe_load(COMPOSE_FILE.read_text())["services"]
APP_SERVICES = ("postgres", "backend", "web")


def test_eval_runner_runs_only_with_the_eval_profile() -> None:
    assert SERVICES["eval-runner"]["profiles"] == ["eval"]


def test_caddy_runs_only_with_the_prod_profile() -> None:
    assert SERVICES["caddy"]["profiles"] == ["prod"]


def test_ngrok_runs_only_with_the_local_profile() -> None:
    assert SERVICES["ngrok"]["profiles"] == ["local"]


def test_app_services_run_whatever_the_profiles() -> None:
    for name in APP_SERVICES:
        assert "profiles" not in SERVICES[name]


def test_every_service_restarts_unless_stopped() -> None:
    for name, service in SERVICES.items():
        assert service.get("restart") == "unless-stopped", name


def test_only_caddy_publishes_ports_on_every_host_address() -> None:
    for name in APP_SERVICES:
        for port in SERVICES[name]["ports"]:
            assert port.startswith("${PORT_BIND_ADDRESS:-127.0.0.1}:"), name

    assert SERVICES["caddy"]["ports"] == ["80:80", "443:443", "443:443/udp"]


def test_caddy_keeps_its_certificates_on_a_volume() -> None:
    assert "caddy-data:/data" in SERVICES["caddy"]["volumes"]


LOAD_TEST_FILE = COMPOSE_FILE.with_name("docker-compose.load-test.yml")
LOAD_TEST_SERVICES: dict[str, Any] = yaml.safe_load(LOAD_TEST_FILE.read_text())[
    "services"
]
LOAD_TEST_ADAPTER_SETTINGS = (
    "CHAT_MODEL_ADAPTER",
    "WEB_SEARCH_ADAPTER",
    "CHAT_CHANNEL_ADAPTER",
    "AUTH_VERIFIER_ADAPTER",
    "SCHEDULER_ADAPTER",
)


def test_the_main_file_never_turns_on_a_load_test() -> None:
    for name, service in SERVICES.items():
        environment = service.get("environment", {})
        assert "LOAD_TEST_RUN" not in environment, name
        assert "load_test" not in str(environment), name


def test_the_load_test_file_puts_only_the_backend_on_the_load_test_adapters() -> None:
    assert list(LOAD_TEST_SERVICES) == ["backend"]
    environment = LOAD_TEST_SERVICES["backend"]["environment"]
    assert environment["LOAD_TEST_RUN"] == "true"
    for setting in LOAD_TEST_ADAPTER_SETTINGS:
        assert environment[setting] == "load_test", setting
    assert environment["TELEGRAM_WEBHOOK_REGISTER"] == "false"
