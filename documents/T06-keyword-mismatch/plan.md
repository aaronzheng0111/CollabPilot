# Plan — 关键词命中但主题不符

## 契约

`reject_keyword_mismatches(creator_ids) -> removed[]`

若 `scenario_tags` 含 `keyword_mismatch`，reason=`keyword_mismatch`，并附 `source_post_id`（取 `recent_posts[0]` 的 `video_id` 或 `id`）。

此函数在 `apply_hard_filters` 之后、写入最终名单之前调用。无开关可关闭。

## 状态

仍为 `EVALUATING`。

## 模块

- `backend/src/starter_agent/campaign/keyword_mismatch.py`
