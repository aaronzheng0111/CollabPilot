# Implement — 跟进合作

状态：`in_progress`（自动化用例 1–9 已通过；等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。
- 跟进正文来自 DeepSeek，标 `real_model_output` 与 `model_name=deepseek-chat`。
- 单测注入假的模型 JSON，不访问 `api.deepseek.com`。
- 不发送消息，不新增 `SENDING` 状态。
- 前序 Task：T10。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/follow_up.py`
- `backend/src/collabpilot/infrastructure/campaign_store.py`
- `backend/tests/unit/test_follow_up.py`
- `backend/src/collabpilot/campaign/decisions.py`
- `frontend/components/follow_up_table.py`（新）、`frontend/components/pending_decisions.py`
- `frontend/tests/test_follow_up_table.py`（新）

## 本 Task 补充约束

`channel` 只能复制已确认渠道，模型若改写渠道则拒绝保存。

## 实现记录

- `campaign/follow_up.py`：`validate_follow_up` 要求草稿 `approved` 且 `channel` 等于 `confirmed_channel`；空 `next_step` 整条不保存。未批准草稿不调模型（`draft_not_approved`）。
- 写跟进是 application 层独立调用，`temperature=creative_temperature`（0.85），提示词 `config/prompts/follow_up.md`。校验通过后排队 `save_follow_up`；`user_approved` 后写入 SQLite `follow_ups` 表，状态 `waiting_user`，阶段 `FOLLOW_UP`。无 `SENDING`。`note_follow_up` 只改 `noted`。
- 前端：`follow_up_table.py` 次级表；「待你决定」先「记录对 {name} 的跟进」，保存后「记下对 {name} 的跟进」。固定 caption「记下不等于发送 [MOCK-SEND]」。无发送按钮。

允许清单之外改动的文件：`application.py`、`campaign/goal.py`（`FOLLOW_UP`）、`campaign/retry.py`（阶段文案）、`campaign/workbench.py`、`tools/policy.py`、`tools/registry.py`、`tools/builtin/save_follow_up.py`、`settings.py`、`config/config.example.yaml`、`config/prompts/follow_up.md`、`providers/mock.py`、`frontend/app.py`。

## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
