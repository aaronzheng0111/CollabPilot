# Plan — 沟通渠道

## 数据模型

SQLite 表 `creator_channels`：`campaign_id`、`creator_id`、`channel`、`confirmed_at`。未确认则无行。

展示用的 `ContactView` 不落库，每次从 `data/mock` 的 `contact` 读取。

## 契约

- `list_contacts(creator_ids)`：`risk_level=read`。合并该创作者 TikTok 与 Instagram 的 `contact`。两边都存在时各返回一行，不合并成一个猜测渠道。
- `confirm_channel(creator_id, channel)`：`risk_level=write`。需要 `user_approved=true`。
- 允许的 `channel`：`tiktok_dm`、`instagram_dm`、`email`。`unknown` 不能作为确认值。

## 状态

`SELECTED` 期间可确认渠道。全部待触达创作者都有 `confirmed_channel` 后，才允许进入 `DRAFTING`。

## 界面

本 Task 提供数据。T11 把 `channel` 放进左表。

## 模块

- `backend/src/collabpilot/campaign/channels.py`
- `backend/src/collabpilot/tools/builtin/confirm_channel.py`
