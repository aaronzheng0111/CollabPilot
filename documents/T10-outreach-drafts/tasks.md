# Tasks — 触达草稿

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T10-01

- 描述：Draft schema 与 validate_drafts：三条互异、cited_post_id 校验、原文片段、渠道名称
- 依赖：T13 verified
- 可并行：否
- 状态：`done`
- Implement：纯函数单测
- Verify：用例 1、3、4、7、8、9

### T10-02

- 描述：批准后写入 pending_review；approve_draft / reject_draft；无发送模块
- 依赖：T10-01
- 可并行：否
- 状态：`done`
- Implement：仓库搜索发送实现并断言草稿状态；注册 decisions 分支
- Verify：用例 2、5、6

### T10-03

- 描述：DeepSeek 评测为 001–003 生成草稿
- 依赖：T10-02
- 可并行：否
- 状态：`done`
- Implement：`tests/eval/test_drafts_eval.py`，标记 eval
- Verify：用例 10

## 前端任务

### T10-F1

- 描述：草稿卡片：创作者、渠道、被引用原文、正文、状态；固定「草稿不会发送」
- 依赖：T10-02
- 可并行：否
- 状态：`done`
- Implement：`components/draft_cards.py`，fixture 做 AppTest
- Verify：用例 11、13

### T10-F2

- 描述：「待你决定」中的保存草稿与逐封审核
- 依赖：T10-F1
- 可并行：否
- 状态：`done`
- Implement：`components/pending_decisions.py` 注册文案
- Verify：用例 12


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
