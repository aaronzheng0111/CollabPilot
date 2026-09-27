# Plan — 硬过滤

## 契约

`apply_hard_filters`：`risk_level=read`。输入 id 必须来自当前活动最近一次 `search_creators` 的返回集。不在该集合中的 id 返回 `error_code=not_in_search`。

判定顺序：先 `own_brand_cooperated`，再 `platform_mismatch`。同一创作者只记录第一个命中的 reason。

`own_brand_cooperated` 只看 `cooperation_history[].is_current_brand`。`removed` 每项附 `evidence: {cooperation_id, brand_name, content_published_at}`，供界面展示依据。

## 状态

`SEARCHING → EVALUATING`（过滤完成后）。

## 数据

不新增表。活动上记录 `last_filter: {{kept, removed}}`。

## 界面

- 主表按 `kept` 替换行。
- `frontend/components/excluded_table.py`：次级区「已排除」折叠表，默认折叠，标题显示人数，例如「已排除 4 位」。

## 模块

- `backend/src/collabpilot/campaign/hard_filter.py`
- `backend/src/collabpilot/tools/builtin/apply_hard_filters.py`
- `frontend/components/excluded_table.py`
