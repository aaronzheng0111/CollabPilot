# Tasks — 合格不足与再搜

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T07-01

- 描述：比较 fit_count 与 target_count，写入合格句式与 SearchRound
- 依赖：T06 verified
- 可并行：否
- 状态：`planned`
- Implement：纯函数
- Verify：用例 1、6

### T07-02

- 描述：第二轮只接受模型给出的 RetryStrategy；无策略则 model_strategy_required；越权字段 rule_locked
- 依赖：T07-01
- 可并行：否
- 状态：`planned`
- Implement：注入策略对象做单测，不写死 90 天
- Verify：用例 2、3、7、8

### T07-03

- 描述：不足时设置 pending_decision=accept_short_list，阻断草稿
- 依赖：T07-02
- 可并行：否
- 状态：`planned`
- Implement：状态机单测
- Verify：用例 4、5


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
