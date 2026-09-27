from __future__ import annotations

import os
import socket
import sys
from pathlib import Path

import pytest
import yaml
from streamlit.testing.v1 import AppTest

FRONTEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(FRONTEND))

from collabpilot.bootstrap import create_application, get_settings  # noqa: E402
from collabpilot.settings import PROJECT_ROOT, AgentSettings  # noqa: E402

BLOCKED_HOST = "api.deepseek.com"


def main_layout_columns(at: AppTest):
    """Page 3:2 columns; ignore per-project icon columns in the sidebar."""
    for index, left in enumerate(at.columns[:-1]):
        right = at.columns[index + 1]
        total = left.proto.weight + right.proto.weight
        if total and round(left.proto.weight / total, 1) == 0.6:
            return left, right
    raise AssertionError("main 3:2 layout columns not found")


def write_config(tmp_path: Path, **model: object) -> Path:
    raw = yaml.safe_load(
        (PROJECT_ROOT / "config/config.example.yaml").read_text(encoding="utf-8")
    )
    raw["app"]["database_url"] = f"sqlite:///{tmp_path / 'agent.db'}"
    raw["app"]["log_path"] = str(tmp_path / "agent.jsonl")
    raw["model"].update(model)
    path = tmp_path / "config.yaml"
    path.write_text(yaml.safe_dump(raw, allow_unicode=True), encoding="utf-8")
    return path


def use_config(monkeypatch: pytest.MonkeyPatch, path: Path) -> None:
    monkeypatch.setenv("COLLABPILOT_CONFIG", str(path))
    get_settings.cache_clear()
    create_application.cache_clear()


@pytest.fixture(autouse=True)
def offline_deepseek(monkeypatch: pytest.MonkeyPatch) -> None:
    """Never let a UI test spend real tokens: ignore backend/.env and block the host."""
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    def env_only(self: AgentSettings, provider_name: str) -> str | None:
        env_name = self.providers[provider_name].api_key_env
        return os.getenv(env_name) if env_name else None

    monkeypatch.setattr(AgentSettings, "provider_api_key", env_only)
    real_getaddrinfo = socket.getaddrinfo

    def guarded_getaddrinfo(host, *args, **kwargs):
        name = host.decode() if isinstance(host, bytes) else str(host)
        if name == BLOCKED_HOST:
            raise AssertionError(f"Tests must not reach {BLOCKED_HOST}")
        return real_getaddrinfo(host, *args, **kwargs)

    monkeypatch.setattr(socket, "getaddrinfo", guarded_getaddrinfo)


@pytest.fixture(autouse=True)
def isolated_application(monkeypatch, tmp_path):
    use_config(
        monkeypatch,
        write_config(
            tmp_path, default_provider="mock", default_model="collabpilot-mock"
        ),
    )
    yield
    get_settings.cache_clear()
    create_application.cache_clear()
