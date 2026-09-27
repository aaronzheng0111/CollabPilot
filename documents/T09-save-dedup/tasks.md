# Tasks — 保存名单与去重

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T09-01

- 描述：campaigns 表与重启后读回；活动字段从会话 metadata 迁入
- 依赖：T08 verified
- 可并行：否
- 状态：`planned`
- Implement：SQLite 集成测试
- Verify：用例 5

### T09-02

- 描述：保存与排除工具在未批准时拒绝；注册 decisions 分支；pending 可被接受但不改 decision
- 依赖：T09-01
- 可并行：否
- 状态：`planned`
- Implement：approval_required
- Verify：用例 1、2、6、8

### T09-03

- 描述：按 creator_id 去重，推荐时去掉 saved、excluded、topic_rejected
- 依赖：T09-02
- 可并行：是
- 状态：`planned`
- Implement：集合语义单测
- Verify：用例 3、4

### T09-04

- 描述：goal_fingerprint 识别同一任务并沿用 campaign_id
- 依赖：T09-01
- 可并行：是
- 状态：`planned`
- Implement：同一 session 发送两次示例需求的集成测试
- Verify：用例 7

## 前端任务

### T09-F1

- 描述：主表「选中」勾选列与「保存到活动」按钮
- 依赖：T09-02
- 可并行：否
- 状态：`planned`
- Implement：`components/main_table.py` 用 data_editor，fixture 做 AppTest
- Verify：用例 9

### T09-F2

- 描述：「待你决定」保存一行；批准后 saved 列
- 依赖：T09-F1
- 可并行：否
- 状态：`planned`
- Implement：`components/pending_decisions.py` 注册文案
- Verify：用例 10

### T09-F3

- 描述：再次运行时主表上方显示跳过人数
- 依赖：T09-03、T09-04
- 可并行：是
- 状态：`planned`
- Implement：读 recommend 返回的三类人数
- Verify：用例 11


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
