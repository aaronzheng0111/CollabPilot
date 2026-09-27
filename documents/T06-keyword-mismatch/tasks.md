# Tasks — 关键词命中但主题不符

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T06-01

- 描述：validate_topic_verdicts：topic_conflict、quote_not_found、unclear 的取值约束
- 依赖：T05 verified
- 可并行：否
- 状态：`planned`
- Implement：手写 Verdict fixture 单测，不调用 DeepSeek
- Verify：用例 1、2

### T06-02

- 描述：lock_topic_rejections 与再次搜索时减去 topic_rejected_ids；GPM 不参与升级
- 依赖：T06-01
- 可并行：否
- 状态：`planned`
- Implement：活动字段 topic_rejected_ids；搜索后过滤并在回复中说明人数
- Verify：用例 3、4、7

### T06-03

- 描述：提示词补充主题判断要求；断言运行时代码不读 keyword_mismatch 与 scenario_tags
- 依赖：T06-01
- 可并行：是
- 状态：`planned`
- Implement：源码检索测试
- Verify：用例 5

### T06-04

- 描述：DeepSeek 评测 011–015 与对照组 001–006
- 依赖：T06-03
- 可并行：否
- 状态：`planned`
- Implement：`tests/eval/test_topic_eval.py`，对照 load_oracle
- Verify：用例 6

## 前端任务

### T06-F1

- 描述：主表「主题不符」胶囊；判断依据面板显示 quote 与锁定行，无加回按钮
- 依赖：T06-02
- 可并行：否
- 状态：`planned`
- Implement：`components/main_table.py`、`components/evidence_panel.py`，fixture 做 AppTest
- Verify：用例 8、9


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
