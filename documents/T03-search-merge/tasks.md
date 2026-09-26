# Tasks — 搜索与跨平台合并

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T03-01

- 描述：加载两个 JSON 并按 creator_id 建索引
- 依赖：T02 verified
- 可并行：否
- 状态：`planned`
- Implement：mock_store.py 单测条数与跨平台 id
- Verify：用例 1、2、4

### T03-02

- 描述：实现 search_creators 与 get_creator 并注册到 ToolRegistry
- 依赖：T03-01
- 可并行：否
- 状态：`planned`
- Implement：只读工具，goal 未就绪返回 goal_not_ready
- Verify：用例 3、5、6


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
