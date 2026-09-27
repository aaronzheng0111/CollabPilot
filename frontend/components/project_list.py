from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

import streamlit as st

from collabpilot.domain.models import ProjectSummary

NEW_PROJECT = "新建项目"
RENAME_ICON = "✎"
DELETE_ICON = "✕"
CONFIRM_RENAME = "确定"
PROJECTS_TITLE = "项目"
EMPTY_NAME = "名称不能为空"
EDITING_KEY = "cp_editing_project"


def _editing_id() -> UUID | None:
    raw = st.session_state.get(EDITING_KEY)
    if not raw:
        return None
    try:
        return UUID(str(raw))
    except ValueError:
        return None


def _set_editing(project_id: UUID | None) -> None:
    if project_id is None:
        st.session_state.pop(EDITING_KEY, None)
    else:
        st.session_state[EDITING_KEY] = str(project_id)


def render_project_list(
    projects: list[ProjectSummary],
    active_id: UUID | None,
    on_select: Callable[[UUID], None],
    on_create: Callable[[], None],
    on_delete: Callable[[UUID], None],
    on_rename: Callable[[UUID, str], None] | None = None,
    rename_error: str | None = None,
) -> None:
    """Project list for Streamlit's native collapsible sidebar."""
    st.markdown(f'<p class="cp-projects-label">{PROJECTS_TITLE}</p>', unsafe_allow_html=True)
    if st.button(NEW_PROJECT, key="cp-new-project", use_container_width=True):
        _set_editing(None)
        on_create()
    if not projects:
        st.caption("还没有项目。发一条消息或点新建项目开始。")
        return

    editing_id = _editing_id()
    for project in projects:
        is_active = active_id is not None and project.session_id == active_id
        is_editing = editing_id == project.session_id
        with st.container(border=True, key=f"cp-project-box-{project.session_id}"):
            if is_editing and on_rename is not None:
                name_col, ok_col = st.columns([4, 1], vertical_alignment="center")
                with name_col:
                    name = st.text_input(
                        "项目名称",
                        value=project.title,
                        key=f"cp-rename-input-{project.session_id}",
                        label_visibility="collapsed",
                    )
                with ok_col:
                    if st.button(
                        CONFIRM_RENAME,
                        key=f"cp-rename-confirm-{project.session_id}",
                        use_container_width=True,
                    ):
                        on_rename(project.session_id, name)
                if rename_error and editing_id == project.session_id:
                    st.caption(rename_error)
            else:
                title_col, rename_col, delete_col = st.columns(
                    [4, 1, 1],
                    vertical_alignment="center",
                )
                with title_col:
                    label = f"{'● ' if is_active else ''}{project.title}"
                    if st.button(
                        label,
                        key=f"cp-project-{project.session_id}",
                        use_container_width=True,
                        type="primary" if is_active else "secondary",
                    ):
                        _set_editing(None)
                        if not is_active:
                            on_select(project.session_id)
                with rename_col:
                    if on_rename is not None and st.button(
                        RENAME_ICON,
                        key=f"cp-rename-btn-{project.session_id}",
                        help="改名",
                        use_container_width=True,
                    ):
                        st.session_state.rename_error = None
                        _set_editing(project.session_id)
                        st.rerun()
                with delete_col:
                    if st.button(
                        DELETE_ICON,
                        key=f"cp-del-project-{project.session_id}",
                        help="删除",
                        use_container_width=True,
                        type="primary",
                    ):
                        _set_editing(None)
                        on_delete(project.session_id)
