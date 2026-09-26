# Verify — 来源标注与设计说明

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 达人与帖子行有 MOCK | 未测 |
| 2 | 判断和草稿行有 LLM 与 deepseek-chat | 未测 |
| 3 | 排除行有 RULE | 未测 |
| 4 | 草稿区标明不会发送 | 未测 |
| 5 | design-note.md 含数据来源、模型判断、状态存储、用户审核、沟通渠道、跟进合作，且不超过 900 字 | 未测 |
| 6 | 界面不出现 API Key | 未测 |

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
