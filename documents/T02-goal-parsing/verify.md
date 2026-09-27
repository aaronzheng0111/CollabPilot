# Verify — 理解合作目标

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_parsed_goal.py`、`tests/unit/test_decisions.py`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_goal_card.py`）。模型回复全部用固定 fixture 或 mock provider，不调用 DeepSeek。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 示例原文解析出 10、3、需要审核、排除已合作 | 自动通过：`test_sample_payload_parses_counts_approval_and_exclusion`、`test_sample_text_turn_reaches_parsed_and_records_model` |
| 2 | 缺品牌时假设为 LinguaGo AI 翻译并可见 | 自动通过：`test_missing_brand_becomes_linguago_assumption`；回复正文含该假设 |
| 3 | 缺人数时 CLARIFYING 且不搜索 | 自动通过：`test_missing_count_is_clarifying_and_never_searches[target_count]`（模型看不到 `search_creators`，工具调用 0） |
| 4 | 缺触达人数时 CLARIFYING，不搜索也不生成草稿 | 自动通过：`test_missing_count_is_clarifying_and_never_searches[outreach_count]` |
| 5 | 缺平台时作为假设而不是追问 | 自动通过：`test_missing_platforms_is_assumed_not_asked` |
| 6 | 非法 JSON 不写入 parsed_goal | 自动通过：`test_invalid_payload_returns_failed_field_names`、`test_invalid_json_is_retried_once_then_not_written` |
| 7 | 「帮我找达人」进入 CLARIFYING，至少 2 个点名问题，且不搜索 | 自动通过：`test_vague_request_with_mock_provider_gets_numbered_questions` |
| 8 | 同一次回复含「推荐过滤」或「换一种说法」 | 自动通过：同上 + `test_template_grill_names_every_missing_field_and_has_both_blocks` |
| 9 | 第 3 轮仍缺关键字段时列出假设，pending_decision=confirm_assumptions | 自动通过：`test_third_round_lists_assumptions_and_sets_pending_decision`、`test_approved_confirm_assumptions_fills_fallbacks_and_parses` |
| 10 | 补齐关键字段后状态变为 PARSED | 自动通过：`test_completing_critical_fields_next_turn_becomes_parsed` |
| 11 | 合作目标卡片逐项展示，假设字段带「假设」与 reason，带 LLM 标签 | 自动通过：`test_goal_card_lists_fields_with_assumption_pills_and_llm_tag`；人工：待走查 |
| 12 | CLARIFYING 时主表只有固定空态文案，右栏有编号追问 | 自动通过：`test_clarifying_shows_fixed_text_and_numbered_questions`；人工：待走查 |
| 13 | 「待你决定」出现确认假设一行，批准后消失；无事项时显示固定文案 | 自动通过：`test_pending_decision_row_approves_and_disappears`、`test_reject_keeps_pending_row`；人工：待走查 |

DeepSeek 真实路径（用例 1、7 用真 Key 各跑一次）：待人工确认后在此补记实际输出。

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
