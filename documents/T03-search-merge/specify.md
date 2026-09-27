# Specify — 搜索与跨平台合并

## 用户故事

目标状态为 `PARSED` 之后，Agent 用工具读取模拟达人，按时间窗口和粉丝门槛筛出近期活跃的账号，并按 `creator_id` 合并 TikTok 与 Instagram。模型和界面看不到数据里给测试用的答案字段。

## 输入 / 输出

- 工具 `search_creators`：`platforms`、`keywords`（string[]）、`window_days`（int，默认 30）、`min_followers`（int | null，默认 null）、`limit`（int，默认 50）。
- 命中规则：关键词出现在 `display_name`、`content_topics`、`profile.signature` 或 `profile.biography`、窗口内帖子的标题或 caption 之一；并且该账号至少有 1 条帖子发布在 `window_days` 天内；并且 `min_followers` 非空时粉丝数不低于它。
- 返回：`accounts[]`（平台账号）、`creators[]`（按 creator_id 聚合，含 `creator_id`、`display_name`、`platforms`、`account_ids`）、`meta`（`window_days`、`min_followers`、`keywords`、`outside_window_hits`）。`outside_window_hits` 是关键词命中但窗口内没有帖子的创作者人数，只给人数，不给 id。
- 工具 `get_creator`：`creator_id`。返回该创作者在两个 JSON 里的账号、`recent_posts`（每条带 `age_days`）、`cooperation_history`、`audience`、`metrics`、`contact`、`product_usage_evidence`。缺失字段保持 JSON 原值，不补造。

## 后端验收

1. Given `data/mock/tiktok_creators.json` 与 `instagram_creators.json`，When 调用 `search_creators(platforms=[tiktok,instagram], keywords=["翻译"])`，Then 返回的账号来自两个文件，且 `meta.is_mock` 均为 true。
2. Given `creator_001` 同时在两个文件，When 搜索结果包含该 id，Then `creators` 里只有一条 `creator_001`，`platforms` 为 [`tiktok`,`instagram`]。
3. Given `get_creator(creator_001)`，When 成功，Then 返回体同时含 `tiktok` 与 `instagram` 键，且 `display_name` 两边一致。
4. Given 只存在于一个平台的创作者，When `get_creator`，Then 另一平台键为 null，不为它生成账号。
5. Given 工具结果，When 序列化给模型或界面，Then `data_origin` 为 `mock_seed` 或结果标明 `[MOCK]`；结果中不存在 `scenario_tags`、`expected_ai_signals`、`product_relation`、`confidence` 这四个键。
6. Given 活动状态不是 `PARSED`，When 模型请求 `search_creators`，Then 工具返回 `ok=false`、`error_code=goal_not_ready`，不读全量达人进回复。
7. Given `keywords=["翻译"]`，When 分别以 `window_days=30` 和 `window_days=90` 搜索，Then 30 天结果不含 `creator_007`、`creator_008`、`creator_009`，`meta.outside_window_hits>=3`；90 天结果包含这三位。
8. Given `min_followers=100000`，When 搜索，Then 返回的每个账号 `follower_count` 或 `followers_count` 都不低于 100000；另一平台账号低于门槛时只去掉该账号，不去掉整个创作者。
9. Given 运行时代码，When 在 `backend/src/` 中搜索 `scenario_tags`、`expected_ai_signals`、`product_relation`，Then 只在 `mock_store.py` 的剔除列表中出现。

## 前端验收

10. Given `search_creators` 处于 `running`，When 渲染主表，Then 主表保留上一次成功的行，并显示含 `search_creators` 的加载层。
11. Given `search_creators` 成功返回 M 个创作者，When 渲染，Then 主表行数为 M，列含 `creator_id`、`display_name`、`platforms`，每行带 `[MOCK]`；主表上方一行小字写明本次 `keywords`、`window_days`、`min_followers`。

## 边界

- 只读 JSON。不写回 `data/mock/`。
- 不在本 Task 做适合度判断或排除已合作。
