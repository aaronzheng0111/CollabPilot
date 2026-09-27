# Plan — 来源标注与提交材料

## 契约

界面组件 `source_badge(origin)`：

- `mock_seed` / `mock_api_response` → `[MOCK]`
- `real_model_output` → `[LLM]`
- 规则结构 `rule=true` → `[RULE]`
- 草稿区固定附加 `[MOCK-SEND]`

样式按 T11 `plan.md` 的「来源标签样式」。图例放在页面标题下方一行。

CLI：`agent demo reset`，在 `interfaces/cli.py` 注册；只删 SQLite 表中的行，不删库文件，不碰 `data/mock/`。

## 交付文件

以下文件在本 Task 实现时写入，规格阶段先不创建，避免把说明写成未实现的功能。内容以当时代码为准。

| 文件 | 内容 |
|------|------|
| `documents/T12-source-labels/design-note.md` | 一页设计说明：数据来源 `data/mock/`；模型判断（目标解析、适合度与主题、再搜策略、草稿、跟进）；状态存储 SQLite `backend/data/agent.db`；用户审核的 8 类待决定事项；渠道与跟进不发送；拿掉模型后停在哪一步 |
| `documents/T12-source-labels/demo-script.md` | 10 步演示脚本，对应 T11 截图 |
| `documents/T12-source-labels/two-week-plan.md` | 两周优先事项与验证方式 |
| 根目录 `README.md` | 「快速开始」一节 |

## 模块

- `frontend/components/source_badge.py`、`frontend/app.py`（图例）
- `backend/src/collabpilot/interfaces/cli.py`
- 上表四个文档
