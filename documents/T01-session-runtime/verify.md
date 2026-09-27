# Verify — 会话与 DeepSeek 运行时

全部用例通过才算本 Task `verified`。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 新会话写入并可按 session_id 读回 | 通过：`test_new_session_is_readable_from_sqlite` |
| 2 | 同一 session_id 的第二轮请求包含第一轮历史 | 通过：`test_second_turn_sends_first_turn_history` |
| 3 | 默认调用命中 deepseek / deepseek-chat（有 Key 的手工检查；自动化只断言配置值） | 自动化通过：`test_example_config_defaults_to_deepseek_and_budget`、`test_chat_without_provider_uses_deepseek`（假 Key，不联网）。真实 Key 手工检查已通过，见 `manual-eval.md` M3 |
| 4 | mock 测试不访问 api.deepseek.com | 通过：`backend/tests/conftest.py` 的 `offline_deepseek` 对全部后端测试拦截该域名解析；`test_deepseek_host_is_blocked_in_tests` |
| 5 | 预算常量为 12 / 24 / 180 | 通过：`test_example_config_defaults_to_deepseek_and_budget`、`test_budget_allows_twelve_model_calls_and_twenty_four_tools`（12 次模型请求、24 次工具调用不抛预算超限） |
| 6 | 工具调用产生 model.requested、tool.started、tool.completed 且顺序正确 | 通过：`test_tool_call_emits_events_in_order`、`test_failed_tool_emits_completed_with_error_code` |
| 7 | 错误文本中不出现密钥字符串 | 通过：`test_missing_key_raises_missing_api_key`、`test_provider_error_does_not_leak_key`（后端日志与异常）、`test_provider_error_is_rendered_without_key`（页面） |
| 8 | 页面左右 3:2，右栏自上而下为状态栏、对话历史、输入框 | 通过：`test_layout_is_three_to_two_with_status_history_input`（列权重 0.6 / 0.4） |
| 9 | 主题底色、主色、文字色与 DESIGN.md 的 canvas、primary、ink 一致 | 通过：`test_theme_matches_design_tokens` |
| 10 | 状态栏从「空闲」到工具名加载，再到「完成」 | 通过：`test_status_goes_idle_running_done`、`test_chat_turn_drives_status_and_session_query` |
| 11 | 同一 session 重开后右栏显示上一轮对话 | 通过：`test_reopened_session_shows_previous_turn` |

运行方式：

```bash
cd backend && uv run --extra dev pytest
cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests
```

## 通过标准

- 上表每一行都有可重复的操作和观察到的结果，且与 `specify.md` 的 Given/When/Then 一一对应。
- 没有用例依赖「看起来合理」这类主观句。失败时记录实际输出。

## 失败时

1. 改 `specify.md`（若标准本身含糊或与笔试冲突）。
2. 再改 `plan.md`、`tasks.md`。
3. 最后按新规格改代码并重跑本表。
4. 不得在本 Task 未通过时开始下一个 Task。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
