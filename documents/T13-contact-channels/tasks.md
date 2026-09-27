# Tasks — 沟通渠道

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T13-01

- 描述：从 mock contact 列出渠道，unknown 与 consent 保持原值
- 依赖：T09 verified
- 可并行：否
- 状态：`done`
- Implement：list_contacts 纯函数
- Verify：用例 1、2、5

### T13-02

- 描述：confirm_channel 需用户批准，且渠道必须在资料上
- 依赖：T13-01
- 可并行：否
- 状态：`done`
- Implement：写 creator_channels，无发送调用；注册 decisions 分支；CHANNEL_LABELS 映射
- Verify：用例 3、4、6

## 前端任务

### T13-F1

- 描述：「沟通渠道」表，未知值显示「未知」，带 MOCK
- 依赖：T13-01
- 可并行：否
- 状态：`done`
- Implement：`components/channel_table.py`，fixture 做 AppTest
- Verify：用例 7、9

### T13-F2

- 描述：确认渠道进入「待你决定」，批准后主表 channel 列；无发送类按钮
- 依赖：T13-02、T13-F1
- 可并行：否
- 状态：`done`
- Implement：`components/pending_decisions.py` 注册文案
- Verify：用例 8、10


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
