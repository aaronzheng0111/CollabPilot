# Tasks — 匹配判断

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T05-01

- 描述：validate_verdicts：证据 id 与 related_post_ids 必须存在，fit 必须有证据和连续 rank；计算 recency
- 依赖：T04 verified
- 可并行：否
- 状态：`done`
- Implement：纯函数单测
- Verify：用例 1、5、6、7、8、10

### T05-02

- 描述：提示词带 age_days、排序原则与 exclusion_rules，且不含测试答案字段
- 依赖：T05-01
- 可并行：是
- 状态：`done`
- Implement：测试检索提示词文件与渲染后的提示词
- Verify：用例 2、9

### T05-03

- 描述：保存时写入 data_origin 与 model_name；GPM 未知写入 unknowns
- 依赖：T05-01
- 可并行：是
- 状态：`done`
- Implement：持久化字段断言
- Verify：用例 3、4

### T05-04

- 描述：模型不可用时返回 model_unavailable，无备用排序
- 依赖：T05-01
- 可并行：是
- 状态：`done`
- Implement：provider 抛错的单测；搜索代码中没有按粉丝或命中数排序的名单函数
- Verify：用例 11

### T05-05

- 描述：DeepSeek 评测用例，对照 load_oracle
- 依赖：T05-02、T05-03
- 可并行：否
- 状态：`done`
- Implement：`tests/eval/test_fit_eval.py`，标记 eval
- Verify：用例 12

## 前端任务

### T05-F1

- 描述：主表 decision 与 rank 列及排序
- 依赖：T05-01
- 可并行：是
- 状态：`done`
- Implement：`components/main_table.py`，fixture Verdict 做 AppTest
- Verify：用例 13

### T05-F2

- 描述：「判断依据」深色面板：理由、帖子原文、age_days、recency、未知项
- 依赖：T05-01
- 可并行：是
- 状态：`done`
- Implement：`components/evidence_panel.py`
- Verify：用例 14


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
