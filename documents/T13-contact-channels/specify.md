# Specify — 沟通渠道

## 用户故事

保存名单之后、写草稿之前，用户看到每位创作者在模拟资料里的联系方式，并确认要用哪一个渠道。未确认不能写草稿。渠道未知时显示未知，不编造成已授权。本模块不发送消息。

## 输入 / 输出

渠道只来自该创作者 mock 资料的 `contact`：

```text
ContactView
  creator_id: str
  preferred_channel: tiktok_dm | instagram_dm | email | unknown
  dm_available: bool
  email: str | null
  consent_status: granted | denied | unknown
  data_origin: mock_seed

ConfirmedChannel
  creator_id: str
  channel: tiktok_dm | instagram_dm | email
  user_approved: true
```

## 验收标准

1. Given `saved_creator_ids` 含一位创作者且 `contact.preferred_channel=tiktok_dm`，When 打开渠道列表，Then 该行渠道为 `tiktok_dm`，来源标记为 `[MOCK]`。
2. Given `consent_status=unknown`，When 展示，Then 文案为「未知」，不是「已同意」或「已拒绝」。
3. Given 用户未确认，When 调用 `confirm_channel`，Then 返回 `approval_required`，`confirmed_channel` 仍为空。
4. Given 用户确认的渠道不在该创作者的 `preferred_channel` 且不是其非空 `email` 所对应的 `email`，When 调用 `confirm_channel`，Then 返回 `channel_not_on_profile`。
5. Given `preferred_channel=unknown` 且 `email` 为 null，When 请求确认，Then 返回 `channel_unknown`，不写入 `confirmed_channel`。
6. Given 确认成功，When 查代码路径，Then 不存在对 TikTok、Instagram 或 SMTP 的发送调用。

## 边界

- 不生成草稿，不生成跟进。草稿读取本 Task 写入的 `confirmed_channel`。
