# Plan — 保存名单与去重

## 数据模型

SQLite 新表 `campaigns`：

```text
id, session_id, status, parsed_goal_json, saved_ids_json, excluded_ids_json, updated_at
```

文件位置沿用 backend 的 `database_url`（`backend/data/agent.db`），不写入 `data/mock/`。

## 契约

- `save_campaign_selection(creator_ids)`：`risk_level=write`。仅当本轮用户消息包含明确确认短语或界面传入 `user_approved=true` 时执行。
- `exclude_creator(creator_id)`：同样 `risk_level=write`，同样需要 `user_approved=true`。
- 推荐函数 `recommend(candidates, excluded_ids)` 在返回前减去 excluded。

## 状态

`CANDIDATES_READY → USER_REVIEW → SELECTED`

## 模块

- `backend/src/collabpilot/infrastructure/campaign_store.py`
- `backend/src/collabpilot/tools/builtin/save_campaign_selection.py`
- `backend/src/collabpilot/tools/builtin/exclude_creator.py`
