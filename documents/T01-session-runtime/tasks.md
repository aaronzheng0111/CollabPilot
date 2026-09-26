# Tasks — 会话与 DeepSeek 运行时

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

### T01-01

- 描述：默认 provider/model 改为 deepseek / deepseek-chat，并提高 runtime 预算
- 依赖：无
- 可并行：否
- 状态：`planned`
- Implement：改 config.example.yaml 与 settings 默认值
- Verify：用例 3、5

### T01-02

- 描述：Runtime.run 增加 on_event，在模型请求和工具开始/结束时发出事件
- 依赖：T01-01
- 可并行：否
- 状态：`planned`
- Implement：改 runtime.py，保持现有 on_delta
- Verify：用例 6

### T01-03

- 描述：同一 session_id 续聊时把历史消息送入模型
- 依赖：无
- 可并行：是
- 状态：`planned`
- Implement：核对 ApplicationService 读库存消息的顺序
- Verify：用例 1、2

### T01-04

- 描述：缺 Key 时返回 missing_api_key，且日志不含密钥
- 依赖：T01-01
- 可并行：是
- 状态：`planned`
- Implement：在 provider 初始化失败路径返回稳定错误码
- Verify：用例 4、7


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
