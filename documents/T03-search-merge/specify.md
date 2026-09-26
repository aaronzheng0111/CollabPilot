# Specify — 搜索与跨平台合并

## 用户故事

目标状态为 `PARSED` 之后，Agent 用工具读取模拟达人，按 `creator_id` 合并 TikTok 与 Instagram。

## 输入 / 输出

- 工具 `search_creators`：`platforms`、`keywords`（string[]）、`limit`（int，默认 50）。
- 返回：`accounts[]`（平台账号）和 `creators[]`（按 creator_id 聚合）。聚合项含 `creator_id`、`display_name`、`platforms`、`account_ids`。
- 工具 `get_creator`：`creator_id`。返回该创作者在两个 JSON 里的账号、`recent_posts`、`cooperation_history`、`audience`、`metrics`。缺文件中的字段保持 JSON 原值，不补造。

## 验收标准

1. Given `data/mock/tiktok_creators.json` 与 `instagram_creators.json`，When 调用 `search_creators(platforms=[tiktok,instagram], keywords=["翻译"])`，Then 返回的账号来自两个文件，且 `meta.is_mock` 均为 true。
2. Given `creator_001` 同时在两个文件，When 搜索结果包含该 id，Then `creators` 里只有一条 `creator_001`，`platforms` 为 [`tiktok`,`instagram`]。
3. Given `get_creator(creator_001)`，When 成功，Then 返回体同时含 `tiktok` 与 `instagram` 键，且 `display_name` 两边一致。
4. Given 只存在于一个平台的创作者，When `get_creator`，Then 另一平台键为 null，不为它生成账号。
5. Given 工具结果，When 序列化给模型，Then `data_origin` 为 `mock_seed` 或结果标明 `[MOCK]`。结果中不包含把 `expected_ai_signals` 当作结论的字段；该字段可以省略。
6. Given 活动状态不是 `PARSED`，When 模型请求 `search_creators`，Then 工具返回 `ok=false`、`error_code=goal_not_ready`，不读全量达人进回复。

## 边界

- 只读 JSON。不写回 `data/mock/`。
- 不在本 Task 做适合度判断或排除已合作。
