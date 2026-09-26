# Plan — 合格不足与再搜

## 数据模型

```text
SearchRound
  index: 1 | 2
  window_days: int
  min_followers: int | null
  keywords: string[]
  fit_count: int
  gap: int
  strategy_reason: str | null
  data_origin: mock_seed | real_model_output
  model_name: str | null

RetryStrategy
  changes: { field, old_value, new_value }[]   # 长度 1 到 3
  reason: str
  data_origin: real_model_output
  model_name: deepseek-chat
```

活动字段 `pending_decision`: `accept_short_list` | null。

## 契约

- 首轮由应用层设定 `window_days=30`，`data_origin=mock_seed`。这不是第二轮策略。
- `accept_retry_strategy(round1, strategy)`：没有 `strategy` 时返回 `model_strategy_required`。
- `changes[].field` 只允许 `window_days`、`min_followers`、`keywords`。新值必须与旧值不同。
- `include_own_brand` 与 `include_keyword_mismatch` 不在允许字段内。出现则 `rule_locked`。
- 代码里不得写死第二轮 `window_days=90` 或任何固定粉丝门槛。单测用注入的策略对象，不调用 DeepSeek。

## 状态

`EVALUATING → INSUFFICIENT → RETRYING → CANDIDATES_READY`

## 模块

- `backend/src/collabpilot/campaign/retry.py`
