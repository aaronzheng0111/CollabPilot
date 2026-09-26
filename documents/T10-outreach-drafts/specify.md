# Specify — 触达草稿

## 用户故事

用户已选定至少 3 位创作者，且每位都已确认沟通渠道。DeepSeek 为其中 3 位各写一封邀请草稿。三封正文不得相同。每封引用该创作者一条真实内容，并写明已确认渠道。发送按钮不存在。

## 验收标准

1. Given `saved_creator_ids` 长度小于 3，When 请求草稿，Then 不调用模型写草稿，返回 `error_code=need_three_creators`。
2. Given 至少 3 个已保存 id 且用户确认生成，When 完成，Then 持久化 3 条 Draft，`status=pending_review`，`data_origin=real_model_output`，`model_name=deepseek-chat`。
3. Given 3 条 Draft，When 比较 `body`，Then 两两不相等。
4. Given 某 Draft 的 `cited_post_id`，When 对照 `get_creator`，Then 该 id 属于对应创作者的 `recent_posts`。不属于则整批草稿不保存。
5. Given 草稿已保存，When 查找发送函数或按钮，Then 代码库中不存在向 TikTok、Instagram、SMTP 发消息的调用。活动状态停在 `DRAFT_REVIEW`。
6. Given 用户未确认，When 调用 `save_draft`，Then `approval_required`。
7. Given 某创作者没有 `confirmed_channel`，When 请求草稿，Then 返回 `error_code=channel_unconfirmed`，不调用模型。
8. Given `confirmed_channel=tiktok_dm`，When 草稿保存，Then `Draft.channel` 为 `tiktok_dm`，且 `body` 含「TikTok 私信」。渠道与确认值不一致则整批不保存。

## 边界

- 批准草稿只把单封状态改为 `approved`，仍不发送。批准逻辑可以在本 Task 实现为状态更新。
