# Verify — 合格不足与再搜

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_retry.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_progress_panel.py`）。评测：`cd backend && uv run pytest -m eval -s tests/eval/test_retry_eval.py`（需要 `backend/.env` 的 `DEEPSEEK_API_KEY`）。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 首轮不足时展示合格 n/10 与缺口 | 自动通过：`test_first_round_insufficient_shows_qualified_and_gap`（合格 2/10、缺口 8）；`test_chat_without_strategy_does_not_open_round_two`（合格 1/10、缺口 9） |
| 2 | 没有模型策略时返回 model_strategy_required，且不改写窗口 | 自动通过：`test_missing_strategy_is_model_strategy_required_and_does_not_change_window`；`test_chat_without_strategy_does_not_open_round_two`（窗口仍 30，`auto_retries=0`） |
| 3 | 第二轮名单不含已合作和 topic_rejected_ids | 自动通过：`test_injected_window_90_adds_007_009_excludes_011_019`；`test_valid_strategy_runs_second_round_once_then_asks_to_accept` |
| 4 | 仍不足时等待用户决定且不写草稿 | 自动通过：`test_still_short_sets_accept_short_list_and_reject_does_not_promote`；`test_valid_strategy_runs_second_round_once_then_asks_to_accept`（`accept_short_list`，`drafts` 空） |
| 5 | 用户拒绝后不把 unfit 改成 fit | 自动通过：`test_still_short_sets_accept_short_list_and_reject_does_not_promote` |
| 6 | 自动再搜只有 1 次 | 自动通过：`test_auto_retry_budget_is_one`（`MAX_AUTO_RETRIES=1`，源码无 `window_days=90`）；`test_valid_strategy_runs_second_round_once_then_asks_to_accept` |
| 7 | 合法 RetryStrategy 被执行，回复含旧值、新值和 reason，并标 deepseek-chat | 自动通过：`test_valid_strategy_returns_params_with_old_new_reason`；`test_valid_strategy_runs_second_round_once_then_asks_to_accept`（30→90，「窗口外仍有相关帖子」，`[LLM]` `deepseek-chat`） |
| 8 | 放宽已合作或关键词排除时返回 rule_locked | 自动通过：`test_locked_fields_return_rule_locked` |
| 9 | 发给模型的首轮摘要含参数、人数、未入选原因汇总与 outside_window_hits，不含测试答案字段 | 自动通过：`test_round_summary_has_counts_outside_window_and_no_oracle` |
| 10 | 注入 window_days 30→90 后新增 007–009，且不含 011–019 | 自动通过：`test_injected_window_90_adds_007_009_excludes_011_019` |
| 11 | eval：模型策略通过校验，第二轮合格人数大于首轮（附策略原文与两轮人数） | eval 通过（2026-09-27，`deepseek-chat`，1 次）：首轮 fit=6（001–006）；策略 `window_days` 30→90，`keywords` `['翻译']`→`['翻译','本地化','字幕翻译']`；第二轮 fit=8（001–004、006–009），缺口 2。005 未进第二轮 fit |
| 12 | 进度区每轮一行，标题显示中文状态 | 自动通过：`test_progress_panel_lists_each_round_and_chinese_stage`（「候选已就绪」，轮次 1/2，窗口 30/90）；人工：待走查 |
| 13 | 「调整了什么」表含字段、旧值、新值、理由，带 LLM 与 deepseek-chat | 自动通过：`test_changes_table_has_old_new_reason_llm_and_model`；人工：待走查 |
| 14 | 「待你决定」出现是否接受当前人数，草稿表为空 | 自动通过：`test_accept_short_list_row_and_empty_drafts`；人工：待走查 |

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
