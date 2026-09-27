# Verify — 工作台集成与视觉验收

全部用例通过才算本 Task `verified`。

自动化：`cd backend && uv run pytest`（`tests/integration/test_workbench_state.py`）；`cd frontend && uv run --project ../backend --extra ui --extra dev pytest tests`（`tests/test_workbench.py`、`tests/test_theme_tokens.py`）。用例 20 截图见 `screenshots/`。用例 21 待人工走查。

| # | 用例 | 结果 |
|---|------|------|
| 1 | get_workbench_state 一次返回全部只读数据，不写库 | 自动通过：`test_get_workbench_state_returns_all_fields_and_does_not_write` |
| 2 | 左栏是数据表，右栏是状态栏、对话历史和输入框 | 自动通过：`test_layout_is_left_table_right_status_history_input`；`test_shell.test_layout_is_three_to_two_with_status_history_input` |
| 3 | 左栏区块顺序固定，无数据区块不渲染，「待你决定」始终渲染 | 自动通过：`test_secondary_order_and_pending_always_present` |
| 4 | search_creators 开始时状态栏与左表都出现该工具名的加载 | 自动通过：`test_running_search_shows_tool_name_on_status_and_table` |
| 5 | 成功返回 M 个创作者后主表行数为 M，列含 creator_id、display_name、platforms | 自动通过：`test_main_table.test_search_success_shows_m_rows_with_mock_and_params` |
| 6 | 硬过滤成功后主表只剩 kept | 自动通过：判断后主表来自 kept（`test_evidence_panel.test_main_table_shows_decision_and_rank_in_order_with_llm`） |
| 7 | fit 按 rank 升序排在 pending 与 unfit 之前 | 自动通过：同上 |
| 8 | 主表有 channel，跟进区有 next_step 与 follow_status | 自动通过：`test_channel_and_follow_up_visible_together` |
| 9 | CLARIFYING 时左表只有固定空态文案，右栏有追问 | 自动通过：`test_clarifying_hides_creator_rows` |
| 10 | 待接受人数时草稿区为空 | 自动通过：`test_accept_short_list_has_no_drafts` |
| 11 | 三封草稿为待审核且无发送按钮 | 自动通过：`test_three_pending_drafts_have_no_send_button` |
| 12 | 同一 session 重开后右栏仍显示历史 | 自动通过：`test_reopened_session_keeps_history` |
| 13 | 工具失败时状态栏为 failed，主表保持上一次成功行 | 自动通过：`test_failed_tool_keeps_rows_and_shows_error_code` |
| 14 | config.toml 与 theme.py 的色值都在 DESIGN.md colors 中 | 自动通过：`test_config_and_theme_hex_are_in_design_colors` |
| 15 | 页面底色 canvas，卡片 surface-card，无纯白背景 | 自动通过：`test_canvas_card_and_no_white_background` |
| 16 | 标题衬线字重 400，正文无衬线，id 等宽 | 自动通过：`test_fonts_serif_sans_mono` |
| 17 | 珊瑚色只用于批准按钮、勾选框、聚焦环 | 自动通过：`test_coral_only_on_approve_checkbox_and_focus` |
| 18 | 状态栏与依据面板为深色，状态圆点颜色正确 | 自动通过：`test_status_and_evidence_are_dark_with_status_dots` |
| 19 | 四类来源标签为胶囊且可互相区分 | 自动通过：`test_source_pills_are_distinct_capsules` |
| 20 | 1440×900 与 1024×768 两栏完整、无横向滚动 | 截图：`screenshots/20-viewport-1440x900.png`、`20-viewport-1024x768.png`（Playwright 量 `scrollWidth==clientWidth`）；人工：待走查确认无横向滚动 |
| 21 | 完整走查 10 步截图齐全 | 待人工走查（DeepSeek Key，见文末合并清单） |

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
