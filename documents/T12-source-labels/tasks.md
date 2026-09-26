# Tasks — 来源标注与设计说明

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T12-01

- 描述：左表四类标签
- 依赖：T11 verified
- 可并行：否
- 状态：`planned`
- Implement：AppTest 断言标签字符串
- Verify：用例 1–4、6

### T12-02

- 描述：撰写不超过 900 字的 design-note.md，包含渠道与跟进且写明不发送
- 依赖：T12-01
- 可并行：否
- 状态：`planned`
- Implement：字数与六件事检查
- Verify：用例 5


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
