# Plan — 合格不足与再搜

## 数据模型

```text
SearchRound
  index: 1 | 2
  keywords: string[]
  window_days: int
  min_followers: int | null
  fit_count: int
  gap: int
  strategy_reason: str | null
  data_origin: mock_seed | real_model_output
  model_name: str | null

RoundSummary              # 请求策略时发给模型
  round: SearchRound
  not_selected: {own_brand_cooperated: int, topic_mismatch: int, pending: int, unfit: int}
  outside_window_hits: int

RetryStrategy
  changes: { field, old_value, new_value }[]   # 长度 1 到 3
  reason: str
  data_origin: real_model_output
  model_name: deepseek-chat
```

活动字段 `pending_decision`: `accept_short_list` | null（与 PLAN.md「待你决定」共用同一字段）。

## 契约

- 首轮参数取 T03 `last_search`：`window_days` 为工具默认 30，`data_origin=mock_seed`。这不是第二轮策略。
- `build_round_summary(campaign) -> RoundSummary`：只用活动内已有数据，不读测试答案字段。
- `accept_retry_strategy(round1, strategy)`：没有 `strategy` 时返回 `model_strategy_required`。
- `changes[].field` 只允许 `window_days`、`min_followers`、`keywords`。新值必须与旧值不同。
- `include_own_brand` 与 `include_keyword_mismatch` 不在允许字段内。出现则 `rule_locked`。
- 第二轮搜索结果先减去 T04 已合作与 T06 `topic_rejected_ids`，再交给模型判断。
- 代码里不得写死第二轮 `window_days=90` 或任何固定粉丝门槛。单测用注入的策略对象，不调用 DeepSeek。

## 状态

`EVALUATING → INSUFFICIENT → RETRYING → CANDIDATES_READY`

## 界面

- `frontend/components/progress_panel.py`：「进度」区块，每轮一行；标题显示中文状态。
- 同文件内「调整了什么」表，来自 `RetryStrategy.changes`。
- `accept_short_list` 在 `pending_decisions.py` 注册一行文案。

## 模块

- `backend/src/collabpilot/campaign/retry.py`
- `backend/src/collabpilot/campaign/decisions.py`（注册 `accept_short_list` 分支）
- `frontend/components/progress_panel.py`、`frontend/components/pending_decisions.py`
