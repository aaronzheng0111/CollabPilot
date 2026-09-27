# Verify — 保存名单与去重

自动化：`cd backend && uv run pytest`（`tests/unit/test_selection.py`、`tests/integration/test_campaign_store.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_selection.py`）。本 Task 无 DeepSeek eval。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 未确认保存返回 approval_required | 自动通过：`test_unapproved_save_returns_approval_required` |
| 2 | 确认后 saved_creator_ids 与入参一致且状态 SELECTED | 自动通过：`test_approved_save_writes_ids_and_selected_stage` |
| 3 | 重复保存不产生第二条 | 自动通过：`test_duplicate_save_keeps_one_and_mentions_already` |
| 4 | 已排除创作者不再出现在推荐 | 自动通过：`test_search_skips_excluded`、`test_recommend_drops_saved_excluded_and_topic_rejected` |
| 5 | 重启进程后 saved、excluded、topic_rejected 仍在 | 自动通过：`test_campaign_lists_survive_reopen` |
| 6 | 未确认的排除被拒绝；确认后从 saved 移到 excluded | 自动通过：`test_unapproved_exclude_rejected_then_approved_moves` |
| 7 | 同一需求再次运行沿用 campaign_id，并跳过三类创作者 | 自动通过：`test_same_goal_reuses_campaign_id_and_skips_three_classes` |
| 8 | 接受的 pending 进入 saved 但 decision 仍为 pending | 自动通过：`test_pending_accepted_stays_pending` |
| 9 | 主表勾选列：fit 默认勾选，pending 可勾选，unfit 与锁定行禁用 | 自动通过：`test_selection_column_defaults_and_locked_rows_unselectable`（`can_select`；AppTest 无 data_editor，读 workbench 行）；人工：待走查 |
| 10 | 「待你决定」出现保存一行，批准后主表有 saved 列 | 自动通过：`test_save_button_queues_pending_row_and_saved_column_after_approve`；人工：待走查 |
| 11 | 再次运行时主表上方显示跳过人数 | 自动通过：`test_skip_counts_caption_after_saved_and_excluded`；人工：待走查 |

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
