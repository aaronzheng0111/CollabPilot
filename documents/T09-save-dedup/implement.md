# Implement — 保存名单与去重

状态：`in_progress`（自动化用例 1–11 已通过；本 Task 无 eval；等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T08。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/infrastructure/campaign_store.py`
- `backend/src/collabpilot/tools/builtin/save_campaign_selection.py`
- `backend/src/collabpilot/tools/builtin/exclude_creator.py`
- `backend/tests/integration/test_campaign_store.py`
- `backend/src/collabpilot/campaign/decisions.py`
- `frontend/components/main_table.py`、`frontend/components/pending_decisions.py`
- `frontend/tests/test_selection.py`（新）


## 本 Task 补充约束

write 工具默认不在 `allow_risk_levels` 时，为本工具单独放开 write，但仍要应用层批准标志。不要放开 dangerous。


## 实现记录

- `infrastructure/campaign_store.py`：SQLite `campaigns` 表（含 `record_json` 全量快照）；`CampaignStore.get/save` 按 `session_id` 读写；旧 `session_metadata.campaign` 首次读取时迁入。`campaign/store.py` 改为再导出。
- `campaign/selection.py`：`fingerprint_goal`（品牌/人数/平台/筛选与排除规范化后哈希）、`recommend` 减去 saved/excluded/topic_rejected 并计三类人数、`apply_save_selection`/`apply_exclude_creator`。pending 进 saved 时写 `accepted_from_pending`，不改 `decision`。
- 写工具 `save_campaign_selection` / `exclude_creator`：`risk_level=write`，`ToolPolicy.WRITE_TOOLS` 单独放开，未 `user_approved` 时 `approval_required` 且名单不变，只排队 `pending_decision`。`decisions.py` 注册 `save_selection` / `exclude_creator`。阶段 `CANDIDATES_READY → USER_REVIEW → SELECTED`。
- `search_creators` 调用 `recommend`；回复含跳过人数与「已在名单中」；其他活动已保存的 id 只加一句提示。
- 前端：判断后主表 `data_editor`「选中」列（fit 默认勾、pending 可勾、unfit/锁定 `can_select=false`）；`保存到活动` secondary 只排队；批准后 `saved` 列。主表上方 caption 读 `skip_counts`。Streamlit AppTest 无 `data_editor`，勾选列断言走 `workbench.main_table_rows`。

允许清单之外改动的文件：`campaign/selection.py`、`campaign/goal.py`（字段与阶段）、`campaign/store.py`、`application.py`、`campaign/workbench.py`、`tools/policy.py`、`tools/registry.py`、`tools/base.py`、`settings.py`、`config/config.example.yaml`、`tools/builtin/search_creators.py`、`campaign/retry.py`、`frontend/app.py`、`frontend/tests/test_evidence_panel.py`、`frontend/tests/test_pending_list.py`、`backend/tests/unit/test_selection.py`、`backend/tests/unit/test_decisions.py`。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
