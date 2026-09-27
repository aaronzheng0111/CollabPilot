# Tasks — 合格不足与再搜

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T07-01

- 描述：比较 fit_count 与 target_count，写入合格句式与 SearchRound
- 依赖：T06 verified
- 可并行：否
- 状态：`planned`
- Implement：纯函数
- Verify：用例 1、6

### T07-02

- 描述：build_round_summary 生成发给模型的首轮摘要
- 依赖：T07-01
- 可并行：否
- 状态：`planned`
- Implement：纯函数单测，断言不含测试答案字段
- Verify：用例 9

### T07-03

- 描述：第二轮只接受模型给出的 RetryStrategy；无策略则 model_strategy_required；越权字段 rule_locked
- 依赖：T07-02
- 可并行：否
- 状态：`planned`
- Implement：注入策略对象做单测，不写死 90 天；在 mock 数据上断言 007–009 出现
- Verify：用例 2、3、7、8、10

### T07-04

- 描述：不足时设置 pending_decision=accept_short_list，阻断草稿
- 依赖：T07-03
- 可并行：否
- 状态：`planned`
- Implement：状态机单测；在 decisions.py 注册分支
- Verify：用例 4、5

### T07-05

- 描述：DeepSeek 评测：首轮摘要 → 策略 → 第二轮人数
- 依赖：T07-04
- 可并行：否
- 状态：`planned`
- Implement：`tests/eval/test_retry_eval.py`，标记 eval
- Verify：用例 11

## 前端任务

### T07-F1

- 描述：「进度」区块与「调整了什么」表
- 依赖：T07-03
- 可并行：是
- 状态：`planned`
- Implement：`components/progress_panel.py`，fixture 两轮数据做 AppTest
- Verify：用例 12、13

### T07-F2

- 描述：「待你决定」中的是否接受当前人数，草稿表为空
- 依赖：T07-04
- 可并行：是
- 状态：`planned`
- Implement：`components/pending_decisions.py` 注册文案
- Verify：用例 14


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
