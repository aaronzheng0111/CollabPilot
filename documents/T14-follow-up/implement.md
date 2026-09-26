# Implement — 跟进合作

状态：`not_started`

## 约束

- Python 3.11。后端只改 `backend/`。
- 跟进正文来自 DeepSeek，标 `real_model_output` 与 `model_name=deepseek-chat`。
- 单测注入假的模型 JSON，不访问 `api.deepseek.com`。
- 不发送消息，不新增 `SENDING` 状态。
- 前序 Task：T10。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/starter_agent/campaign/follow_up.py`
- `backend/src/starter_agent/infrastructure/campaign_store.py`
- `backend/tests/unit/test_follow_up.py`

## 本 Task 补充约束

`channel` 只能复制已确认渠道，模型若改写渠道则拒绝保存。

## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
