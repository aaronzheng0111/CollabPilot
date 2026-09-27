# AI 达人合作工作台：计划

产品范围以 `docs/AI笔试题目.md` 为准。模型默认 DeepSeek `deepseek-chat`。目录保持 `frontend/`、`backend/`、`data/mock/` 分离。本文件是计划正文，与各 Task 规格冲突时，先改本文件对应段落，再改该 Task 的 `specify.md`。

## 规格放哪里

```text
documents/
  PLAN.md                   本文件
  README.md                 顺序、门禁、当前 Task
  T01-session-runtime/
    specify.md plan.md tasks.md implement.md verify.md
  ...
  T12-source-labels/
```

| 文件 | 作用 |
|------|------|
| `specify.md` | 可测试验收标准，分「后端验收」与「前端验收」 |
| `plan.md` | 数据模型、工具契约、状态、界面 |
| `tasks.md` | 原子步骤，分「后端任务」与「前端任务」 |
| `implement.md` | 代码约束与允许修改的文件。评估通过前不写该 Task 的业务代码 |
| `verify.md` | 通过后才能开始下一个 Task |

## 门禁

1. 实现顺序见下方 Task 表，不按文件夹编号。前一个未通过，不写后一个的业务代码。T13 在 T10 之前，T14 在 T11 之前。
2. 同一时刻只有一个 Task 可以是 `in_progress`。
3. 需求变更先改 `specify.md`，再改 `plan.md`、`tasks.md`，最后改代码。
4. 一个 Task 的后端任务和前端任务都 `done`，且 `verify.md` 全部通过，该 Task 才算 `verified`。

## 前后端分工

每个 Task 按纵向切片交付：后端先交付函数、工具和状态，前端在同一个 Task 里把它渲染出来。演示者在任一 Task 完成后都能在页面上看到这一步。

| 层 | 目录 | 职责 |
|----|------|------|
| 后端 | `backend/src/collabpilot/` | 运行时、工具、校验、状态机、SQLite。所有业务规则只写在这里 |
| 前端 | `frontend/` | Streamlit 页面。进程内调用 `ApplicationService`，订阅运行时事件，只做展示和收集用户批准 |

- 前端不实现第二套业务规则。排除、去重、渠道校验、草稿校验都调用后端函数。
- 前端不直接读 `data/mock/`，只读后端工具结果和活动存储。
- T01 交付页面骨架（左表、右栏状态栏、对话、主题）。T02–T14 各自往骨架里加一个区块。T11 做整页集成和视觉验收，不再从零搭页面。
- 前端组件放在 `frontend/components/`，每个组件是一个接受后端数据、返回渲染结果的函数，可用 Streamlit AppTest 单测。

## 模拟数据与测试答案

`data/mock/` 两个 JSON 共 44 个平台账号，按 `creator_id` 去重后 34 位创作者，全部标 `[MOCK]`。

以下字段是给测试和评测用的答案，运行时代码不得读取，也不得传给模型或界面：

- `scenario_tags`
- `expected_ai_signals`
- `product_usage_evidence[].product_relation`、`product_usage_evidence[].confidence`

`mock_store` 加载时剔除这些字段，只在 `backend/tests/` 的 fixture 中通过 `load_oracle()` 读取。自动化检查：`backend/src/` 下不出现这些字段名（`mock_store` 的剔除列表除外）。

评测答案（按 `creator_id`）：

| 场景 | 创作者 | 期望 |
|------|--------|------|
| 首轮合适 | 001–006 | `fit`，都在 30 天窗口内持续发布本品内容 |
| 放宽时间窗口后合适 | 007–009 | 相关帖子发布于 40–73 天前，`window_days=30` 搜不到，`window_days=90` 能搜到并判 `fit` |
| 关键词命中但主题不符 | 011–015 | 模型判 `unfit`，理由为字幕剪辑、考试英语、AI 绘画、留学申请、语言考试。012 的 GPM 为 28.1，高于 `target_gpm=20` |
| 已合作本品牌 | 016–019 | 规则排除，`cooperation_history` 中有 `is_current_brand=true` |
| 受众未知 | 020–023 | `pending`，受众四项显示「未知」 |
| 相关内容只有 1 条 | 024–027、034 | `pending`，持续性不足；034 同时 GPM 未知 |
| 竞品合作或无本品证据 | 010、028–033 | `pending` 或 `unfit` |

期望计数：首轮合格 6/10，缺口 4。模型把窗口放宽到 90 天后，合格 9/10，缺口 1，进入「是否接受当前人数」。这是评测期望，不是代码常量；实现不得写死这些 id 或人数。

## 界面

左栏是数据表，右栏是对话。工具状态栏在右栏顶部，对话输入在右栏底部。

```text
+------------------------------+---------------------------+
| 左：数据表                    | 右上：工具状态栏            |
| 随最近一次成功的工具结果替换    |  running 时显示工具名与加载 |
| 工具 running 时表格进入 loading | 右中：对话历史              |
|------------------------------|                           |
| 左下：待你决定 / 进度 / 证据 / |                           |
|       草稿 / 跟进（次级区）    | 右下：输入框                |
+------------------------------+---------------------------+
```

列宽比例 `3:2`（左宽于右）。不使用「左聊天、右五标签」布局。

### 视觉规范

视觉以 `frontend/DESIGN.md`（Claude 设计系统）为准，工作台的取用方式见 `documents/T11-dashboard/plan.md` 的「视觉映射」。要点：

- 底色用奶油色 `canvas #faf9f5`，不用纯白或冷灰。
- 标题用衬线字体、字重 400，正文用无衬线字体。
- 珊瑚色 `primary #cc785c` 只用于「待你决定」里的批准按钮，其他地方不用。
- 工具状态栏和证据摘录用深色产品面板 `surface-dark #181715`。
- 来源标签用胶囊形状 `badge-pill`。

### 工具状态栏

每条工具调用一条状态：

- `idle`：尚无工具调用，状态栏显示「空闲」
- `running`：显示工具名与加载指示
- `succeeded`：显示工具名与「完成」
- `failed`：显示工具名与 `error_code`

`tool.started` 把该工具置为 `running`。匹配的 `tool.completed` 置为 `succeeded` 或 `failed`。

### 左表何时变化

表格行集合等于最近一次 `succeeded` 且返回创作者列表的工具结果。更早的结果不保留在主表里。

| 最近成功的工具 | 主表行 | 列 |
|----------------|--------|----|
| 无 | 空表 | 无数据行 |
| `search_creators` | 聚合后的创作者 | `creator_id`、`display_name`、`platforms` |
| `apply_hard_filters` | `kept` | 上述列加 `filter=kept` |
| 判断写入后 | 仍在名单中的创作者 | 加 `decision`、`rank`；`fit` 按 `rank` 从小到大排在表顶 |
| `save_campaign_selection` | `saved_creator_ids` | 加 `saved=true` |
| `confirm_channel` | 已确认渠道的创作者 | 加 `channel` |
| 跟进记录写入后 | 已有跟进的创作者 | 次级表展示 `next_step`、`channel`、`follow_status` |

`running` 期间主表显示加载层，加载文案含当前工具名，行内容保持上一次成功结果，直到本次 `succeeded` 再替换。失败时加载层消失，行保持上一次成功结果，状态栏为 `failed`。

需求处于 `CLARIFYING` 时，主表不展示达人行，显示一句固定文案：`需求未完成，表格暂无筛选结果`。

进度、证据摘录、待审核草稿放在左表下方的次级区，不占右栏。草稿表没有「发送」按钮。

### 待你决定

所有需要用户批准的动作集中在左栏次级区顶部的「待你决定」卡片，每项一行，含说明、批准按钮和拒绝按钮。点击批准时，前端以 `user_approved=true` 调用对应后端函数；在对话里回复「确认」等价于批准当前唯一一项待决定事项。

| `pending_decision` | 来源 Task | 批准后 |
|--------------------|-----------|--------|
| `confirm_assumptions` | T02 | 按列出的假设解析，进入 `PARSED` |
| `accept_short_list` | T07 | 接受当前合格人数，进入保存 |
| `save_selection` | T09 | 写入 `saved_creator_ids` |
| `exclude_creator` | T09 | 从 saved 移到 excluded |
| `confirm_channel` | T13 | 写入 `confirmed_channel` |
| `save_drafts` | T10 | 3 封草稿写为 `pending_review` |
| `approve_draft` | T10 | 单封草稿改为 `approved`，仍不发送 |
| `save_follow_up` / `note_follow_up` | T14 | 写入或记下跟进，仍不发送 |

没有待决定事项时卡片显示「目前没有需要你决定的事项」。

## 需求不清时追问

关键字段只有四个：`target_count`、`outreach_count`、`needs_user_approval`、`exclusion_criteria` 中是否包含已合作排除。任一缺失，状态为 `CLARIFYING`，不调用搜索。品牌、产品、受众、平台都不是关键字段，缺失时写入假设，不追问。

右栏回复必须同时包含：

1. 至少 2 个编号问题，每个问题点名一个缺失字段。只缺 1 个关键字段时，第二个问题可以确认一条假设。
2. 一块「推荐过滤」：`字段 + 比较方式 + 示例值`，或一块「换一种说法」：一段可直接发送的改写。两块至少出现一块。

用户下一轮把关键字段补齐后，状态变为 `PARSED`，才允许 `search_creators`。同一活动自动追问最多 3 轮；第 3 轮仍缺关键字段时，列出假设并在「待你决定」中出现 `confirm_assumptions`，确认前不搜索。

非关键默认假设：品牌 `LinguaGo AI 翻译`，产品「AI 翻译工具」，受众「中文用户」，平台 `tiktok` 与 `instagram`。

## Task 顺序

| 顺序 | 文件夹 | 后端交付 | 前端交付 |
|------|--------|----------|----------|
| T01 | `T01-session-runtime` | 会话续聊；DeepSeek；工具事件；预算 | 页面骨架、主题、状态栏、对话历史 |
| T02 | `T02-goal-parsing` | 解析目标；不清时追问、推荐过滤或换一种说法 | 目标卡片与假设；`CLARIFYING` 空态；「待你决定」卡片骨架 |
| T03 | `T03-search-merge` | 只读 `data/mock`；按 `creator_id` 合并；时间窗口与粉丝门槛 | 主表显示搜索结果与加载层 |
| T04 | `T04-hard-filter` | 已合作按创作者排除（只读合作记录） | 主表换成 `kept`；移除原因 `[RULE]` |
| T05 | `T05-fit-judgment` | DeepSeek 判断、引用证据与发布时间，并对 fit 排序 | `decision`、`rank` 列与证据摘录 |
| T06 | `T06-keyword-mismatch` | DeepSeek 判定主题不符；应用层校验引用并锁定 | 不符者的原文引用与锁定标记 |
| T07 | `T07-insufficient-retry` | 人数不足时由模型提出再搜策略，应用层只做校验 | 进度区：轮次、合格 n/10、策略变更表 |
| T08 | `T08-audience-unknown` | 受众缺失标未知并阻止自动 fit | 受众「未知」与待确认列表 |
| T09 | `T09-save-dedup` | 确认后保存；不重复推荐已排除者 | 保存与排除的批准项；`saved` 列 |
| T13 | `T13-contact-channels` | 展示并确认沟通渠道；未知不编造；不发送 | 渠道表与确认操作 |
| T10 | `T10-outreach-drafts` | 3 封草稿，引用内容特点和已确认渠道；不发送 | 草稿表、批准按钮、无发送按钮 |
| T14 | `T14-follow-up` | 草稿批准后生成跟进事项；不发送 | 跟进次级表与「记下」操作 |
| T11 | `T11-dashboard` | 无新业务规则 | 整页集成、视觉验收、完整演示走查 |
| T12 | `T12-source-labels` | 无新业务规则 | 来源标签；设计说明、演示脚本、两周计划、启动说明 |

实现顺序按上表，不按文件夹编号。T13 在 T10 之前。T14 在 T11 之前。

当前进度：T01 verified；T02–T14 代码与自动化用例已完成（`in_progress`，待人工走查后依次改 `verified`）。实现顺序已走完，无下一个代码 Task。
