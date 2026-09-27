# Verify — 受众信息缺失

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_audience.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_pending_list.py`、`tests/test_evidence_panel.py`）。本 Task 无 DeepSeek eval。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 受众视图四项都是「未知」，不是 null、0、空数组或不限 | 自动通过：`test_audience_view_unknown_fields_are_the_string_unknown` |
| 2 | 自动 fit 被改成 pending 且 unknowns 含 audience | 自动通过：`test_fit_with_unknown_audience_becomes_pending_with_override` |
| 3 | 未手动接受前不在 fit 名单 | 自动通过：`test_020_to_023_are_not_in_fit_creators_and_overridden_are_pending`（仅 001 留在 `fit_creators`） |
| 4 | MOCK 与 RULE 标记同时可见 | 自动通过：`test_audience_source_labels_are_mock_and_rule`；面板见 `test_evidence_panel_shows_reasons_posts_age_recency_unknowns_and_model` |
| 5 | mock 数据上 020–023 都不在 fit_creators；被改判者带 rule_override | 自动通过：`test_020_to_023_are_not_in_fit_creators_and_overridden_are_pending` |
| 6 | 依据面板受众四项显示「未知」与平台原文 | 自动通过：`test_evidence_panel_shows_reasons_posts_age_recency_unknowns_and_model`（选 020：年龄/性别/地区/兴趣「未知」、`平台未公开受众画像`、`[MOCK]`）；人工：待走查 |
| 7 | 主表该行为「待确认」并有「受众未知」胶囊 | 自动通过：`test_main_table_audience_unknown_row_is_pending_with_badge`（`audience` 列为纯文本「受众未知」，dataframe 无法套胶囊）；人工：待走查 |
| 8 | 次级区「待确认」列表与 fit 名单分开，每行有原因 | 自动通过：`test_pending_list_is_separate_and_states_reason`（`creator_020`「受众未知」、另有「相关内容只有 1 条」，主表前三行仍为「合适」）；人工：待走查 |

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
