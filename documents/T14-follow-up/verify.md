# Verify — 跟进合作

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_follow_up.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_follow_up_table.py`）。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 草稿未批准时 draft_not_approved | 自动通过：`test_unapproved_draft_is_draft_not_approved`、`test_unapproved_draft_does_not_call_model` |
| 2 | 渠道与 confirmed_channel 不一致时 channel_mismatch | 自动通过：`test_channel_mismatch_is_not_saved` |
| 3 | 确认后写入 waiting_user，并标 deepseek-chat | 自动通过：`test_approved_save_writes_waiting_user_and_origin` |
| 4 | 未确认保存时 approval_required | 自动通过：`test_unapproved_save_is_approval_required` |
| 5 | 记下后状态为 noted 且无发送记录 | 自动通过：`test_note_changes_status_and_has_no_send` |
| 6 | 跟进模块无 TikTok、Instagram、SMTP 发送调用 | 自动通过：同上（无 smtp/send_mail/tiktok.com/SENDING） |
| 7 | 跟进表展示创作者、渠道、next_step、中文状态，带 LLM | 自动通过：`test_follow_up_table_shows_creator_channel_step_status_and_llm`；人工：待走查 |
| 8 | 「待你决定」出现记录跟进，批准后跟进表有该行 | 自动通过：`test_pending_record_follow_up_then_table_waiting_user`；人工：待走查 |
| 9 | 批准记下后显示「已记下」，无发送类按钮 | 自动通过：`test_note_follow_up_shows_noted_and_has_no_send_buttons`；人工：待走查 |

## 通过标准

- 上表每一行都有可重复的操作和观察到的结果，且与 `specify.md` 的 Given/When/Then 一一对应。
- 没有用例依赖「看起来合理」这类主观句。失败时记录实际输出。

## 失败时

1. 改 `specify.md`。
2. 再改 `plan.md`、`tasks.md`。
3. 最后按新规格改代码并重跑本表。
4. 不得在本 Task 未通过时开始下一个 Task。

## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
