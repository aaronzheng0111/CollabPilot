# Implement — 搜索与跨平台合并

状态：`in_progress`（自动化用例 1–11 已通过，等人工走查后改 `verified`）

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

## 实现记录

- `campaign/mock_store.py`：`load()` 读仓库根 `data/mock/` 两个 JSON（路径 `PROJECT_ROOT.parent/data/mock`），递归剔除 `ORACLE_FIELDS`（含 `cooperation_history[].product_relation`，保证结果里不出现这四个键），按 `creator_id` 合并为 `MergedCreator{tiktok, instagram, platforms}`，帖子加 `post_id` 与 `age_days`（基准 `meta.generated_at`=2026-09-26）。`load_brand()` 读 JSON 的 `brand` 块供 T05 提示词用；`load_oracle()` 只给测试。
- `tools/builtin/search_creators.py`：纯函数 `run_search` + `SearchCreatorsTool`。默认值只写在 `input_schema`（`window_days=30`、`min_followers=null`、`limit=50`），代码经 `default()` 读取。返回 `accounts[]`（`account_id=<platform>:<handle>`）、`creators[]`（含 `account_ids`）、`meta`（`is_mock`、`outside_window_hits` 只给人数）。`goal_status!=PARSED` 返回 `goal_not_ready`。成功后写活动 `stage=SEARCHING`、`last_search{keywords, window_days, min_followers, platforms, creators, outside_window_hits}`（`creator_ids` 由 `creators` 派生，多存 `display_name/platforms` 是为了主表不再回读 mock）。
- `tools/builtin/get_creator.py`：`fit_result()` 按「媒体噪音 → 互动数据/合作明细 → 帖子截到 2 → 1 → 只剩 id」逐级缩到 `max_tool_result_chars`，缩过即 `truncated=true` 且保留 `creator_id`。
- 工具需要读写活动记录：新增 `campaign/store.py::CampaignStore`（包装 `session_metadata`），`ApplicationService.campaign()/save_campaign()` 改为委托它；`ToolRegistry(enabled, campaigns, max_result_chars)` 注册 `search_creators`、`get_creator`；`bootstrap.py`、`tests/conftest.py` 同步。`ApplicationService.chat` 在 `runtime.run` 之后重新读活动，避免用回合开始时的旧对象覆盖工具写入。
- `Campaign` 新增 `stage: CREATED|SEARCHING|EVALUATING` 与 `last_search`，与 `goal_status` 分开：目标仍是 `PARSED`，T07 再搜时搜索工具不会被隐藏。`SEARCH_TOOLS`（未 PARSED 时隐藏）扩为 `search_creators`+`get_creator`。
- `max_tool_result_chars` 默认与示例配置从 8000 提到 12000：完整搜索结果约 7.7–8.7K 字符，8000 会把 JSON 截成半截喂给模型。
- `campaign/workbench.py`（新）：`main_table_rows(campaign)`、`search_caption(campaign)`，前端只渲染它的输出。`frontend/app.py` 把主表放进 `st.empty()` 槽，`on_event` 时重画，`running` 时叠 `cp-table-loading` 层（`theme.py`）。T01 的 `test_layout` 里左栏第一个子元素相应改为容器。
- Mock provider：PARSED 后用户说「开始/搜索」→ 调 `search_creators(keywords=["翻译"], window_days=30|文中的 N 天)`；工具返回后直接回显 `display`。`goal.md` 加第 8 条，指导 DeepSeek 何时调用搜索。
- 允许清单之外改动的文件：`campaign/goal.py`（Campaign 字段）、`campaign/store.py`、`campaign/workbench.py`、`application.py`、`settings.py`、`config/config.example.yaml`、`tools/registry.py`、`providers/mock.py`、`config/prompts/goal.md`、`frontend/app.py`、`frontend/theme.py`、`frontend/tests/test_shell.py`、`backend/tests/conftest.py`。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
