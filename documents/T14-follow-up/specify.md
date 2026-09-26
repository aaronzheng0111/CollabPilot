# Specify — 跟进合作

## 用户故事

至少一封草稿被标为 `approved` 之后，DeepSeek 为该创作者写一条跟进事项：下一步做什么、用哪个已确认渠道。用户看到事项后决定是否记下。记下不等于发送。

## 输入 / 输出

```text
FollowUp
  id: str
  campaign_id: str
  creator_id: str
  draft_id: str
  channel: tiktok_dm | instagram_dm | email
  next_step: str
  follow_status: waiting_user | noted
  data_origin: real_model_output
  model_name: deepseek-chat
```

## 验收标准

1. Given 该创作者没有 `approved` 草稿，When 请求跟进，Then 返回 `error_code=draft_not_approved`，不调用模型。
2. Given 有已批准草稿且 `confirmed_channel=email`，When 模型输出的 `channel` 不是 `email`，Then 整条不保存，错误码 `channel_mismatch`。
3. Given 校验通过且用户确认生成，When 写入，Then `follow_status=waiting_user`，`data_origin=real_model_output`，`model_name=deepseek-chat`，`next_step` 非空。
4. Given 用户未确认，When 调用保存跟进，Then `approval_required`。
5. Given 用户把事项标为已记下，When 更新，Then `follow_status=noted`，且不产生发送记录。
6. Given 代码库，When 搜索跟进模块，Then 不存在 TikTok、Instagram 或 SMTP 发送调用。

## 边界

- 不新增 `SENDING` 状态。
- 跟进文案由模型写，渠道必须等于已确认渠道，不能改渠道。
