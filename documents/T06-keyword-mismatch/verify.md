# Verify — 关键词命中但主题不符

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | mismatch 且 fit 返回 topic_conflict，不保存 | 未测 |
| 2 | mismatch 缺主题、证据或 quote 不是帖子原文子串时返回 quote_not_found | 未测 |
| 3 | mismatch 进入 topic_rejected_ids，后续轮次不重判也不推荐 | 未测 |
| 4 | GPM 高于 target_gpm 仍不在最终候选 | 未测 |
| 5 | backend/src 不读 keyword_mismatch 与 scenario_tags | 未测 |
| 6 | eval：011–015 全部 mismatch+unfit，001–006 无 mismatch（附模型原文） | 未测 |
| 7 | 判断与理由标 LLM，锁定动作标 RULE | 未测 |
| 8 | 主表该行为「不合适」并有「主题不符」胶囊 | 未测 |
| 9 | 依据面板显示 quote 与帖子 id，锁定行标 RULE，无加回按钮 | 未测 |

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
