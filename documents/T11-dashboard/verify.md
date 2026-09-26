# Verify — Streamlit 工作台

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 左栏是数据表，右栏是状态栏、对话历史和输入框 | 未测 |
| 2 | search_creators 开始时状态栏与左表都出现该工具名的加载 | 未测 |
| 3 | 成功返回 M 个创作者后主表行数为 M，列含 creator_id、display_name、platforms | 未测 |
| 4 | 硬过滤成功后主表只剩 kept | 未测 |
| 5 | CLARIFYING 时左表只有固定空态文案，右栏有追问 | 未测 |
| 6 | 待接受人数时草稿表为空 | 未测 |
| 7 | 三封草稿为待审核且无发送按钮 | 未测 |
| 8 | 同一 session 重开后右栏仍显示历史 | 未测 |
| 9 | 工具失败时状态栏为 failed，主表保持上一次成功行 | 未测 |
| 10 | fit 按 rank 升序排在 pending 与 unfit 之前 | 未测 |
| 11 | 主表有 channel，次级表有 next_step 与 follow_status | 未测 |

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
