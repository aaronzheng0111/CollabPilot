# Specify — 关键词命中但主题不符

## 用户故事

昵称或话题含「翻译 / 英语 / AI / 留学 / 小语种」，但近期内容是字幕剪辑、考试英语、AI 绘画、留学申请或语言考试时，系统判定不适合，并且不进入最终候选。

## 验收标准

1. Given 创作者 `scenario_tags` 含 `keyword_mismatch`，When 跑主题校验，Then 最终候选集合中不存在该 `creator_id`。
2. Given 该创作者有 `recent_posts`，When 向用户解释，Then 解释引用至少一条帖子 id 或 caption/title 的原文片段（不超过 80 字）。
3. Given 该创作者 GPM 高于目标 `target_gpm`，When 过滤名单，Then 仍然不在最终候选中。
4. Given 最终候选，When 统计，Then 其中 `scenario_tags` 含 `keyword_mismatch` 的人数为 0。
5. Given 解释文本，When 查看来源，Then 排除动作标 `[RULE]`；若模型另外写了理由，该理由标 `[LLM]`，且不能把该创作者加回名单。

## 边界

- 规则使用数据里的 `keyword_mismatch` 标签作为可测试判定。模型可以补充解释，但不能覆盖排除。
