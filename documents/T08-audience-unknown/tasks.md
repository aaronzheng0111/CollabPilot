# Tasks — 受众信息缺失

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T08-01

- 描述：enforce_audience_unknown 纯函数
- 依赖：T07 verified
- 可并行：否
- 状态：`planned`
- Implement：fit 被改为 pending；mock 数据上 020–023 都不在 fit_creators
- Verify：用例 2、3、5

### T08-02

- 描述：audience_view 把 null 受众转为「未知」，并带来源标记
- 依赖：T08-01
- 可并行：是
- 状态：`planned`
- Implement：字符串断言
- Verify：用例 1、4

## 前端任务

### T08-F1

- 描述：判断依据面板受众区块显示「未知」与平台原文
- 依赖：T08-02
- 可并行：是
- 状态：`planned`
- Implement：`components/evidence_panel.py` 读 audience_view
- Verify：用例 6

### T08-F2

- 描述：主表「受众未知」胶囊与次级区「待确认」列表
- 依赖：T08-01
- 可并行：是
- 状态：`planned`
- Implement：`components/pending_list.py`，fixture 做 AppTest
- Verify：用例 7、8


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
