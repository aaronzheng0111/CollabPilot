# Specify — 理解合作目标

## 用户故事

用户粘贴一段合作需求。系统抽出结构化目标。原文含糊或缺少关键字段时，在右栏追问，并给出「推荐过滤」或「换一种说法」。关键字段补齐前不搜索。不关键的细节写成假设并展示，不追问。

## 输入 / 输出

- 输入：用户原文。
- 输出：`ParsedGoal` JSON，由应用层用 schema 校验。校验失败则再请求模型一次；仍失败则进入 `CLARIFYING`，向用户列出未通过校验的字段名。

`ParsedGoal` 字段：

- `brand`: string | null
- `product`: string | null
- `target_audience`: string[]
- `platforms`: (`tiktok` | `instagram`)[]
- `target_count`: int | null
- `inclusion_criteria`: string[]
- `exclusion_criteria`: string[]
- `outreach_count`: int | null
- `needs_user_approval`: bool | null
- `assumptions`: {field, value, reason}[]
- `missing_critical`: string[]

## 验收标准

1. Given 原文为「为一款面向中文用户的 AI 翻译工具，找 10 位使用这个翻译工具的创作者。优先选择最近持续发布相关内容的人，排除已经合作过的账号。整理候选名单，并为最合适的 3 位准备合作邀请草稿。发送前让我审核。」，When 解析完成且 schema 通过，Then `target_count=10`，`outreach_count=3`，`needs_user_approval=true`，`exclusion_criteria` 含「已经合作过的账号」，`platforms` 为 [`tiktok`,`instagram`] 且该平台值来自假设列表。
2. Given 原文没有品牌名，When 解析，Then `brand` 为 `LinguaGo AI 翻译` 且 `assumptions` 中有一条 `field=brand`。界面或回复文本能读到这条假设。
3. Given 原文没有人数，When 解析，Then `missing_critical` 含 `target_count`，状态为 `CLARIFYING`，不调用搜索工具。
4. Given 原文没有触达人数，When 解析，Then `missing_critical` 含 `outreach_count`，不生成草稿。
5. Given 原文没有写平台，When 解析，Then 不把平台放进 `missing_critical`；`platforms=[tiktok,instagram]` 且出现在 `assumptions`。
6. Given 模型输出不是合法 JSON 或缺少 schema 要求的键，When 应用层校验，Then 不把该输出写入活动的 `parsed_goal`。
7. Given 原文为「帮我找达人」，When 解析，Then 状态为 `CLARIFYING`，不调用 `search_creators`，回复含至少 2 个编号问题，且每个问题点名一个缺失字段。
8. Given 同一次 `CLARIFYING` 回复，When 读取正文，Then 存在标题为「推荐过滤」的块（含字段名、比较方式、示例值）或标题为「换一种说法」的块（一段可直接发送的改写）。两块至少有一块。
9. Given 追问已进行 3 轮且关键字段仍缺，When 生成第 3 轮回复，Then 列出假设，并要求用户回复「确认」或改正文；未确认前不搜索。
10. Given 用户在下一轮补齐 `target_count`、`outreach_count`、`needs_user_approval` 与已合作排除，When 再次解析，Then 状态为 `PARSED`。

## 边界

- 解析由 DeepSeek 完成，标 `[LLM]`。不用正则单独当最终解析器。
- 不在本 Task 搜索达人。
