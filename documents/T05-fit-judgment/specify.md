# Specify — 匹配判断

## 用户故事

对硬过滤后的创作者，DeepSeek 阅读帖子与合作记录，给出适合、不适合或待确认，指出证据 id，并对适合的人排序。

## 输入 / 输出

每条判断：

```text
Verdict
  creator_id: str
  decision: fit | unfit | pending
  reasons: str[]          # 至少 1 条
  evidence_ids: str[]     # 必须能在该创作者的 recent_posts 或 product_usage_evidence 中找到
  unknowns: str[]         # 用到了缺失数据时列出字段名，例如 audience、gpm
  rank: int | null        # 仅 fit 有值；1 表示最优先
  data_origin: real_model_output
  model_name: deepseek-chat
```

## 验收标准

1. Given `get_creator` 的返回，When 写入一条 Verdict，Then 每条 `evidence_ids` 都能在该返回的帖子 id 或 `evidence_id` 中找到。找不到的判断被应用层拒绝，不进入名单。
2. Given 模型回复里复制了 JSON 的 `expected_ai_signals.expected_decision_hint`，When 应用层保存，Then 仍以模型写出的 `decision` 为准，并且界面不展示 `expected_decision_hint`。
3. Given `metrics.gpm_origin=unknown`，When 判断引用 GPM，Then `unknowns` 含 `gpm`，`decision` 不得仅为「编造的 GPM 数值」；回复中的 GPM 只能是工具返回的 null 或 unknown。
4. Given 一批判断，When 展示，Then 每条带 `[LLM]` 和 `model_name=deepseek-chat`。
5. Given 没有 evidence_ids 的 fit，When 校验，Then 降为拒绝保存，错误码 `evidence_required`。
6. Given 三条 `decision=fit` 的判断，When 校验，Then `rank` 分别为 1、2、3 且互不重复。缺 rank、重复 rank 或从 0 起排，返回 `error_code=rank_invalid`，整批不保存。
7. Given `decision` 为 `unfit` 或 `pending`，When 校验，Then `rank` 为 null。非 null 返回 `rank_invalid`。
8. Given 校验通过的名单，When 排序展示，Then 顺序为 fit 的 rank 升序，其后 pending，其后 unfit。

## 边界

- 本 Task 不实现「关键词主题不符」的专用断言，那是 T06。
- 不生成邀请草稿。
