# Tasks — 受众信息缺失

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T08-01

- 描述：enforce_audience_unknown 纯函数
- 依赖：T07 verified
- 可并行：否
- 状态：`planned`
- Implement：fit 被改为 pending
- Verify：用例 3、4

### T08-02

- 描述：渲染 null 受众为「未知」
- 依赖：T08-01
- 可并行：是
- 状态：`planned`
- Implement：快照或字符串断言
- Verify：用例 1、2、5


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
