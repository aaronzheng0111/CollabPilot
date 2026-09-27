# Plan — 保存名单与去重

## 数据模型

SQLite 新表 `campaigns`：

```text
id, session_id, goal_fingerprint, status, parsed_goal_json, pending_decision_json,
saved_ids_json, excluded_ids_json, topic_rejected_ids_json, accepted_from_pending_json, updated_at
```

文件位置沿用 backend 的 `database_url`（`backend/data/agent.db`），不写入 `data/mock/`。T02–T07 暂存在会话 metadata 的活动字段，本 Task 迁入此表，字段名不变。

`goal_fingerprint`：对 `ParsedGoal` 的品牌、人数、平台、筛选与排除条件做规范化后取哈希。同一 session 内指纹相同视为同一任务。

## 契约

- `save_campaign_selection(creator_ids)`：`risk_level=write`。仅当本轮用户消息包含明确确认短语或界面传入 `user_approved=true` 时执行。
- `exclude_creator(creator_id)`：同样 `risk_level=write`，同样需要 `user_approved=true`。
- `recommend(candidates, campaign)` 在返回前减去 saved、excluded、topic_rejected，并返回三类各自的人数。
- 在 `decisions.py` 注册 `save_selection` 与 `exclude_creator` 两个分支。

## 状态

`CANDIDATES_READY → USER_REVIEW → SELECTED`

## 界面

- 主表「选中」列用 `st.data_editor` 的勾选列；不可勾选行禁用。
- 主表下方「保存到活动」按钮用 `button-secondary`；它只创建待决定事项，真正批准在「待你决定」里用珊瑚色按钮。
- 主表上方的跳过人数说明用 `caption` 样式。

## 模块

- `backend/src/collabpilot/infrastructure/campaign_store.py`
- `backend/src/collabpilot/tools/builtin/save_campaign_selection.py`
- `backend/src/collabpilot/tools/builtin/exclude_creator.py`
- `backend/src/collabpilot/campaign/decisions.py`
- `frontend/components/main_table.py`、`frontend/components/pending_decisions.py`
