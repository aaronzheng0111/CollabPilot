# Tasks — Streamlit 工作台

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T11-01

- 描述：左表右聊布局，右栏含状态栏、历史与输入
- 依赖：T14 verified
- 可并行：否
- 状态：`planned`
- Implement：Streamlit 页面与 session_id
- Verify：用例 1、8

### T11-02

- 描述：订阅 on_event，running 时加载，成功后按工具替换主表行
- 依赖：T11-01
- 可并行：否
- 状态：`planned`
- Implement：用假事件驱动 session_state
- Verify：用例 2、3、4、9、10、11

### T11-03

- 描述：CLARIFYING、接受人数、草稿区与无发送按钮
- 依赖：T11-02
- 可并行：否
- 状态：`planned`
- Implement：用 fixture campaign 渲染断言
- Verify：用例 5、6、7


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
