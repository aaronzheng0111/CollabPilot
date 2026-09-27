# Specify — 关键词命中但主题不符

## 用户故事

昵称或话题含「翻译 / 英语 / AI / 留学 / 小语种」，但近期内容是字幕剪辑、考试英语、AI 绘画、留学申请或语言考试时，DeepSeek 读帖子后判定主题不符，给出原文引用，这些人不进入最终候选。应用层只核对引用是否真实、判断是否自洽，并把结论锁定，防止后续轮次把人补回来。数据里的 `keyword_mismatch` 标签只是评测答案，运行时不读。

## 后端验收

1. Given 一条 Verdict 的 `topic_match=mismatch` 且 `decision=fit`，When 校验，Then 返回 `error_code=topic_conflict`，整条不保存。
2. Given 一条 `topic_match=mismatch` 的 Verdict，When 校验，Then `mismatch_topic` 非空，`evidence_ids` 至少一条属于该创作者的 `recent_posts`，`quote` 不超过 80 字且是其中某条帖子标题或 caption 的原文子串；任一不满足返回 `quote_not_found`，不保存。
3. Given 校验通过的 mismatch 判断，When 写入活动，Then 该 `creator_id` 进入 `topic_rejected_ids`，不在最终候选中。之后的搜索轮次和同一活动的再次运行都不再把它交给模型重判，也不推荐。
4. Given 该创作者 GPM 高于 `target_gpm`（mock 中 `creator_012` 为 28.1），When 生成最终候选，Then 仍不在其中；应用层不存在依据 GPM 把 unfit 改成 fit 的路径。
5. Given 运行时代码，When 在 `backend/src/` 中搜索 `keyword_mismatch` 与 `scenario_tags`，Then 没有读取它们的代码（`mock_store.py` 的剔除列表除外）。
6. Given 标记为 `eval` 的 DeepSeek 集成测试，When 对 `creator_001`–`creator_006` 与 `creator_011`–`creator_015` 跑判断，Then 011–015 全部为 `topic_match=mismatch` 且 `decision=unfit`，001–006 没有一位是 mismatch。用 `load_oracle()` 对照，结果与模型原文写入 `verify.md` 备注。
7. Given 解释文本，When 查看来源，Then 主题不符的判断与理由标 `[LLM]`；「已锁定，不再推荐」这一动作标 `[RULE]`。

## 前端验收

8. Given 一位 mismatch 创作者，When 渲染主表，Then 该行 `decision` 为「不合适」，旁边有「主题不符：{mismatch_topic}」胶囊。
9. Given 选中该行，When 渲染「判断依据」面板，Then 显示 `quote` 原文与对应帖子 id，标 `[LLM]`；下方一行「已锁定，不再推荐」标 `[RULE]`；面板中没有「加回名单」按钮。

## 边界

- 判定由模型完成。规则只做引用核对、自洽校验和锁定，不替模型判定主题。
- 评测不通过时改提示词或补充品牌 `exclusion_rules` 的表述，不加关键词黑名单，不读测试答案字段。
- 用户想恢复被锁定的人，只能在对话里明确要求；恢复流程不在本 Task。
