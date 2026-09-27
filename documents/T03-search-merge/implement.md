# Implement — 搜索与跨平台合并

状态：`not_started`

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T02。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/mock_store.py`
- `backend/src/collabpilot/tools/builtin/search_creators.py`
- `backend/src/collabpilot/tools/builtin/get_creator.py`
- `backend/src/collabpilot/bootstrap.py`（注册工具）
- `backend/tests/unit/test_mock_store.py`
- `backend/tests/unit/test_search_creators.py`
- `frontend/components/main_table.py`
- `frontend/tests/test_main_table.py`


## 本 Task 补充约束

工具返回给模型的单条达人详情必须截断到 runtime `max_tool_result_chars`。截断时保留 `creator_id` 与 `truncated=true`。

`window_days` 与 `min_followers` 的默认值只在工具签名里出现一次，不在其他模块另写常量。测试答案字段只能经 `load_oracle()` 读取，且只在 `backend/tests/` 中调用。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
