# Verify — 跟进合作

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 草稿未批准时 draft_not_approved | 未测 |
| 2 | 渠道与 confirmed_channel 不一致时 channel_mismatch | 未测 |
| 3 | 确认后写入 waiting_user，并标 deepseek-chat | 未测 |
| 4 | 未确认保存时 approval_required | 未测 |
| 5 | 记下后状态为 noted 且无发送记录 | 未测 |
| 6 | 跟进模块无 TikTok、Instagram、SMTP 发送调用 | 未测 |
| 7 | 跟进表展示创作者、渠道、next_step、中文状态，带 LLM | 未测 |
| 8 | 「待你决定」出现记录跟进，批准后跟进表有该行 | 未测 |
| 9 | 批准记下后显示「已记下」，无发送类按钮 | 未测 |

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
