# Plan — 会话与 DeepSeek 运行时

## 数据模型

沿用 `backend/src/collabpilot/domain/models.py` 的 `Message`、`StoredMessage`。不新增业务表。

事件对象（内存，不落库）：

```text
RuntimeEvent
  type: model.requested | tool.started | tool.completed
  session_id: str
  turn_id: str
  name: str
  ok: bool | null
  error_code: str | null      仅 tool.completed 失败时有值，供状态栏 failed 显示
```

会话库存本轮 `user`、`tool`、`assistant`（最终回复）。库里不存助手的 `tool_calls`，所以续聊时送给模型的历史不含 `tool` 消息，只含 `user` 与 `assistant`；界面按时间顺序展示三类消息。

## 契约

- `ApplicationService.chat(content, session_id=None, provider_name=None, model=None, on_delta=None, on_event=None) -> ChatResult`（沿用现有参数名，CLI 与 API 不变）
- `ApplicationService.history(session_id) -> list[Message]`：按时间顺序读回会话消息，供界面续聊
- `AgentRuntime.run(..., on_event=Callable[[RuntimeEvent], Awaitable[None]] | None)`，`RuntimeEvent` 定义在 `agent/runtime.py`
- 缺 Key：`MissingApiKeyError`，`code=missing_api_key`，在创建会话之前抛出
- 配置：`backend/config/config.example.yaml` 的 `model.default_provider=deepseek`，`model.default_model=deepseek-chat`，`runtime.max_model_calls=12`，`runtime.max_tool_calls=24`，`runtime.max_seconds=180`。
- Key：`DEEPSEEK_API_KEY`，只从环境变量读取。

## 状态

本 Task 不引入活动状态机。

## 界面

本 Task 交付页面骨架，后续 Task 只往骨架里加区块。

- `frontend/app.py`：`st.columns([3, 2])`。左栏放主表占位 `components/main_table.py` 和次级区占位；右栏放 `components/tool_status.py`、对话历史、`st.chat_input`。
- 进程内调用 `ApplicationService.chat(..., on_event=...)`。`on_event` 写入 `st.session_state.tool_status` 并重绘状态栏占位符（`st.empty()`）；本轮 `chat` 返回或报错后再 `st.rerun()`。不在回调里 `st.rerun()`，否则会中断进行中的这一轮。
- `session_id` 放在 URL 查询参数 `?session=`，刷新页面后能续聊。
- 主题：`frontend/.streamlit/config.toml` 写入 `DESIGN.md` 的颜色、字体和圆角；`frontend/theme.py` 注入 Streamlit 主题管不到的 CSS。映射表见 T11 `plan.md` 的「视觉映射」，本 Task 先落颜色、字体、圆角与状态栏样式。
- 启动：`cd frontend && uv run --project ../backend --extra ui streamlit run app.py`。

## 模块

- `backend/src/collabpilot/agent/runtime.py`：增加 `on_event`
- `backend/src/collabpilot/settings.py` 与 `config.example.yaml`：默认 DeepSeek 与预算
- `backend/src/collabpilot/infrastructure/session_store.py`：确认能按 session 读回 tool 消息
- `backend/tests/`：续聊与事件顺序用 mock provider
- `backend/pyproject.toml`：optional extra `ui` 加入 `streamlit`
- `frontend/app.py`、`frontend/theme.py`、`frontend/.streamlit/config.toml`、`frontend/components/tool_status.py`、`frontend/components/main_table.py`
- `frontend/tests/test_shell.py`：AppTest，用 mock provider
