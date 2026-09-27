# Specify — 会话与 DeepSeek 运行时

## 用户故事

品牌成员打开工作台后能开始一轮对话。关闭后再打开同一会话，能看到之前的用户消息、助手消息和工具消息。演示使用 DeepSeek，而不是 Mock 模型。

## 输入 / 输出

- 输入：用户文本、可选 `session_id`、provider=`deepseek`、model=`deepseek-chat`。
- 输出：`session_id`、助手回复、本轮工具调用次数。会话库中按时间顺序存下本轮 `user` / `assistant` / `tool` 消息。
- 事件：每轮模型请求、每次工具开始、每次工具结束各产生一条可被界面订阅的事件。事件字段至少含 `type`、`session_id`、`turn_id`、`name`（工具名或模型名）。

## 后端验收

1. Given 没有 `session_id`，When 发送一条消息，Then 返回新的 `session_id`，并且 SQLite 中能按该 id 读回这条用户消息和助手回复。
2. Given 已有 `session_id` 且其中已有 1 轮对话，When 用同一 id 再发一条消息，Then 模型请求中的历史包含上一轮用户消息与助手回复。
3. Given `.env` 中有 `DEEPSEEK_API_KEY` 且配置 `default_provider=deepseek`、`default_model=deepseek-chat`，When 不传 provider 调用对话，Then 响应里的 provider 为 `deepseek`，model 为 `deepseek-chat`。
4. Given 使用 `mock` provider，When 跑单元测试，Then 测试不访问 `api.deepseek.com`。演示命令 `uv run agent model test --provider deepseek --model deepseek-chat` 不在单元测试里强制执行。
5. Given 运行预算 `max_model_calls>=12` 且 `max_tool_calls>=24` 且 `max_seconds>=180`，When 一轮里模型连续请求工具不超过上述上限，Then 运行时不抛出预算超限。
6. Given 注册了一个只读工具并让模型调用它，When 工具执行完成，Then 订阅者依次收到 `model.requested`、`tool.started`、`tool.completed`。`tool.completed` 含 `ok` 布尔值。
7. Given 日志与界面渲染，When 发生模型或工具错误，Then 输出不包含 `DEEPSEEK_API_KEY` 的值。

## 前端验收

8. Given 在 `frontend/` 下启动 Streamlit，When 页面加载，Then 页面分左右两栏，比例 3:2；左栏是空数据表和空的次级区，右栏自上而下是工具状态栏、对话历史、输入框。
9. Given 页面主题，When 读取 `frontend/.streamlit/config.toml`，Then 底色为 `#faf9f5`，主色为 `#cc785c`，文字色为 `#141413`，与 `frontend/DESIGN.md` 的 `canvas`、`primary`、`ink` 一致。
10. Given 尚无工具调用，When 查看状态栏，Then 文案为「空闲」。Given 注入 `tool.started(name=get_current_time)` 事件，When 渲染，Then 状态栏显示该工具名与加载指示；随后注入 `tool.completed(ok=true)`，状态栏显示「完成」。
11. Given 同一 `session_id` 已有 1 轮对话，When 重新打开页面并传入该 id，Then 右栏按时间顺序显示上一轮用户消息和助手回复。

## 边界

- 不在本 Task 解析合作目标，不读达人 JSON。
- 前端只搭骨架，不渲染达人行，不实现「待你决定」卡片。
- Key 缺失时返回明确错误 `missing_api_key`，不回落到静默使用 mock。
