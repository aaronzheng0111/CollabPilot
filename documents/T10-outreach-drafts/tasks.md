# Tasks — 触达草稿

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T10-01

- 描述：Draft schema、三条互异、cited_post_id 校验
- 依赖：T13 verified
- 可并行：否
- 状态：`planned`
- Implement：纯函数单测
- Verify：用例 1、3、4、7、8

### T10-02

- 描述：批准后写入 pending_review，无发送模块
- 依赖：T10-01
- 可并行：否
- 状态：`planned`
- Implement：仓库搜索发送实现并断言草稿状态
- Verify：用例 2、5、6


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
