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

- 模型输出 3 个对象的 JSON。应用层校验 cited_post_id 与正文不相等。
- `save_draft` 不是模型直接写库；应用层校验通过且 `user_approved=true` 后写入。
- 状态：`SELECTED → DRAFTING → DRAFT_REVIEW`。无 `SENDING` 状态。

## 模块

- `backend/src/collabpilot/campaign/drafts.py`
