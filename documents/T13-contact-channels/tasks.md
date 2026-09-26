# Tasks — 沟通渠道

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T13-01

- 描述：从 mock contact 列出渠道，unknown 与 consent 保持原值
- 依赖：T09 verified
- 可并行：否
- 状态：`planned`
- Implement：list_contacts 纯函数
- Verify：用例 1、2、5

### T13-02

- 描述：confirm_channel 需用户批准，且渠道必须在资料上
- 依赖：T13-01
- 可并行：否
- 状态：`planned`
- Implement：写 creator_channels，无发送调用
- Verify：用例 3、4、6

## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
