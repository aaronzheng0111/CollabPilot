# Specify — Streamlit 工作台

## 用户故事

用户打开页面后，左边看到会随工具结果替换的数据表，右边与 Agent 对话。工具执行时，右栏顶部状态栏显示工具名和加载状态，左表进入 loading。工具成功后，左表换成该工具返回的行。

## 验收标准

1. Given 打开 `frontend` 应用，When 页面加载，Then 左栏是数据表，右栏自上而下是工具状态栏、对话历史、输入框。页面上不存在把对话放在左栏的布局。
2. Given 尚无工具调用，When 查看状态栏，Then 文案为「空闲」。Given `tool.started` 且工具名为 `search_creators`，When 渲染，Then 状态栏含该工具名与加载指示，左表含同一工具名的加载层。
3. Given 上一次成功结果有 N 行，When `search_creators` 处于 `running`，Then 这 N 行仍在，加载层可见。Given 随后 `tool.completed` 且 `ok=true` 并返回 M 个创作者，When 渲染，Then 主表行数为 M，列含 `creator_id`、`display_name`、`platforms`，加载层消失，状态栏为「完成」。
10. Given 判断已写入且含 `rank`，When 渲染主表，Then `fit` 行按 `rank` 升序排在 pending 与 unfit 之前，列中可见 `rank`。
11. Given 已确认渠道且已有跟进记录，When 渲染，Then 主表可见 `channel`，次级表可见 `next_step` 与 `follow_status`。
4. Given `apply_hard_filters` 成功返回 `kept`，When 渲染主表，Then 行集合等于 `kept`，且不再显示本次被移除的创作者。
5. Given 活动状态为 `CLARIFYING`，When 渲染左表，Then 没有达人数据行，可见固定文案 `需求未完成，表格暂无筛选结果`。右栏历史中能看到追问。
6. Given `pending_decision=accept_short_list`，When 渲染，Then 左栏次级区域有「是否接受当前人数」，草稿表为空。
7. Given 3 封 `pending_review` 草稿，When 渲染左栏草稿表，Then 能看到 3 封正文和状态「待审核」，页面上没有「发送」按钮。
8. Given 同一 `session_id` 已有历史，When 重新打开，Then 右栏按时间展示已保存消息。
9. Given `tool.completed` 且 `ok=false`，When 渲染，Then 状态栏含 `failed` 与 `error_code`，主表行仍为上一次成功结果。

## 边界

- 界面不实现第二套业务规则。排除、去重、草稿校验都调用 backend 已有函数。
- 不把 FastAPI 当作本页的数据通道。
- 进度、证据摘录、草稿放在左栏主表下方，不放进右栏。
