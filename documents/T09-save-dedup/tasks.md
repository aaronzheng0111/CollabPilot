# Tasks — 保存名单与去重

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T09-01

- 描述：campaigns 表与重启后读回
- 依赖：T08 verified
- 可并行：否
- 状态：`planned`
- Implement：SQLite 集成测试
- Verify：用例 5

### T09-02

- 描述：保存与排除工具在未批准时拒绝
- 依赖：T09-01
- 可并行：否
- 状态：`planned`
- Implement：approval_required
- Verify：用例 1、2、6

### T09-03

- 描述：按 creator_id 去重，推荐时去掉 excluded
- 依赖：T09-02
- 可并行：是
- 状态：`planned`
- Implement：集合语义单测
- Verify：用例 3、4


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
