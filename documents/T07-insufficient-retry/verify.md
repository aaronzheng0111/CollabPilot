# Verify — 合格不足与再搜

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 首轮不足时展示合格 n/10 与缺口 | 未测 |
| 2 | 没有模型策略时返回 model_strategy_required，且不改写窗口 | 未测 |
| 3 | 第二轮名单不含已合作和关键词不符 | 未测 |
| 4 | 仍不足时等待用户决定且不写草稿 | 未测 |
| 5 | 用户拒绝后不把 unfit 改成 fit | 未测 |
| 6 | 自动再搜只有 1 次 | 未测 |
| 7 | 合法 RetryStrategy 被执行，回复含旧值、新值和 reason，并标 deepseek-chat | 未测 |
| 8 | 放宽已合作或关键词排除时返回 rule_locked | 未测 |

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
