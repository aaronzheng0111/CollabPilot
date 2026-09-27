# Verify — 沟通渠道

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_channels.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_channel_table.py`）。本 Task 无 DeepSeek eval。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 列表渠道等于 mock preferred_channel，并标 MOCK | 自动通过：`test_list_contacts_matches_mock_preferred_and_is_mock` |
| 2 | consent_status=unknown 显示「未知」 | 自动通过：`test_unknown_consent_is_the_string_unknown` |
| 3 | 未批准确认时 approval_required | 自动通过：`test_unapproved_confirm_is_rejected` |
| 4 | 资料上没有的渠道返回 channel_not_on_profile | 自动通过：`test_channel_not_on_profile` |
| 5 | 无可用渠道时 channel_unknown，不写入确认 | 自动通过：`test_unknown_channel_cannot_be_confirmed` |
| 6 | 确认成功后仍无发送实现 | 自动通过：`test_approved_confirm_writes_channel_and_has_no_send` |
| 7 | 渠道表每平台一行，未知值显示「未知」，带 MOCK | 自动通过：`test_channel_table_one_row_per_platform_unknowns_and_mock`；人工：待走查 |
| 8 | 确认渠道进入「待你决定」，批准后主表有 channel 列 | 自动通过：`test_confirm_queues_pending_and_channel_column_after_approve`；人工：待走查 |
| 9 | 无可用渠道的行没有确认按钮 | 自动通过：`test_unknown_channel_row_has_no_confirm_button`；人工：待走查 |
| 10 | 渠道区没有发送类按钮 | 自动通过：`test_channel_area_has_no_send_buttons`（只断言按钮文案，不含「发送前审核」）；人工：待走查 |

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
