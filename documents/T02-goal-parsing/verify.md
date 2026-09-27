# Verify — 理解合作目标

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 示例原文解析出 10、3、需要审核、排除已合作 | 未测 |
| 2 | 缺品牌时假设为 LinguaGo AI 翻译并可见 | 未测 |
| 3 | 缺人数时 CLARIFYING 且不搜索 | 未测 |
| 4 | 缺触达人数时 CLARIFYING，不搜索也不生成草稿 | 未测 |
| 5 | 缺平台时作为假设而不是追问 | 未测 |
| 6 | 非法 JSON 不写入 parsed_goal | 未测 |
| 7 | 「帮我找达人」进入 CLARIFYING，至少 2 个点名问题，且不搜索 | 未测 |
| 8 | 同一次回复含「推荐过滤」或「换一种说法」 | 未测 |
| 9 | 第 3 轮仍缺关键字段时列出假设，pending_decision=confirm_assumptions | 未测 |
| 10 | 补齐关键字段后状态变为 PARSED | 未测 |
| 11 | 合作目标卡片逐项展示，假设字段带「假设」与 reason，带 LLM 标签 | 未测 |
| 12 | CLARIFYING 时主表只有固定空态文案，右栏有编号追问 | 未测 |
| 13 | 「待你决定」出现确认假设一行，批准后消失；无事项时显示固定文案 | 未测 |

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
