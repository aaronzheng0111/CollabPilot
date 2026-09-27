# Verify — 触达草稿

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/unit/test_drafts.py`，默认 `-m 'not eval'`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_draft_cards.py`）。评测：`cd backend && uv run pytest -m eval -s tests/eval/test_drafts_eval.py`（需要 `backend/.env` 的 `DEEPSEEK_API_KEY`）。

| # | 用例 | 结果 |
|---|------|------|
| 1 | 少于 3 人时 need_three_creators | 自动通过：`test_fewer_than_three_saved_is_need_three_creators`、`test_need_three_does_not_call_model` |
| 2 | 成功时 3 条 pending_review 且带来源字段 | 自动通过：`test_approved_save_writes_three_pending_review_and_has_no_send` |
| 3 | 三封 body 互不相同，cited_post_id 互不相同 | 自动通过：同上；`test_bodies_and_cited_posts_must_be_unique` |
| 4 | cited_post_id 不属于该创作者则整批不保存 | 自动通过：`test_cited_post_not_on_creator_drops_batch` |
| 5 | 无发送实现，状态停在 DRAFT_REVIEW | 自动通过：`test_approved_save_writes_three_pending_review_and_has_no_send`（无 smtp/send_mail/SENDING） |
| 6 | 未确认时 approval_required | 自动通过：`test_unapproved_save_is_rejected` |
| 7 | 未确认渠道时返回 channel_unconfirmed 且不调用模型 | 自动通过：`test_unconfirmed_channel_does_not_call_model` |
| 8 | 三种渠道的正文名称正确；不一致时 channel_mismatch | 自动通过：`test_channel_mismatch_and_labels` |
| 9 | 正文含所引帖子不少于 8 字的原文片段，否则 quote_not_found | 自动通过：`test_quote_not_found_drops_batch` |
| 10 | eval：001–003 的草稿通过用例 3、4、8、9（附三封原文） | eval 通过（2026-09-27，`deepseek-chat`，1 次）：001 TikTok 私信引 `tt_video_001_1`「用LinguaGo实时对话翻译和日本供应商开视频会，全程没卡壳」；002 Instagram 私信引 `ig_media_002_2`「跨境选品周报｜本周用LinguaGo翻了40份供应商报价」；003 邮件引 `tt_video_003_1`「外企周报中译英，LinguaGo保留了原来的表格格式」。三封 body 互异 |
| 11 | 草稿卡片展示创作者、渠道、被引用原文、正文、「待审核」，带 LLM | 自动通过：`test_draft_cards_show_creator_channel_quote_body_pending_and_llm`；人工：待走查 |
| 12 | 「待你决定」先有保存草稿，再有逐封审核；批准后显示「已批准」 | 自动通过：`test_pending_save_then_per_draft_review_and_approve`；人工：待走查 |
| 13 | 草稿区无发送类按钮，有「草稿不会发送」 | 自动通过：`test_draft_area_has_no_send_buttons_and_states_will_not_send`；人工：待走查 |

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
