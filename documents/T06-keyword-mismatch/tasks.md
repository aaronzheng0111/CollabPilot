# Tasks — 关键词命中但主题不符

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T06-01

- 描述：实现 reject_keyword_mismatches 并单测 GPM 高仍排除
- 依赖：T05 verified
- 可并行：否
- 状态：`planned`
- Implement：用 mock 数据中带 keyword_mismatch 的 id
- Verify：用例 1、3、4

### T06-02

- 描述：解释结构带 source_post_id 与不超过 80 字的片段
- 依赖：T06-01
- 可并行：否
- 状态：`planned`
- Implement：从首条帖子截取
- Verify：用例 2、5


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
