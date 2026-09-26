# Verify — 沟通渠道

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 列表渠道等于 mock preferred_channel，并标 MOCK | 未测 |
| 2 | consent_status=unknown 显示「未知」 | 未测 |
| 3 | 未批准确认时 approval_required | 未测 |
| 4 | 资料上没有的渠道返回 channel_not_on_profile | 未测 |
| 5 | 无可用渠道时 channel_unknown，不写入确认 | 未测 |
| 6 | 确认成功后仍无发送实现 | 未测 |

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
