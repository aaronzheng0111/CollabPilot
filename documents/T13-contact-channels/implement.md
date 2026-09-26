# Implement — 沟通渠道

状态：`not_started`

## 约束

- Python 3.11。后端只改 `backend/`。模拟达人 JSON 只读 `data/mock/`。
- 不调用 DeepSeek 猜测渠道。渠道只读 mock `contact`。
- 不发送私信或邮件。
- 前序 Task：T09。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/channels.py`
- `backend/src/collabpilot/tools/builtin/confirm_channel.py`
- `backend/src/collabpilot/infrastructure/campaign_store.py`
- `backend/tests/unit/test_channels.py`

## 本 Task 补充约束

`consent_status=unknown` 时展示字符串必须是「未知」。

## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
