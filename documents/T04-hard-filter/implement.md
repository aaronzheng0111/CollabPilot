# Implement — 硬过滤

状态：`in_progress`（自动化用例 1–8 已通过，等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T03。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/hard_filter.py`
- `backend/src/collabpilot/tools/builtin/apply_hard_filters.py`
- `backend/tests/unit/test_hard_filter.py`
- `frontend/components/main_table.py`、`frontend/components/excluded_table.py`（新）
- `frontend/tests/test_excluded_table.py`（新）


## 本 Task 补充约束

函数签名不得包含 relax_own_brand 或同等开关。

## 实现记录

- `campaign/hard_filter.py`：纯函数 `hard_filter(merged, platforms) -> (kept, removed)`。先 `own_brand_cooperated`（任一平台 `cooperation_history[].is_current_brand=true`，附 `evidence{cooperation_id, brand_name, content_published_at, platform}`），再 `platform_mismatch`；一人只记第一个原因。`REASON_LABELS` 给界面中文；`RULE_ORIGIN="rule"`、`RULE_LABEL="[RULE]"`。签名只有两个参数，单测用 `inspect.signature` 锁定。
- `tools/builtin/apply_hard_filters.py`：`creator_ids` 必须来自 `last_search`（否则 `not_in_search` 并列出越界 id）；省略即处理全部搜索结果（减轻模型回传 30 个 id 的负担）。没有搜索记录返回 `search_required`。成功后写 `stage=EVALUATING`、`last_filter{kept, removed}`，`display` 以 `[RULE]` 开头，`data.data_origin="rule"`。目标 `platforms` 取 `parsed_goal.platforms`。
- `Campaign.last_filter: FilterRecord`（`goal.py`），`ToolRegistry`/`settings`/`config.example.yaml` 注册 `apply_hard_filters`，`SEARCH_TOOLS` 同步扩充（未 PARSED 时隐藏）。
- `campaign/workbench.py`：`main_table_rows` 在有 `last_filter` 时改为 `kept` 行（列加 `filter=kept`，来源 `[MOCK] [RULE]`）；新增 `excluded_rows`（原因中文、合作品牌、合作日期、`[RULE]`）。
- `frontend/components/excluded_table.py`：`st.expander("已排除 N 位", expanded=False)` 内一张 dataframe；`app.py` 在「待你决定」下方渲染。
- Mock provider：`search_creators` 成功后接着调 `apply_hard_filters({})`，最终回复拼接本轮所有工具的 `display`。`goal.md` 加第 9 条，让 DeepSeek 搜索后立刻调规则过滤。
- 允许清单之外改动的文件：`campaign/goal.py`、`campaign/workbench.py`、`tools/registry.py`、`settings.py`、`config/config.example.yaml`、`application.py`（`SEARCH_TOOLS`）、`providers/mock.py`、`config/prompts/goal.md`、`frontend/app.py`、`backend/tests/unit/test_search_creators.py` 与 `frontend/tests/test_main_table.py`（适配 mock 链式调用）。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
