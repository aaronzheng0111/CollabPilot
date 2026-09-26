# Tasks — 匹配判断

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T05-01

- 描述：validate_verdicts：证据 id 必须存在，fit 必须有证据和连续 rank
- 依赖：T04 verified
- 可并行：否
- 状态：`planned`
- Implement：纯函数单测
- Verify：用例 1、5、6、7、8

### T05-02

- 描述：提示词与 get_creator 输出都不含 expected_ai_signals
- 依赖：T05-01
- 可并行：是
- 状态：`planned`
- Implement：测试检索提示词文件
- Verify：用例 2

### T05-03

- 描述：保存时写入 data_origin 与 model_name
- 依赖：T05-01
- 可并行：是
- 状态：`planned`
- Implement：持久化字段断言
- Verify：用例 3、4


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
