# Verify — 受众信息缺失

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 受众视图四项都是「未知」，不是 null、0、空数组或不限 | 未测 |
| 2 | 自动 fit 被改成 pending 且 unknowns 含 audience | 未测 |
| 3 | 未手动接受前不在 fit 名单 | 未测 |
| 4 | MOCK 与 RULE 标记同时可见 | 未测 |
| 5 | mock 数据上 020–023 都不在 fit_creators；被改判者带 rule_override | 未测 |
| 6 | 依据面板受众四项显示「未知」与平台原文 | 未测 |
| 7 | 主表该行为「待确认」并有「受众未知」胶囊 | 未测 |
| 8 | 次级区「待确认」列表与 fit 名单分开，每行有原因 | 未测 |

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
