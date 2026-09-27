"""Session-as-project: list, title, delete turn, delete project."""

from __future__ import annotations

from uuid import uuid4

import pytest

from collabpilot.campaign.goal import Campaign
from collabpilot.domain.models import Message
from collabpilot.infrastructure.session_store import DEFAULT_PROJECT_TITLE


async def test_chat_titles_project_and_lists_it(application) -> None:
    result = await application.chat("为一款翻译产品找达人", provider_name="mock")
    projects = application.list_projects()
    assert len(projects) == 1
    assert projects[0].session_id == result.session_id
    assert "翻译产品" in projects[0].title


async def test_projects_isolate_history_and_campaign(application) -> None:
    first = await application.chat("甲产品", provider_name="mock")
    application.save_campaign(
        application.campaign(first.session_id).model_copy(
            update={"saved_creator_ids": ["creator_001"]}
        )
    )
    second = application.create_project("乙产品")
    await application.chat("乙产品目标", session_id=second.session_id, provider_name="mock")

    assert [m.content for m in application.history(first.session_id) if m.role == "user"] == [
        "甲产品"
    ]
    assert [m.content for m in application.history(second.session_id) if m.role == "user"] == [
        "乙产品目标"
    ]
    assert application.campaign(first.session_id).saved_creator_ids == ["creator_001"]
    assert application.campaign(second.session_id).saved_creator_ids == []


async def test_delete_turn_removes_tool_and_assistant(application) -> None:
    result = await application.chat("现在几点？", provider_name="mock")
    entries = application.history_entries(result.session_id)
    roles = [e.message.role for e in entries]
    assert "tool" in roles and "assistant" in roles
    turn_id = entries[0].turn_id

    deleted = application.delete_turn(result.session_id, turn_id)
    assert deleted >= 2
    assert application.history(result.session_id) == []


async def test_delete_message_removes_only_that_row(application) -> None:
    result = await application.chat("现在几点？", provider_name="mock")
    entries = application.history_entries(result.session_id)
    user = next(e for e in entries if e.message.role == "user")
    assistant = next(e for e in entries if e.message.role == "assistant")
    before = len(entries)

    deleted = application.delete_message(result.session_id, user.id)
    assert deleted == 1
    remaining = application.history_entries(result.session_id)
    assert len(remaining) == before - 1
    assert all(e.id != user.id for e in remaining)
    assert any(e.id == assistant.id for e in remaining)
    assert any(e.message.role == "tool" for e in remaining)

    deleted = application.delete_message(result.session_id, assistant.id)
    assert deleted >= 2
    remaining = application.history_entries(result.session_id)
    assert remaining == []


async def test_delete_assistant_also_removes_tool_rows(application) -> None:
    result = await application.chat("现在几点？", provider_name="mock")
    entries = application.history_entries(result.session_id)
    assistant = next(e for e in entries if e.message.role == "assistant")
    assert any(e.message.role == "tool" for e in entries)

    deleted = application.delete_message(result.session_id, assistant.id)
    assert deleted >= 2
    remaining = application.history_entries(result.session_id)
    assert all(e.id != assistant.id for e in remaining)
    assert all(e.message.role != "tool" for e in remaining)
    assert any(e.message.role == "user" for e in remaining)


async def test_rename_project_persists_and_rejects_empty(application) -> None:
    project = application.create_project()
    renamed = application.rename_project(project.session_id, "春季活动")
    assert renamed is not None
    assert renamed.title == "春季活动"
    assert application.list_projects()[0].title == "春季活动"
    assert application.rename_project(project.session_id, "   ") is None
    assert application.list_projects()[0].title == "春季活动"


async def test_delete_project_removes_campaign_rows(application) -> None:
    session_id = application.store.create_session("演示")
    application.save_campaign(
        Campaign(campaign_id=session_id, saved_creator_ids=["creator_001"])
    )
    application.store.add_message(
        session_id, uuid4(), Message(role="user", content="hi")
    )
    assert application.campaign(session_id).saved_creator_ids == ["creator_001"]

    application.delete_project(session_id)
    assert application.store.get_project(session_id) is None
    assert application.history(session_id) == []
    # Fresh get returns empty campaign object, not prior saved ids.
    assert application.campaign(session_id).saved_creator_ids == []
    assert application.list_projects() == []


def test_default_title_until_first_prompt(application) -> None:
    project = application.create_project()
    assert project.title == DEFAULT_PROJECT_TITLE
