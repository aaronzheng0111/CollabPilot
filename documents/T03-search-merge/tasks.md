# Tasks — 搜索与跨平台合并

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T03-01

- 描述：加载两个 JSON，剔除测试答案字段，按 creator_id 建索引；帖子换算 age_days
- 依赖：T02 verified
- 可并行：否
- 状态：`planned`
- Implement：mock_store.py 单测条数、跨平台 id、剔除字段
- Verify：用例 1、2、4、5、9

### T03-02

- 描述：实现 search_creators（含 window_days、min_followers、outside_window_hits）与 get_creator 并注册到 ToolRegistry
- 依赖：T03-01
- 可并行：否
- 状态：`planned`
- Implement：只读工具，goal 未就绪返回 goal_not_ready
- Verify：用例 3、6、7、8

## 前端任务

### T03-F1

- 描述：主表渲染 search_creators 结果与加载层，上方显示搜索参数
- 依赖：T03-02
- 可并行：否
- 状态：`planned`
- Implement：`components/main_table.py`，用假事件与 fixture 结果做 AppTest
- Verify：用例 10、11


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
