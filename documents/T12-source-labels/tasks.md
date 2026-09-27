# Tasks — 来源标注与提交材料

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T12-01

- 描述：`agent demo reset` 清空演示数据
- 依赖：T11 verified
- 可并行：是
- 状态：`planned`
- Implement：CLI 命令与集成测试，断言 data/mock 未变
- Verify：用例 1

## 前端任务

### T12-F1

- 描述：全页来源标签审计与顶部图例
- 依赖：T11 verified
- 可并行：是
- 状态：`planned`
- Implement：AppTest 断言标签字符串与图例；源码检索无密钥
- Verify：用例 2–7

## 文档任务

### T12-D1

- 描述：撰写不超过 900 字的 design-note.md
- 依赖：T12-F1
- 可并行：是
- 状态：`planned`
- Implement：字数与六件事检查
- Verify：用例 8

### T12-D2

- 描述：撰写 demo-script.md，并按脚本计时走查一遍
- 依赖：T12-01、T12-F1
- 可并行：否
- 状态：`planned`
- Implement：每步秒数相加在 180–300 之间
- Verify：用例 9、10

### T12-D3

- 描述：撰写 two-week-plan.md
- 依赖：T12-D1
- 可并行：是
- 状态：`planned`
- Implement：每项含为什么、做什么、如何验证
- Verify：用例 11

### T12-D4

- 描述：根目录 README「快速开始」
- 依赖：T12-01
- 可并行：是
- 状态：`planned`
- Implement：在干净目录按步骤操作一遍
- Verify：用例 12


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
