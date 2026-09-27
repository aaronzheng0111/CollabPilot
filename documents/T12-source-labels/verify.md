# Verify — 来源标注与提交材料

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/integration/test_demo_reset.py`、`tests/unit/test_t12_docs.py`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_source_labels.py`）。用例 9 现场计时与完整 DeepSeek 走查待人工。

| # | 用例 | 结果 |
|---|------|------|
| 1 | demo reset 清空会话与活动相关表，data/mock 不变 | 自动通过：`test_demo_reset_clears_tables_and_leaves_mock_untouched`、`test_cli_demo_reset_invokes_clear` |
| 2 | 达人、帖子、GPM 行有 MOCK | 自动通过：`test_creator_rows_are_tagged_mock` |
| 3 | 判断、策略、草稿、跟进有 LLM 与 deepseek-chat | 自动通过：`test_llm_on_verdict_strategy_drafts_and_follow_up` |
| 4 | 已合作、主题不符锁定、受众改判行有 RULE | 自动通过：`test_rule_on_excluded_lock_and_audience` |
| 5 | 草稿区标明不会发送 | 自动通过：`test_drafts_state_will_not_send` |
| 6 | 界面不出现 API Key | 自动通过：`test_ui_does_not_contain_api_key` |
| 7 | 页面顶部有四类标签图例 | 自动通过：`test_legend_lists_four_labels_on_empty_page` |
| 8 | design-note.md 覆盖六件事与「拿掉模型停在哪」，不超过 900 字 | 自动通过：`test_design_note_covers_six_topics_under_900_chars` |
| 9 | demo-script.md 10 步齐全，含三处专门展示，总时长 180–300 秒 | 自动通过：`test_demo_script_ten_steps_timing_and_highlights`（秒数求和）；人工：待按脚本计时走查 |
| 10 | 演示脚本含无 Key 重跑看到 model_unavailable 的一步 | 自动通过：同上（附录含 `model_unavailable`）；人工：待拔 Key 走查 |
| 11 | two-week-plan.md 3–5 项，每项有可重复的验证方式 | 自动通过：`test_two_week_plan_has_repeatable_checks` |
| 12 | 根 README 快速开始不超过 6 条命令，覆盖 Key、依赖、启动、测试、评测、重置 | 自动通过：`test_readme_quickstart_has_six_commands_and_links` |

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
