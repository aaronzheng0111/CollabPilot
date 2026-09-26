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
```

## 契约

- `ApplicationService.chat(message, session_id=None, provider=None, model=None) -> ChatResult`
- `AgentRuntime.run(..., on_event=Callable[[RuntimeEvent], Awaitable[None]] | None)`
- 配置：`backend/config/config.example.yaml` 的 `model.default_provider=deepseek`，`model.default_model=deepseek-chat`，`runtime.max_model_calls=12`，`runtime.max_tool_calls=24`，`runtime.max_seconds=180`。
- Key：`DEEPSEEK_API_KEY`，只从环境变量读取。

## 状态

本 Task 不引入活动状态机。

## 界面

无。事件回调留给 T11 订阅。

## 模块

- `backend/src/collabpilot/agent/runtime.py`：增加 `on_event`
- `backend/src/collabpilot/settings.py` 与 `config.example.yaml`：默认 DeepSeek 与预算
- `backend/src/collabpilot/infrastructure/session_store.py`：确认能按 session 读回 tool 消息
- `backend/tests/`：续聊与事件顺序用 mock provider
