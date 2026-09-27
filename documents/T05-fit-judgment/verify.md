# Verify — 匹配判断

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 证据 id 不在帖子或 evidence 中则拒绝保存 | 未测 |
| 2 | 提示词与工具结果不含测试答案字段，界面不展示 expected_decision_hint | 未测 |
| 3 | GPM 未知时 unknowns 含 gpm 且不出现编造数字 | 未测 |
| 4 | 保存结果含 real_model_output 与 deepseek-chat | 未测 |
| 5 | 无证据的 fit 返回 evidence_required | 未测 |
| 6 | fit 的 rank 必须是从 1 开始且不重复，否则 rank_invalid | 未测 |
| 7 | unfit 与 pending 的 rank 必须为 null | 未测 |
| 8 | 展示顺序为 fit 的 rank 升序，然后 pending，然后 unfit | 未测 |
| 9 | 提示词中每条帖子带 age_days，并写明排序原则与 exclusion_rules | 未测 |
| 10 | fit 的 related_post_ids 非空且属于该创作者；recency 由应用层计算 | 未测 |
| 11 | 模型不可用时无 Verdict、回复 model_unavailable、无备用排序 | 未测 |
| 12 | eval：001–006 全为 fit；011–015 无 fit（附模型原始输出） | 未测 |
| 13 | 主表显示 decision 中文与 rank，顺序正确，带 LLM | 未测 |
| 14 | 判断依据面板展示理由、帖子原文、age_days、recency、未知项与 deepseek-chat | 未测 |

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
