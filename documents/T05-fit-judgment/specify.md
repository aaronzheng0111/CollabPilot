# Specify — 匹配判断

## 用户故事

对硬过滤后的创作者，DeepSeek 阅读帖子（含发布时间）与合作记录，给出适合、不适合或待确认，指出证据 id，并对适合的人排序。优先最近持续发布相关内容的人。没有模型就没有候选名单。

## 输入 / 输出

每条判断：

```text
Verdict
  creator_id: str
  decision: fit | unfit | pending
  reasons: str[]            # 至少 1 条
  evidence_ids: str[]       # 必须能在该创作者的 recent_posts 或 product_usage_evidence 中找到
  related_post_ids: str[]   # 模型认为与品牌相关的帖子；fit 时非空
  topic_match: match | mismatch | unclear
  mismatch_topic: str | null   # topic_match=mismatch 时必填，例如「影视字幕剪辑」
  quote: str | null            # topic_match=mismatch 时必填，帖子原文片段，不超过 80 字
  unknowns: str[]           # 用到了缺失数据时列出字段名，例如 audience、gpm
  rank: int | null          # 仅 fit 有值；1 表示最优先
  data_origin: real_model_output
  model_name: deepseek-chat
```

## 后端验收

1. Given `get_creator` 的返回，When 写入一条 Verdict，Then 每条 `evidence_ids` 都能在该返回的帖子 id 或 `evidence_id` 中找到。找不到的判断被应用层拒绝，不进入名单。
2. Given 发给模型的提示词和工具结果，When 检查，Then 不含 `expected_ai_signals`、`scenario_tags`、`product_relation`、`confidence`；界面不展示 `expected_decision_hint`。
3. Given `metrics.gpm_origin=unknown`，When 判断引用 GPM，Then `unknowns` 含 `gpm`，`decision` 不得仅为「编造的 GPM 数值」；回复中的 GPM 只能是工具返回的 null 或 unknown。
4. Given 一批判断，When 展示，Then 每条带 `[LLM]` 和 `model_name=deepseek-chat`。
5. Given 没有 evidence_ids 的 fit，When 校验，Then 降为拒绝保存，错误码 `evidence_required`。
6. Given 三条 `decision=fit` 的判断，When 校验，Then `rank` 分别为 1、2、3 且互不重复。缺 rank、重复 rank 或从 0 起排，返回 `error_code=rank_invalid`，整批不保存。
7. Given `decision` 为 `unfit` 或 `pending`，When 校验，Then `rank` 为 null。非 null 返回 `rank_invalid`。
8. Given 校验通过的名单，When 排序展示，Then 顺序为 fit 的 rank 升序，其后 pending，其后 unfit。
9. Given 判断用的提示词，When 检查，Then 每条帖子带 `age_days`，并写明「优先最近持续发布相关内容」与品牌的 `exclusion_rules`。
10. Given `decision=fit` 的 Verdict，When 校验，Then `related_post_ids` 非空且都属于该创作者，否则 `evidence_required`。应用层据此算出 `recent_related_count`（窗口内相关帖子数）与 `latest_related_age_days`，写入 Verdict 旁的 `recency` 字段，不由模型填写。
11. Given DeepSeek 调用失败或未配置 Key，When 进入判断步骤，Then 不产生任何 Verdict，活动停在 `EVALUATING`，回复含 `model_unavailable`；不存在按关键词命中数、粉丝数或 GPM 排序的备用名单。
12. Given 标记为 `eval` 的 DeepSeek 集成测试（不在单元测试中运行），When 对 mock 数据首轮（`window_days=30`）跑判断，Then `creator_001`–`creator_006` 全部为 fit，`creator_011`–`creator_015` 没有一位是 fit。受众未知者的断言在 T08。结果与模型原始输出写入 `verify.md` 备注。

## 前端验收

13. Given 判断已写入，When 渲染主表，Then 列加 `decision`（显示「合适 / 待确认 / 不合适」）与 `rank`，顺序同用例 8，每行带 `[LLM]`。
14. Given 选中主表中一位创作者，When 渲染次级区「判断依据」，Then 以深色面板展示该创作者的 `reasons`、每条 `evidence_ids` 对应的帖子原文与 `age_days`、`recency`、`unknowns`（逐项写「未知：gpm」这类文案），并显示 `deepseek-chat`。

## 边界

- 本 Task 定义 `topic_match`、`mismatch_topic`、`quote` 字段并要求模型填写；主题不符的校验与锁定在 T06。
- 不生成邀请草稿。
