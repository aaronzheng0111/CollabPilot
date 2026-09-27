# Verify — 匹配判断

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_verdict.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_evidence_panel.py`）。评测：`cd backend && uv run pytest -m eval -s`（需要 `backend/.env` 的 `DEEPSEEK_API_KEY`）。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 证据 id 不在帖子或 evidence 中则拒绝保存 | 自动通过：`test_unknown_evidence_id_rejects_only_that_verdict`（别人的帖子 id 也拒绝）、`test_evidence_ids_may_point_at_product_usage_evidence` |
| 2 | 提示词与工具结果不含测试答案字段，界面不展示 expected_decision_hint | 自动通过：`test_prompt_and_candidates_have_no_oracle_fields`；前端 `test_evidence_panel_shows_...` 断言页面无 `expected_decision_hint` |
| 3 | GPM 未知时 unknowns 含 gpm 且不出现编造数字 | 自动通过：`test_unknown_gpm_is_added_to_unknowns_and_payload_has_no_number`（creator_020 payload 里 `gpm=null`、`gpm_origin=unknown`）；eval 中 020–023、034 的 unknowns 均含 `gpm` |
| 4 | 保存结果含 real_model_output 与 deepseek-chat | 自动通过：`test_accepted_verdicts_carry_real_model_output_and_model_name`、`test_chat_turn_searches_filters_and_persists_validated_verdicts` |
| 5 | 无证据的 fit 返回 evidence_required | 自动通过：`test_fit_without_evidence_or_related_posts_is_evidence_required` |
| 6 | fit 的 rank 必须是从 1 开始且不重复，否则 rank_invalid | 自动通过：`test_three_fits_need_ranks_one_two_three`、`test_bad_fit_ranks_drop_the_whole_batch`（重复 / 从 0 起 / 缺 rank / 不连续，整批丢弃） |
| 7 | unfit 与 pending 的 rank 必须为 null | 自动通过：`test_non_fit_rank_must_be_null` |
| 8 | 展示顺序为 fit 的 rank 升序，然后 pending，然后 unfit | 自动通过：`test_sort_is_fit_rank_then_pending_then_unfit`（并锁定 `sort_verdicts` 源码不含 follower/gpm/keyword） |
| 9 | 提示词中每条帖子带 age_days，并写明排序原则与 exclusion_rules | 自动通过：`test_prompt_states_recency_priority_exclusion_rules_and_age_days` |
| 10 | fit 的 related_post_ids 非空且属于该创作者；recency 由应用层计算 | 自动通过：`test_fit_related_posts_must_belong_to_the_creator_and_drive_recency`（creator_001 六条帖子 → `recent_related_count=6`；creator_007 → 0） |
| 11 | 模型不可用时无 Verdict、回复 model_unavailable、无备用排序 | 自动通过：`test_provider_failure_becomes_model_unavailable_without_fallback`（`verdicts=None`、stage 仍 `EVALUATING`、事件 `tool.completed ok=False error_code=model_unavailable`） |
| 12 | eval：001–006 全为 fit；011–015 无 fit（附模型原始输出） | eval 通过（2026-09-27，`deepseek-chat`，连续 2 次）：fit = 001(1)、002(2)、003(3)、004(4)、005(5)、006(6)；011 unfit/mismatch「影视字幕剪辑内容」；010、028、031、032 unfit（近期竞品合作）；030 unfit（无本品证据）；020–023 pending 且 unknowns=[audience, gpm]；024、025、026、034 pending「仅 1 条 LinguaGo」；029、033 pending；rejected=[]。首次运行 005 被判 unfit（evidence.product_name 标为竞品），只改 `campaign.md` 后通过，见 implement.md |
| 13 | 主表显示 decision 中文与 rank，顺序正确，带 LLM | 自动通过：`test_main_table_shows_decision_and_rank_in_order_with_llm`；人工：待走查 |
| 14 | 判断依据面板展示理由、帖子原文、age_days、recency、未知项与 deepseek-chat | 自动通过：`test_evidence_panel_shows_reasons_posts_age_recency_unknowns_and_model`（切到 creator_020 显示「未知：gpm」「未知：audience」）；人工：待走查 |

补充：`test_invalid_batch_is_retried_once_then_left_empty`（rank_invalid → 纠错重试一次 → 仍失败则 `verdict_error=verdicts_invalid`）、`test_evaluation_only_runs_once_per_filter`、`test_mock_provider_runs_full_chain_with_pending_verdicts`。

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
