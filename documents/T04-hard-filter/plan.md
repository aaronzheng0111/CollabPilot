# Plan — 硬过滤

## 契约

`apply_hard_filters`：`risk_level=read`。输入 id 必须来自当前活动最近一次 `search_creators` 的返回集。不在该集合中的 id 返回 `error_code=not_in_search`。

判定顺序：先 `own_brand_cooperated`，再 `platform_mismatch`。同一创作者只记录第一个命中的 reason。

## 状态

`SEARCHING → EVALUATING`（过滤完成后）。

## 数据

不新增表。活动上记录 `last_filter: {{kept, removed}}`。

## 模块

- `backend/src/starter_agent/campaign/hard_filter.py`
- `backend/src/starter_agent/tools/builtin/apply_hard_filters.py`
