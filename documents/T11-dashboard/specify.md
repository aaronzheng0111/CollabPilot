# Specify — 工作台集成与视觉验收

## 用户故事

T01–T14 各自交付了页面区块。本 Task 把它们按固定顺序装进同一页，按 `frontend/DESIGN.md`（Claude 设计系统）统一视觉，并从空会话走完一次完整演示。演示时能一眼看清：任务进度、AI 做了什么判断、依据是什么、哪些事在等用户决定。

## 后端验收

1. Given 一个 `campaign_id`，When 调用 `get_workbench_state(campaign_id)`，Then 一次返回页面需要的全部只读数据：活动状态、`parsed_goal`、`pending_decision` 列表、主表行、搜索轮次、判断、已排除、待确认、渠道、草稿、跟进。该函数不写库，不含业务规则。

## 前端验收：布局与交互

2. Given 打开 `frontend` 应用，When 页面加载，Then 左栏是数据表，右栏自上而下是工具状态栏、对话历史、输入框。页面上不存在把对话放在左栏的布局。
3. Given 左栏，When 自上而下读取，Then 顺序为：主表 → 「待你决定」→ 「合作目标」→ 「进度」→ 「判断依据」→ 「待确认」→ 「已排除」→ 「沟通渠道」→ 「草稿」→ 「跟进」。没有数据的区块不渲染，「待你决定」始终渲染。
4. Given 尚无工具调用，When 查看状态栏，Then 文案为「空闲」。Given `tool.started` 且工具名为 `search_creators`，When 渲染，Then 状态栏含该工具名与加载指示，左表含同一工具名的加载层。
5. Given 上一次成功结果有 N 行，When `search_creators` 处于 `running`，Then 这 N 行仍在，加载层可见。Given 随后 `tool.completed` 且 `ok=true` 并返回 M 个创作者，When 渲染，Then 主表行数为 M，列含 `creator_id`、`display_name`、`platforms`，加载层消失，状态栏为「完成」。
6. Given `apply_hard_filters` 成功返回 `kept`，When 渲染主表，Then 行集合等于 `kept`，且不再显示本次被移除的创作者。
7. Given 判断已写入且含 `rank`，When 渲染主表，Then `fit` 行按 `rank` 升序排在 pending 与 unfit 之前，列中可见 `rank`。
8. Given 已确认渠道且已有跟进记录，When 渲染，Then 主表可见 `channel`，「跟进」区可见 `next_step` 与 `follow_status`。
9. Given 活动状态为 `CLARIFYING`，When 渲染左表，Then 没有达人数据行，可见固定文案 `需求未完成，表格暂无筛选结果`。右栏历史中能看到追问。
10. Given `pending_decision` 含 `accept_short_list`，When 渲染，Then 「待你决定」有「是否接受当前人数」，草稿区为空。
11. Given 3 封 `pending_review` 草稿，When 渲染草稿区，Then 能看到 3 封正文和状态「待审核」，页面上没有「发送」按钮。
12. Given 同一 `session_id` 已有历史，When 重新打开，Then 右栏按时间展示已保存消息。
13. Given `tool.completed` 且 `ok=false`，When 渲染，Then 状态栏含 `failed` 与 `error_code`，主表行仍为上一次成功结果。

## 前端验收：视觉

14. Given `frontend/.streamlit/config.toml` 与 `frontend/theme.py`，When 提取其中所有十六进制色值，Then 每个都在 `frontend/DESIGN.md` 的 `colors` 列表中。
15. Given 渲染后的页面，When 检查背景色，Then 页面底色为 `canvas #faf9f5`，次级区卡片为 `surface-card #efe9de`，没有 `#ffffff` 背景。
16. Given 页面标题与区块标题，When 检查字体，Then 使用 T11 `plan.md` 定义的衬线字体栈且字重为 400；正文使用无衬线字体栈；`creator_id`、帖子 id、工具名使用等宽字体栈。
17. Given 珊瑚色 `primary #cc785c`，When 检查使用位置，Then 只出现在「待你决定」的批准按钮、勾选框与输入框聚焦环上；来源标签、表头、标题、卡片底色都不用珊瑚色。
18. Given 工具状态栏与「判断依据」面板，When 渲染，Then 底色为 `surface-dark #181715`，文字为 `on-dark #faf9f5`；running 圆点用 `accent-amber`，完成用 `success`，失败用 `error`。
19. Given `[MOCK]`、`[RULE]`、`[LLM]`、`[MOCK-SEND]` 四类标签，When 渲染，Then 都是胶囊形状（`rounded.pill`），样式按 T11 `plan.md` 的「来源标签样式」，四类在截图中可互相区分。
20. Given 浏览器视口 1440×900 与 1024×768，When 截图，Then 两栏都完整可见、没有页面级横向滚动，比例保持 3:2。

## 前端验收：完整走查

21. Given 空会话与 DeepSeek Key，When 粘贴 `docs/AI笔试题目.md` 的示例需求，并且只通过「待你决定」和对话回复推进，Then 页面依次出现：合作目标卡片 → 首轮搜索结果 → 硬过滤 → 判断与依据 → 合格不足与模型策略 → 第二轮结果 → 是否接受当前人数 → 保存 → 渠道确认 → 3 封待审核草稿。每一步截一张图，存入 `documents/T11-dashboard/screenshots/`，编号与步骤一致。

## 边界

- 界面不实现第二套业务规则。排除、去重、草稿校验都调用 backend 已有函数。
- 不把 FastAPI 当作本页的数据通道。
- 进度、证据摘录、草稿放在左栏主表下方，不放进右栏。
- 不照搬 DESIGN.md 的营销页组件（hero、96px 分段、珊瑚色通栏、页脚）。
