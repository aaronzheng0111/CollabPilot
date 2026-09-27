# Plan — 跟进合作

## 数据模型

SQLite 表 `follow_ups`，字段与 `FollowUp` 相同。一个 `draft_id` 最多一条跟进。

## 契约

- 模型输出 `FollowUp` 草案 JSON。应用层 `validate_follow_up` 核对 `draft.status=approved` 且 `channel` 等于 `confirmed_channel`。
- `save_follow_up`：`risk_level=write`，需要 `user_approved=true`。初始状态 `waiting_user`。
- `note_follow_up(id)`：仅把状态改为 `noted`。需要 `user_approved=true`。

## 状态

`DRAFT_REVIEW` 中某草稿变为 `approved` 后可创建跟进。活动状态增加 `FOLLOW_UP`，从 `DRAFT_REVIEW` 进入。没有 `SENDING`。

## 界面

- `frontend/components/follow_up_table.py`：次级区「跟进」表，展示 `next_step`、`channel`、`follow_status` 的中文。
- 在 `decisions.py` 注册 `save_follow_up` 与 `note_follow_up` 分支；`pending_decisions.py` 注册文案。

## 模块

- `backend/src/collabpilot/campaign/follow_up.py`
- `backend/src/collabpilot/campaign/decisions.py`
- `frontend/components/follow_up_table.py`、`frontend/components/pending_decisions.py`
