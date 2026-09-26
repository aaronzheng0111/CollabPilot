# Specify — 保存名单与去重

## 用户故事

用户确认后，系统把选中的创作者保存到当前活动。再次运行同一活动时，不重复保存，也不再推荐已排除的创作者。

## 验收标准

1. Given 用户没有确认，When 模型调用 `save_campaign_selection`，Then 返回 `error_code=approval_required`，活动中 `saved_creator_ids` 不变。
2. Given 用户确认保存 `creator_001` 与 `creator_002`，When 工具成功，Then `saved_creator_ids` 恰好为这两个 id，状态为 `SELECTED`。
3. Given `creator_001` 已在 `saved_creator_ids`，When 再次保存它，Then 集合仍只有一条，回复含「已在名单中」。
4. Given `creator_003` 在 `excluded_creator_ids`，When 新的一轮搜索推荐，Then 推荐列表不含 `creator_003`。
5. Given 同一 `campaign_id` 重启进程，When 读取活动，Then `saved_creator_ids` 与 `excluded_creator_ids` 与重启前相同。
6. Given 调用 `exclude_creator`，When 用户未确认，Then `approval_required`。确认后该 id 从 saved 集合移除并进入 excluded。

## 边界

- 本 Task 不生成草稿。
- 不跨活动做硬拦截。若同一创作者在另一个活动里，本 Task 只在回复中加一句提示，不自动排除。
