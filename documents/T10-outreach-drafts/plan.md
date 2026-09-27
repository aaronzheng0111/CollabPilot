# Plan — 触达草稿

## 数据模型

```text
Draft
  id: str
  campaign_id: str
  creator_id: str
  body: str
  cited_post_id: str
  channel: tiktok_dm | instagram_dm | email
  status: pending_review | approved | rejected
  data_origin: real_model_output
  model_name: str
```

表 `drafts` 存在同一 SQLite。

## 契约

- 模型输出 3 个对象的 JSON。应用层 `validate_drafts` 校验：cited_post_id 属于该创作者且三者互异、正文互异、正文含所引帖子不少于 8 字的原文片段、渠道名称来自 `channels.CHANNEL_LABELS`。
- 提示词给模型的每位创作者材料：`display_name`、已确认渠道、全部 `recent_posts` 原文与 `age_days`、T05 的 `reasons`。要求每封点出该创作者一条具体内容，不写通用模板句。
- 写草稿的模型调用传 `temperature=settings.model.creative_temperature`（默认 `0.85`）；工具编排与适合度判断仍用 `settings.model.temperature`（默认 `0.2`）。
- 校验通过后先写 `pending_decision=save_drafts`；`save_draft` 不是模型直接写库，`user_approved=true` 后才写入。
- `approve_draft(draft_id)` 与 `reject_draft(draft_id)`：需要 `user_approved=true`，只改状态。
- 在 `decisions.py` 注册 `save_drafts` 与 `approve_draft` 分支。
- 状态：`SELECTED → DRAFTING → DRAFT_REVIEW`。无 `SENDING` 状态。

## 界面

- `frontend/components/draft_cards.py`：每封一张 `feature-card`（`surface-card` 底色、`rounded.lg`）；被引用帖子原文用引用样式；状态用 `badge-pill`。
- 区块底部固定一行 `caption`：「草稿不会发送 [MOCK-SEND]」。

## 模块

- `backend/src/collabpilot/campaign/drafts.py`
- `backend/src/collabpilot/campaign/decisions.py`
- `frontend/components/draft_cards.py`、`frontend/components/pending_decisions.py`
