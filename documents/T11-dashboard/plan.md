# Plan — Streamlit 工作台

## 布局

`frontend/app.py`：`st.columns([3, 2])`。

- 左栏：主表 `st.dataframe`；其下为次级区（进度、证据摘录、草稿表）。
- 右栏：顶部工具状态栏，中部对话历史，底部 `st.chat_input`。

列宽左大于右。对话不在左栏。

## 契约

- 进程内调用 `ApplicationService`。`on_event` 写入 `st.session_state.tool_status` 与 `st.session_state.table_rows` 后 `st.rerun()`。
- `tool.started`：`tool_status.state=running`，`tool_status.name` 为工具名，左表显示加载层。
- `tool.completed` 且 `ok=true`：按 `documents/PLAN.md` 的工具到表格映射替换 `table_rows`，状态为 `succeeded`。
- `tool.completed` 且 `ok=false`：不替换 `table_rows`，状态为 `failed`。
- 页面读取 campaign store 与事件，不直接解析达人 JSON。
- `CLARIFYING` 时忽略旧行，主表位置只渲染 `需求未完成，表格暂无筛选结果`。
- 启动命令写在 `frontend/README.md`。

## 状态

展示 T02–T10 已定义的状态枚举，不新增活动状态名。工具状态仅 `idle | running | succeeded | failed`。

## 模块

- `frontend/app.py`
- backend 的 optional extra `ui` 加入 `streamlit`
