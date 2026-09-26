# Tasks — 跟进合作

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T14-01

- 描述：validate_follow_up 要求已批准草稿且渠道一致
- 依赖：T10 verified
- 可并行：否
- 状态：`planned`
- Implement：纯函数单测
- Verify：用例 1、2

### T14-02

- 描述：确认后写入 waiting_user；记下后改为 noted；无发送
- 依赖：T14-01
- 可并行：否
- 状态：`planned`
- Implement：follow_ups 表与两个写操作
- Verify：用例 3、4、5、6

## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
