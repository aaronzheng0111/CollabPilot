# Verify — 搜索与跨平台合并

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 搜索结果来自两个 mock 文件 | 未测 |
| 2 | creator_001 只聚合为一条且含两个平台 | 未测 |
| 3 | get_creator 返回两边资料且 display_name 一致 | 未测 |
| 4 | 单平台创作者的另一侧为 null | 未测 |
| 5 | 结果标明 MOCK，且不含四个测试答案字段 | 未测 |
| 6 | 目标未解析时 search_creators 返回 goal_not_ready | 未测 |
| 7 | 30 天窗口不含 007–009 且 outside_window_hits≥3；90 天窗口包含 | 未测 |
| 8 | min_followers 只去掉低于门槛的账号 | 未测 |
| 9 | backend/src 只在剔除列表中出现测试答案字段名 | 未测 |
| 10 | 搜索运行中主表保留旧行并显示加载层 | 未测 |
| 11 | 搜索成功后主表 M 行、带 MOCK，上方显示搜索参数 | 未测 |

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
