# Verify — 硬过滤

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_hard_filter.py`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_excluded_table.py`）。规则不调用模型；端到端走 mock provider。

| # | 用例 | 结果 |
|---|------|------|
| 1 | is_current_brand 排除创作者的全部平台 | 自动通过：`test_own_brand_cooperation_removes_every_platform_of_the_creator`（evidence=LinguaGo AI 翻译 / 2026-06-08） |
| 2 | 规则不读 scenario_tags；mock 数据上已合作排除集合恰为 016–019 | 自动通过：`test_mock_data_own_brand_set_is_exactly_016_to_019_without_reading_tags`（与 `load_oracle()` 对照，模块源码不含 `scenario_tags`） |
| 3 | 平台不在目标列表则 platform_mismatch | 自动通过：`test_instagram_only_creator_is_platform_mismatch_when_target_is_tiktok`、`test_tool_uses_goal_platforms_for_mismatch` |
| 4 | 未合作的跨平台创作者保留两个账号 | 自动通过：`test_cross_platform_uncooperated_creator_keeps_both_accounts` |
| 5 | 结果标记为 RULE | 自动通过：`test_tool_marks_rule_and_records_last_filter`（display 以 `[RULE]` 开头，`data_origin=rule`） |
| 6 | 工具 API 不暴露放宽参数；偏好读自合作目标 | 自动通过：`test_tool_schema_has_no_relax_parameter_preference_comes_from_goal`；允许再联系时保留已合作：`test_allow_recontact_keeps_own_brand_collaborators`、`test_tool_keeps_own_brand_when_goal_allows_recontact`；默认仍排除：`test_tool_excludes_own_brand_on_default_goal` |
| 7 | 主表行集合等于 kept | 自动通过：`test_main_table_rows_equal_kept_with_filter_column`（22 行，`filter=kept`）；人工：待走查 |
| 8 | 「已排除」表含原因、合作品牌与日期，带 RULE | 自动通过：`test_excluded_table_is_collapsed_with_reason_brand_date_and_rule`（标题「已排除 4 位」，默认折叠）；人工：待走查 |

补充：`test_own_brand_is_checked_before_platform_and_only_first_reason_recorded`、`test_tool_rejects_ids_outside_the_search_and_requires_search`（`not_in_search` / `search_required`）、`test_mock_provider_chains_search_then_filter`。

DeepSeek 真实路径：待人工用真 Key 确认模型在搜索后自动调用 `apply_hard_filters`，并在回复里列出 016–019。

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
