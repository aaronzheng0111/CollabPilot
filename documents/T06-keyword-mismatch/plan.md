# Plan — 关键词命中但主题不符

## 契约

`validate_topic_verdicts(verdicts, merged_creators) -> accepted, errors`

- `topic_match=mismatch` 时要求 `decision=unfit`，否则 `topic_conflict`。
- `mismatch_topic` 非空；`quote` 长度不超过 80 字，且是某条 `evidence_ids` 所指帖子标题或 caption 的子串，否则 `quote_not_found`。
- `topic_match=unclear` 时 `decision` 只能是 `pending` 或 `unfit`。

`lock_topic_rejections(campaign, accepted)`：把 mismatch 的 `creator_id` 追加到 `Campaign.topic_rejected_ids`，写入 `rule=true` 的锁定记录。

`search_creators` 结果交给模型前，应用层减去 `topic_rejected_ids` 与 T04 的 `own_brand_cooperated`，并在回复中说明「已有 N 位此前判定不符，未重复评估」。

此校验在 T05 的 `validate_verdicts` 之后、写入最终名单之前调用。无开关可关闭。

## 提示片段

在 T05 提示词中补充：「昵称或话题命中关键词不代表内容相关。逐条阅读帖子，判断内容主题是否服务于『使用 AI 翻译工具』这一合作目标；若主题是影视字幕剪辑、应试语言学习、AI 绘画、留学申请等，填 `topic_match=mismatch`，`mismatch_topic` 写主题，`quote` 摘一段帖子原文。」

## 状态

仍为 `EVALUATING`。活动增加字段 `topic_rejected_ids: str[]`，T09 落盘时一起保存。

## 界面

- 主表 `decision=unfit` 且 mismatch 的行，加 `badge-pill`「主题不符：{mismatch_topic}」。
- `evidence_panel.py` 增加 mismatch 区块：`quote` 用引用样式，下方 `[RULE]` 锁定行。

## 评测

`backend/tests/eval/test_topic_eval.py`，标记 `eval`。

## 模块

- `backend/src/collabpilot/campaign/topic_match.py`
- `backend/config/prompts/campaign.md`
- `frontend/components/main_table.py`、`frontend/components/evidence_panel.py`
