"""T11 verify cases 14–19: theme tokens vs DESIGN.md colors."""

from __future__ import annotations

import re
import tomllib

import yaml
from conftest import FRONTEND


HEX = re.compile(r"#[0-9a-fA-F]{6}")
CORAL = "#cc785c"


def _design_colors() -> dict[str, str]:
    header = (FRONTEND / "DESIGN.md").read_text(encoding="utf-8").split("---")[1]
    return {key: value.lower() for key, value in yaml.safe_load(header)["colors"].items()}


def test_config_and_theme_hex_are_in_design_colors() -> None:
    allowed = set(_design_colors().values())
    for path in (
        FRONTEND / ".streamlit" / "config.toml",
        FRONTEND / "theme.py",
    ):
        found = {match.group(0).lower() for match in HEX.finditer(path.read_text(encoding="utf-8"))}
        extra = found - allowed
        assert not extra, f"{path.name} has colors not in DESIGN.md: {extra}"


def test_canvas_card_and_no_white_background() -> None:
    colors = _design_colors()
    config = tomllib.loads((FRONTEND / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    theme = config["theme"]
    css = (FRONTEND / "theme.py").read_text(encoding="utf-8").lower()
    assert theme["backgroundColor"].lower() == colors["canvas"] == "#faf9f5"
    assert colors["surface-card"] in css
    assert "background: #ffffff" not in css
    assert "background-color: #ffffff" not in css
    assert theme["secondaryBackgroundColor"].lower() != "#ffffff"
    assert theme["backgroundColor"].lower() != "#ffffff"


def test_fonts_serif_sans_mono() -> None:
    config = tomllib.loads((FRONTEND / ".streamlit" / "config.toml").read_text(encoding="utf-8"))
    theme = config["theme"]
    css = (FRONTEND / "theme.py").read_text(encoding="utf-8")
    assert "Tiempos Headline" in theme["headingFont"]
    assert "Noto Serif SC" in theme["headingFont"]
    assert "Inter" in theme["font"]
    assert "PingFang SC" in theme["font"]
    assert "JetBrains Mono" in theme["codeFont"]
    assert "font-weight: 400" in css


def test_coral_only_on_approve_checkbox_and_focus() -> None:
    css = (FRONTEND / "theme.py").read_text(encoding="utf-8")
    config = (FRONTEND / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert CORAL in config
    lines = css.splitlines()
    for index, line in enumerate(lines):
        if CORAL.lower() not in line.lower():
            continue
        window = "\n".join(lines[max(0, index - 4) : index + 1]).lower()
        assert any(
            token in window for token in ("focus", "checkbox", "coral only", "primary")
        ), f"coral on line {index + 1}: {line}"


def test_status_and_evidence_are_dark_with_status_dots() -> None:
    css = (FRONTEND / "theme.py").read_text(encoding="utf-8")
    colors = _design_colors()
    assert ".cp-status" in css and colors["surface-dark"] in css
    assert ".cp-evidence" in css
    assert colors["on-dark"] in css
    assert "cp-status-running" in css and colors["accent-amber"] in css
    assert "cp-status-succeeded" in css and colors["success"] in css
    assert "cp-status-failed" in css and colors["error"] in css
    assert "cp-tool-line-succeeded" in css and colors["success"] in css
    assert "cp-tool-line-running" in css and "cp-spinner" in css
    assert "cp-tool-line-failed" in css and colors["error"] in css


def test_source_pills_are_distinct_capsules() -> None:
    css = (FRONTEND / "theme.py").read_text(encoding="utf-8")
    colors = _design_colors()
    assert "border-radius: 9999px" in css
    assert ".cp-pill-mock" in css and colors["surface-card"] in css
    assert ".cp-pill-rule" in css
    assert ".cp-pill-llm" in css and colors["surface-dark-elevated"] in css
    assert ".cp-pill-mock-send" in css and colors["surface-soft"] in css
    mock_bg = "background: #efe9de"
    llm_bg = "background: #252320"
    send_bg = "background: #f5f0e8"
    assert mock_bg in css and llm_bg in css and send_bg in css
    assert mock_bg != llm_bg != send_bg
