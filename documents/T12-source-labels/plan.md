# Plan — 来源标注与设计说明

## 契约

界面组件 `source_badge(origin)`：

- `mock_seed` / `mock_api_response` → `[MOCK]`
- `real_model_output` → `[LLM]`
- 规则结构 `rule=true` → `[RULE]`
- 草稿区固定附加 `[MOCK-SEND]`

## 交付文件

- `documents/T12-source-labels/design-note.md` 由本 Task 实现时写入，规格阶段先空着，避免把说明写成未实现的功能。
- 实现时以当时代码为准填写路径：`data/mock/`、SQLite `backend/data/agent.db`、DeepSeek `deepseek-chat`。

## 模块

- `frontend/app.py` 中的 badge 函数
- `documents/T12-source-labels/design-note.md`
