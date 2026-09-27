# Specify — 保存名单与去重

## 用户故事

用户在名单里勾选创作者并确认后，系统把选中的人保存到当前活动。再次运行同一活动时，不重复保存，也不再推荐已排除的创作者。

## 后端验收

1. Given 用户没有确认，When 模型调用 `save_campaign_selection`，Then 返回 `error_code=approval_required`，活动中 `saved_creator_ids` 不变。
2. Given 用户确认保存 `creator_001` 与 `creator_002`，When 工具成功，Then `saved_creator_ids` 恰好为这两个 id，状态为 `SELECTED`。
3. Given `creator_001` 已在 `saved_creator_ids`，When 再次保存它，Then 集合仍只有一条，回复含「已在名单中」。
4. Given `creator_003` 在 `excluded_creator_ids`，When 新的一轮搜索推荐，Then 推荐列表不含 `creator_003`。
5. Given 同一 `campaign_id` 重启进程，When 读取活动，Then `saved_creator_ids`、`excluded_creator_ids`、`topic_rejected_ids` 与重启前相同。
6. Given 调用 `exclude_creator`，When 用户未确认，Then `approval_required`。确认后该 id 从 saved 集合移除并进入 excluded。
7. Given 同一 `session_id` 已有活动，When 用户再次发送同一段合作需求，Then 沿用原 `campaign_id`，不新建活动；新一轮推荐不含 `saved_creator_ids`（标为「已在名单中」）、`excluded_creator_ids` 与 `topic_rejected_ids`，回复写明各跳过了几位。
8. Given 某 pending 创作者，When 用户勾选它并确认保存，Then 它进入 `saved_creator_ids`，并记录 `accepted_from_pending=true`；它的 `decision` 仍为 `pending`，不改成 fit。

## 前端验收

9. Given 判断已写入，When 渲染主表，Then 有「选中」勾选列：fit 默认勾选，pending 默认不勾选但可勾选，unfit 与被锁定的行不可勾选。
10. Given 用户点击「保存到活动」，When 渲染「待你决定」，Then 出现一行「保存 {n} 位到活动」并列出名字；批准后主表加 `saved=true` 列，该行从「待你决定」消失。
11. Given 活动已有 saved 或 excluded，When 同一需求再次运行，Then 主表上方显示「已在名单中 {a} 位，已排除 {b} 位，此前判定不符 {c} 位，均未重复推荐」。

## 边界

- 本 Task 不生成草稿。
- 不跨活动做硬拦截。若同一创作者在另一个活动里，本 Task 只在回复中加一句提示，不自动排除。
