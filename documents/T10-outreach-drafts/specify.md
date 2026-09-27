# Specify — 触达草稿

## 用户故事

用户已选定至少 3 位创作者，且每位都已确认沟通渠道。DeepSeek 为其中 3 位各写一封邀请草稿。三封正文不得相同，各自引用该创作者一条不同的真实内容，并写明已确认渠道。发送按钮不存在。

## 后端验收

1. Given `saved_creator_ids` 长度小于 3，When 请求草稿，Then 不调用模型写草稿，返回 `error_code=need_three_creators`。
2. Given 至少 3 个已保存 id 且用户确认生成，When 完成，Then 持久化 3 条 Draft，`status=pending_review`，`data_origin=real_model_output`，`model_name=deepseek-chat`。
3. Given 3 条 Draft，When 比较 `body`，Then 两两不相等，且 3 个 `cited_post_id` 两两不相等。
4. Given 某 Draft 的 `cited_post_id`，When 对照 `get_creator`，Then 该 id 属于对应创作者的 `recent_posts`。不属于则整批草稿不保存。
5. Given 草稿已保存，When 查找发送函数或按钮，Then 代码库中不存在向 TikTok、Instagram、SMTP 发消息的调用。活动状态停在 `DRAFT_REVIEW`。
6. Given 用户未确认，When 调用 `save_draft`，Then `approval_required`。
7. Given 某创作者没有 `confirmed_channel`，When 请求草稿，Then 返回 `error_code=channel_unconfirmed`，不调用模型。
8. Given 某创作者的 `confirmed_channel`，When 草稿保存，Then `Draft.channel` 等于它，且 `body` 含 `CHANNEL_LABELS` 中对应名称：`tiktok_dm` →「TikTok 私信」，`instagram_dm` →「Instagram 私信」，`email` →「邮件」。渠道与确认值不一致则整批不保存，错误码 `channel_mismatch`。
9. Given 某 Draft，When 校验正文，Then `body` 中含 `cited_post_id` 所指帖子标题或 caption 的连续原文片段，长度不少于 8 个字；否则 `quote_not_found`，整批不保存。
10. Given 标记为 `eval` 的 DeepSeek 集成测试，When 为 `creator_001`–`creator_003` 生成草稿，Then 通过用例 3、4、8、9 的校验。三封草稿原文写入 `verify.md` 备注。

## 前端验收

11. Given 3 封 `pending_review` 草稿，When 渲染次级区「草稿」，Then 每封一张卡片：创作者名、渠道中文名、被引用帖子原文、正文、状态「待审核」；区块标题带 `[LLM]` 与 `deepseek-chat`。
12. Given 模型已返回草稿但尚未保存，When 渲染「待你决定」，Then 有一行「保存 3 封草稿供审核」；批准后草稿卡片出现。保存后「待你决定」每封一行「审核草稿：{display_name}」，含批准与退回按钮；批准后该草稿状态显示「已批准」。
13. Given 草稿区，When 查找按钮，Then 没有「发送」类按钮；区块内有固定说明「草稿不会发送」。

## 边界

- 批准草稿只把单封状态改为 `approved`，退回改为 `rejected`，都不发送。批准逻辑在本 Task 实现为状态更新。
