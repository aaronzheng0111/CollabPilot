# Implement — 理解合作目标

状态：`in_progress`（自动化用例 1–13 已通过，等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T01。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/goal.py`（新）
- `backend/config/prompts/system.md` 或活动专用提示片段
- `backend/tests/unit/test_parsed_goal.py`（新）
- `backend/src/collabpilot/campaign/decisions.py`（新）
- `backend/tests/unit/test_decisions.py`（新）
- `frontend/components/goal_card.py`、`frontend/components/pending_decisions.py`（新）
- `frontend/components/main_table.py`、`frontend/app.py`
- `frontend/tests/test_goal_card.py`（新）


## 本 Task 补充约束

示例原文的断言用固定 fixture，不调用 DeepSeek。DeepSeek 路径只在手工验收或单独标记的集成测试中运行。

## 实现记录

- 模型在回复里输出一个 fenced JSON（ParsedGoal + 可选 `grill`），提示片段在 `backend/config/prompts/goal.md`，由 `ApplicationService.goal_prompt` 拼进 system 消息并带上当前活动状态。
- `campaign/goal.py`：`ParsedGoal`、`Grill`、`Campaign`、`CRITICAL_FIELDS`（第四项键名 `exclude_cooperated`）、`validate_parsed_goal`（`missing_critical` 由应用层重算，不信模型）、`build_grill` / `render_clarifying_reply` / `parse_grill_reply`。模型给的 `grill` 只有每个问题都点名缺失字段时才采用，否则用模板问题。
- `campaign/decisions.py`：`approve_pending` + `@register_decision`；`confirm_assumptions` 用 `CRITICAL_FALLBACKS`（10 / 3 / 需审核 / 排除已合作）补齐后进入 `PARSED`。对话里回复「确认」等价于批准。
- JSON 校验失败重试一次；仍失败不写 `parsed_goal`，状态 `CLARIFYING`，回复列出字段名（若活动已 `PARSED` 则保持不变）。回复没有 JSON 块时视为普通对话，直接透传。
- 活动记录存在 `session_metadata` 表（`session_store.py`，T09 再迁活动表）。`AgentRuntime.run` 新增 `disabled_tools`，未 `PARSED` 时对模型隐藏并拒绝 `search_creators`（`error_code=tool_disabled`）。
- Mock provider 对含「达人/创作者/合作…」的用户消息用正则拼出 ParsedGoal JSON，仅供无 Key 测试；`PARSING` 只是回合内的过渡态，未落库。
- 允许清单之外改动的文件：`agent/runtime.py`、`application.py`、`domain/models.py`（`ChatResult.goal_status`）、`infrastructure/session_store.py`、`providers/mock.py`、`frontend/theme.py`、`frontend/tests/conftest.py`（拦截 `api.deepseek.com` 并忽略 `backend/.env`，原 `test_shell.py` 在本机有 Key 时会真调 DeepSeek）。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
