# Implement — 沟通渠道

状态：`in_progress`（自动化用例 1–10 已通过；本 Task 无 eval；等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T09。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/channels.py`
- `backend/src/collabpilot/tools/builtin/confirm_channel.py`
- `backend/src/collabpilot/infrastructure/campaign_store.py`
- `backend/tests/unit/test_channels.py`
- `backend/src/collabpilot/campaign/decisions.py`
- `frontend/components/channel_table.py`（新）、`frontend/components/pending_decisions.py`、`frontend/components/main_table.py`
- `frontend/tests/test_channel_table.py`（新）


## 本 Task 补充约束

`consent_status=unknown` 时展示字符串必须是「未知」。


## 实现记录

- `campaign/channels.py`：`list_contacts` 按平台各一行读 mock `contact`，不合并猜测渠道；`unknown` 与空邮箱展示「未知」；`CHANNEL_LABELS` 供前端与 T10 共用。`validate_channel` 只允许资料上的 `tiktok_dm` / `instagram_dm` / 非空 `email`。`confirm_channel` 需 `user_approved`，未批准只排队。
- SQLite `creator_channels` 与 `Campaign.confirmed_channels` 同步；写工具 `confirm_channel` 标 `risk_level=write`，无 SMTP / TikTok / Instagram 发送路径。`decisions.py` 注册 `confirm_channel`。
- 前端：`channel_table.py` 次级区「沟通渠道」，未知渠道行只有「资料中没有可用渠道」；「确认渠道」secondary 排队；批准后主表 `channel` 列。AppTest 无发送类按钮（只比按钮文案，避免命中目标卡「发送前审核」）。

允许清单之外改动的文件：`campaign/goal.py`（`confirmed_channels`）、`application.py`、`campaign/workbench.py`、`tools/policy.py`、`tools/registry.py`、`settings.py`、`config/config.example.yaml`、`frontend/app.py`。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
