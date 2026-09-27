# Tasks — 会话与 DeepSeek 运行时

原子步骤。状态只允许 `planned` / `in_progress` / `done`。包级别评估见 `verify.md`。

## 后端任务

### T01-01

- 描述：默认 provider/model 改为 deepseek / deepseek-chat，并提高 runtime 预算
- 依赖：无
- 可并行：否
- 状态：`done`
- Implement：改 config.example.yaml 与 settings 默认值
- Verify：用例 3、5

### T01-02

- 描述：Runtime.run 增加 on_event，在模型请求和工具开始/结束时发出事件
- 依赖：T01-01
- 可并行：否
- 状态：`done`
- Implement：改 runtime.py，保持现有 on_delta
- Verify：用例 6

### T01-03

- 描述：同一 session_id 续聊时把历史消息送入模型
- 依赖：无
- 可并行：是
- 状态：`done`
- Implement：核对 ApplicationService 读库存消息的顺序
- Verify：用例 1、2

### T01-04

- 描述：缺 Key 时返回 missing_api_key，且日志不含密钥
- 依赖：T01-01
- 可并行：是
- 状态：`done`
- Implement：在 provider 初始化失败路径返回稳定错误码
- Verify：用例 4、7

## 前端任务

### T01-F1

- 描述：Streamlit 左右 3:2 骨架，右栏状态栏、对话历史、输入框；`ui` extra 加入 streamlit
- 依赖：T01-03
- 可并行：否
- 状态：`done`
- Implement：`frontend/app.py` 进程内调用 `ApplicationService`，session_id 放 URL 查询参数
- Verify：用例 8、11

### T01-F2

- 描述：按 `frontend/DESIGN.md` 写主题配置与 `theme.py`
- 依赖：T01-F1
- 可并行：是
- 状态：`done`
- Implement：`config.toml` 写颜色、字体、圆角；`theme.py` 注入衬线标题与深色状态栏 CSS
- Verify：用例 9

### T01-F3

- 描述：订阅 `on_event` 驱动状态栏 idle / running / succeeded / failed
- 依赖：T01-02、T01-F1
- 可并行：否
- 状态：`done`
- Implement：`components/tool_status.py`，用假事件做 AppTest
- Verify：用例 10


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
