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
| `specify.md` | 可测试验收标准 |
| `plan.md` | 数据模型、工具契约、状态、界面 |
| `tasks.md` | 原子步骤 |
| `implement.md` | 代码约束。评估通过前不写该 Task 的业务代码 |
| `verify.md` | 通过后才能开始下一个 Task |

## 门禁

1. 实现顺序见下方 Task 表，不按文件夹编号。前一个未通过，不写后一个的业务代码。T13 在 T10 之前，T14 在 T11 之前。
2. 同一时刻只有一个 Task 可以是 `in_progress`。
3. 需求变更先改 `specify.md`，再改 `plan.md`、`tasks.md`，最后改代码。

## 界面

左栏是数据表，右栏是对话。工具状态栏在右栏顶部，对话输入在右栏底部。

```text
+------------------------------+---------------------------+
| 左：数据表                    | 右上：工具状态栏            |
| 随最近一次成功的工具结果替换    |  running 时显示工具名与加载 |
| 工具 running 时表格进入 loading | 右中：对话历史              |
|                              | 右下：输入框                |
+------------------------------+---------------------------+
```

列宽比例 `3:2`（左宽于右）。不使用「左聊天、右五标签」布局。

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

进度、证据摘录、待审核草稿放在左表下方的次级表，不占右栏。草稿表没有「发送」按钮。

## 需求不清时追问

用户原文缺少关键字段，或短到无法抽出品牌、人数、排除条件中的至少两项时，状态为 `CLARIFYING`，不调用搜索。

右栏回复必须同时包含：

1. 至少 2 个编号问题，每个问题点名一个缺失字段。
2. 一块「推荐过滤」：`字段 + 比较方式 + 示例值`，或一块「换一种说法」：一段可直接发送的改写。两块至少出现一块。

用户下一轮把关键字段补齐后，状态变为 `PARSED`，才允许 `search_creators`。同一活动自动追问最多 3 轮；第 3 轮仍缺关键字段时，列出假设并请用户回复「确认」或继续改正文，确认前不搜索。

非关键默认假设不变：品牌 `LinguaGo AI 翻译`，平台 `tiktok` 与 `instagram`。缺平台不追问，写入假设。

## Task 顺序

| 顺序 | 文件夹 | 交付 |
|------|--------|------|
| T01 | `T01-session-runtime` | 会话续聊；DeepSeek；工具事件；预算 |
| T02 | `T02-goal-parsing` | 解析目标；不清时追问、推荐过滤或换一种说法 |
| T03 | `T03-search-merge` | 只读 `data/mock`；按 `creator_id` 合并 |
| T04 | `T04-hard-filter` | 已合作按创作者排除 |
| T05 | `T05-fit-judgment` | DeepSeek 判断、引用证据，并对 fit 排序 |
| T06 | `T06-keyword-mismatch` | 主题不符者不进名单 |
| T07 | `T07-insufficient-retry` | 人数不足时由模型提出再搜策略，应用层只做校验 |
| T08 | `T08-audience-unknown` | 受众缺失标未知 |
| T09 | `T09-save-dedup` | 确认后保存；不重复推荐已排除者 |
| T13 | `T13-contact-channels` | 展示并确认沟通渠道；未知不编造；不发送 |
| T10 | `T10-outreach-drafts` | 至少 3 封草稿，引用内容特点和已确认渠道；不发送 |
| T14 | `T14-follow-up` | 草稿批准后生成跟进事项；不发送 |
| T11 | `T11-dashboard` | 左表右聊；表含排序、渠道和跟进 |
| T12 | `T12-source-labels` | MOCK / LLM / RULE 标签与一页设计说明 |

实现顺序按上表，不按文件夹编号。T13 在 T10 之前。T14 在 T11 之前。

当前允许开始实现的只有 **T01**。
