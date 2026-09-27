# Tasks — 工作台集成与视觉验收

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T11-01

- 描述：只读聚合 get_workbench_state
- 依赖：T14 verified
- 可并行：否
- 状态：`done`
- Implement：集成测试断言返回字段齐全、调用前后库内容不变
- Verify：用例 1

## 前端任务

### T11-F1

- 描述：app.py 按固定顺序装配全部区块，每次 rerun 只调用一次 get_workbench_state
- 依赖：T11-01
- 可并行：否
- 状态：`done`
- Implement：用 fixture WorkbenchState 做 AppTest
- Verify：用例 2、3、8、10、11、12

### T11-F2

- 描述：事件驱动主表与状态栏的回归测试
- 依赖：T11-F1
- 可并行：是
- 状态：`done`
- Implement：用假事件驱动 session_state
- Verify：用例 4、5、6、7、9、13

### T11-F3

- 描述：按视觉映射补齐 config.toml 与 theme.py；色值白名单测试
- 依赖：T11-F1
- 可并行：是
- 状态：`done`
- Implement：`tests/test_theme_tokens.py` 从 DESIGN.md 的 YAML 头读出 colors，与两个文件中的色值做集合比较
- Verify：用例 14、15、16、17、18、19

### T11-F4

- 描述：两种视口截图与完整演示走查截图
- 依赖：T11-F2、T11-F3
- 可并行：否
- 状态：`done`
- Implement：浏览器手工走查，截图存 `documents/T11-dashboard/screenshots/`
- Verify：用例 20、21


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
