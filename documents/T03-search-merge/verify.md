# Verify — 搜索与跨平台合并

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_mock_store.py`、`tests/unit/test_search_creators.py`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_main_table.py`）。全部走 mock provider，不调用 DeepSeek。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 搜索结果来自两个 mock 文件 | 自动通过：`test_results_come_from_both_files_and_are_mock`、`test_merges_both_files_by_creator_id`（34 位、10 位跨平台） |
| 2 | creator_001 只聚合为一条且含两个平台 | 自动通过：`test_cross_platform_creator_is_one_row_with_two_platforms` |
| 3 | get_creator 返回两边资料且 display_name 一致 | 自动通过：`test_get_creator_returns_both_sides_with_same_display_name` |
| 4 | 单平台创作者的另一侧为 null | 自动通过：`test_single_platform_creator_has_null_other_side`、`test_get_creator_single_platform_and_not_found` |
| 5 | 结果标明 MOCK，且不含四个测试答案字段 | 自动通过：`test_oracle_fields_are_removed_everywhere`、`test_search_payload_has_no_oracle_keys`；`data_origin=mock_seed`，display 带 `[MOCK]` |
| 6 | 目标未解析时 search_creators 返回 goal_not_ready | 自动通过：`test_search_requires_parsed_goal` |
| 7 | 30 天窗口不含 007–009 且 outside_window_hits≥3；90 天窗口包含 | 自动通过：`test_window_30_excludes_007_009_and_counts_them_outside`（关键词「翻译」：30 天 26 位 / outside 3；90 天 29 位 / outside 0） |
| 8 | min_followers 只去掉低于门槛的账号 | 自动通过：`test_min_followers_drops_only_the_account_below_threshold`（creator_003 只剩 instagram） |
| 9 | backend/src 只在剔除列表中出现测试答案字段名 | 自动通过：`test_backend_src_only_names_oracle_fields_in_the_strip_list` |
| 10 | 搜索运行中主表保留旧行并显示加载层 | 自动通过：`test_running_search_keeps_old_rows_and_shows_loading_layer`；人工：待走查 |
| 11 | 搜索成功后主表 M 行、带 MOCK，上方显示搜索参数 | 自动通过：`test_search_success_shows_m_rows_with_mock_and_params`；人工：待走查 |

补充：`test_get_creator_is_truncated_to_limit_keeping_id` 覆盖「截断保留 creator_id 与 truncated=true」；`test_mock_provider_turn_searches_and_fills_the_campaign` 覆盖 PARSED 后一轮对话触发搜索并写入 `last_search`。

DeepSeek 真实路径：待人工用真 Key 走一次「解析目标 → 开始搜索」，在此补记模型选用的 keywords 与人数。

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
