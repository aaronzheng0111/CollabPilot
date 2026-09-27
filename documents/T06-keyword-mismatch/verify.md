# Verify — 关键词命中但主题不符

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_topic_match.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_evidence_panel.py`）。评测：`cd backend && uv run pytest -m eval -s tests/eval/test_topic_eval.py`（需要 `backend/.env` 的 `DEEPSEEK_API_KEY`）。

| # | 用例 | 结果 |
|---|------|------|
| 1 | mismatch 且 fit 返回 topic_conflict，不保存 | 自动通过：`test_mismatch_plus_fit_is_topic_conflict_and_not_saved`；`test_unclear_fit_is_topic_conflict` |
| 2 | mismatch 缺主题、证据或 quote 不是帖子原文子串时返回 quote_not_found | 自动通过：`test_mismatch_missing_topic_evidence_or_quote_is_quote_not_found`（空主题、假 quote、>80 字、只有 evidence_id 没有帖子）；合法 quote 见 `test_valid_mismatch_quote_must_be_post_substring` |
| 3 | mismatch 进入 topic_rejected_ids，后续轮次不重判也不推荐 | 自动通过：`test_lock_puts_mismatch_in_topic_rejected_ids`、`test_locked_ids_are_dropped_from_later_search_and_judgment`、`test_evaluate_skips_locked_and_does_not_rejudge` |
| 4 | GPM 高于 target_gpm 仍不在最终候选 | 自动通过：`test_high_gpm_mismatch_stays_out_of_fit`（creator_012 GPM 28.1 > 20；`fit_creator_ids` 源码无 GPM 升级） |
| 5 | backend/src 不读 keyword_mismatch 与 scenario_tags | 自动通过：`test_runtime_source_does_not_read_keyword_mismatch_or_scenario_tags` |
| 6 | eval：011–015 全部 mismatch+unfit，001–006 无 mismatch（附模型原文） | eval 通过（2026-09-27，`deepseek-chat`，1 次）：001–006 全 match+fit rank 1–6；011 影视字幕剪辑 / 012 语言考试 / 013 AI绘画 / 014 留学申请 / 015 语言考试，全部 mismatch+unfit，rejected=[]，锁定 011–015 |
| 7 | 判断与理由标 LLM，锁定动作标 RULE | 自动通过：`test_mismatch_judgment_is_llm_lock_is_rule` |
| 8 | 主表该行为「不合适」并有「主题不符」胶囊 | 自动通过：`test_mismatch_row_and_panel_show_quote_lock_and_no_restore`（`topic` 列为纯文本「主题不符：影视字幕剪辑」，dataframe 无法套胶囊，与 T05 相同）；人工：待走查 |
| 9 | 依据面板显示 quote 与帖子 id，锁定行标 RULE，无加回按钮 | 自动通过：同上（quote「高能剪辑」、`tt_video_011_1`、`[LLM]`、`已锁定，不再推荐` `[RULE]`、无「加回名单」）；人工：待走查 |

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
