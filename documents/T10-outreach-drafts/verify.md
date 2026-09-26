# Verify — 触达草稿

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 少于 3 人时 need_three_creators | 未测 |
| 2 | 成功时 3 条 pending_review 且带来源字段 | 未测 |
| 3 | 三封 body 互不相同 | 未测 |
| 4 | cited_post_id 不属于该创作者则整批不保存 | 未测 |
| 5 | 无发送实现，状态停在 DRAFT_REVIEW | 未测 |
| 6 | 未确认时 approval_required | 未测 |
| 7 | 未确认渠道时返回 channel_unconfirmed 且不调用模型 | 未测 |
| 8 | 草稿 channel 与 confirmed_channel 一致，正文含对应渠道名称 | 未测 |

## 通过标准

- 上表每一行都有可重复的操作和观察到的结果，且与 `specify.md` 的 Given/When/Then 一一对应。
- 没有用例依赖「看起来合理」这类主观句。失败时记录实际输出。

## 失败时

1. 改 `specify.md`（若标准本身含糊或与笔试冲突）。
2. 再改 `plan.md`、`tasks.md`。
3. 最后按新规格改代码并重跑本表。
4. 不得在本 Task 未通过时开始下一个 Task。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
