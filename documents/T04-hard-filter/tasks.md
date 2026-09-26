# Tasks — 硬过滤

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T04-01

- 描述：纯函数 hard_filter(merged, platforms) -> kept, removed
- 依赖：T03 verified
- 可并行：否
- 状态：`planned`
- Implement：单测覆盖已合作、标签、平台不匹配
- Verify：用例 1–4、6

### T04-02

- 描述：注册工具并写入活动 last_filter
- 依赖：T04-01
- 可并行：否
- 状态：`planned`
- Implement：结果带 RULE 标记
- Verify：用例 5


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
