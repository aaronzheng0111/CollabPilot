# Tasks — 理解合作目标

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T02-01

- 描述：实现 ParsedGoal schema 与 validate_parsed_goal
- 依赖：T01 verified
- 可并行：否
- 状态：`planned`
- Implement：新增 campaign/goal.py 与单元测试
- Verify：用例 6

### T02-02

- 描述：把关键字段表写成常量：target_count、outreach_count、needs_user_approval、已合作排除
- 依赖：T02-01
- 可并行：否
- 状态：`planned`
- Implement：缺任一则 missing_critical 非空
- Verify：用例 3、4

### T02-03

- 描述：提示词要求 DeepSeek 输出 JSON；应用层写入 goal_model_name
- 依赖：T02-01
- 可并行：是
- 状态：`planned`
- Implement：从回复提取 JSON 并校验，失败不落 parsed_goal
- Verify：用例 1、2、5、7、8、9、10

### T02-04

- 描述：`approve_pending` 统一入口与 `confirm_assumptions` 分支
- 依赖：T02-03
- 可并行：否
- 状态：`planned`
- Implement：新增 campaign/decisions.py；未批准时返回 approval_required
- Verify：用例 9、13

## 前端任务

### T02-F1

- 描述：「合作目标」卡片，假设字段带「假设」与 reason，卡片带 LLM 标签
- 依赖：T02-03
- 可并行：是
- 状态：`planned`
- Implement：`components/goal_card.py`，用 fixture ParsedGoal 做 AppTest
- Verify：用例 11

### T02-F2

- 描述：CLARIFYING 时主表只显示固定空态文案
- 依赖：T02-03
- 可并行：是
- 状态：`planned`
- Implement：`components/main_table.py` 读 goal_status
- Verify：用例 12

### T02-F3

- 描述：「待你决定」卡片骨架与 confirm_assumptions 一行
- 依赖：T02-04
- 可并行：否
- 状态：`planned`
- Implement：`components/pending_decisions.py`，批准按钮调用 approve_pending
- Verify：用例 13


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
