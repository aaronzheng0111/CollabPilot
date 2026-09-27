"""T12 verify cases 8–12: design note, demo script, two-week plan, README."""

from __future__ import annotations

import re

from collabpilot.settings import PROJECT_ROOT


DOCS = PROJECT_ROOT.parent / "documents" / "T12-source-labels"
README = PROJECT_ROOT.parent / "README.md"


def _cjk_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def _cjk_len(text: str) -> int:
    return len(re.findall(r"[\u4e00-\u9fff]", text))


def test_design_note_covers_six_topics_under_900_chars() -> None:
    text = (DOCS / "design-note.md").read_text(encoding="utf-8")
    assert _cjk_len(text) <= 900
    for needle in (
        "data/mock",
        "deepseek-chat",
        "agent.db",
        "待你决定",
        "渠道",
        "跟进",
        "拿掉",
        "model_unavailable",
        "不发出站外",
        "[MOCK-SEND]",
    ):
        assert needle in text
    for decision in (
        "确认假设",
        "接受不足人数",
        "保存名单",
        "排除创作者",
        "确认渠道",
        "保存草稿",
        "批准草稿",
        "跟进",
    ):
        assert decision in text


def test_demo_script_ten_steps_timing_and_highlights() -> None:
    text = (DOCS / "demo-script.md").read_text(encoding="utf-8")
    numbered = re.findall(r"^## \d+\. .+$", text, flags=re.MULTILINE)
    assert len(numbered) == 10
    seconds = [int(value) for value in re.findall(r"·\s*(\d+)s", text)]
    assert seconds
    total = sum(seconds[:10])
    assert 180 <= total <= 300, total
    assert "主题不符" in text or "字幕剪辑" in text
    assert "旧值" in text and "新值" in text
    assert "未知" in text
    assert "model_unavailable" in text
    assert "不产生" in text
    assert "DEEPSEEK_API_KEY" in text or "Key" in text


def test_two_week_plan_has_repeatable_checks() -> None:
    text = (DOCS / "two-week-plan.md").read_text(encoding="utf-8")
    items = re.findall(r"^## \d+\. ", text, flags=re.MULTILINE)
    assert 3 <= len(items) <= 5
    for heading in items:
        start = text.find(heading)
        chunk = text[start : start + 800]
        assert "为什么优先" in chunk
        assert "做什么" in chunk
        assert "如何验证" in chunk
    assert "pytest -m eval" in text


def test_readme_quickstart_has_six_commands_and_links() -> None:
    text = README.read_text(encoding="utf-8")
    assert "## 快速开始" in text
    section = text.split("## 快速开始", 1)[1].split("## ", 1)[0]
    fence = re.search(r"```(?:bash)?\n(.*?)```", section, flags=re.S)
    assert fence, section
    commands = [
        line.strip()
        for line in fence.group(1).splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert 1 <= len(commands) <= 6, commands
    blob = section
    assert "DEEPSEEK_API_KEY" in blob
    assert "uv sync" in blob
    assert "uv run pytest" in blob
    assert "pytest -m eval" in blob
    assert "streamlit run app.py" in blob
    assert "agent demo reset" in blob
    assert "documents/T12-source-labels/design-note.md" in section
    assert "documents/T12-source-labels/demo-script.md" in section
    assert "documents/T12-source-labels/two-week-plan.md" in section
