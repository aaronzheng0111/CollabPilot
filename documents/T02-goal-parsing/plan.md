# Plan — 理解合作目标

## 数据模型

活动记录增加：

```text
Campaign.goal_status: PARSING | CLARIFYING | PARSED
Campaign.parsed_goal: ParsedGoal | null
Campaign.goal_origin: real_model_output
Campaign.goal_model_name: string
```

本 Task 只定义并写入 `parsed_goal`。活动存储的物理表在 T09 落盘；本 Task 允许先放在会话 metadata，T09 再迁到活动表。规格要求字段名保持不变。

## 契约

- 不设独立 `parse_goal` 工具。模型在回复中输出一个 fenced JSON 块，应用层提取并校验。
- 校验函数 `validate_parsed_goal(obj) -> ParsedGoal | list[str]`，纯函数，可单测。
- 关键字段：`target_count`、`outreach_count`、`needs_user_approval`、`exclusion_criteria` 中是否包含已合作排除。四者任一缺失则 `CLARIFYING`。
- 非关键默认假设（必须写入 `assumptions`）：品牌 `LinguaGo AI 翻译`，产品「AI 翻译工具」，受众「中文用户」，平台 `tiktok`+`instagram`。

## 状态

`CREATED → PARSING → CLARIFYING | PARSED`

## 追问结构

`CLARIFYING` 回复除 `missing_critical` 外，还要能被应用层解析出：

```text
Grill
  questions: string[]          # 长度 >= 2
  filter_suggestion: {field, operator, example} | null
  rephrase: string | null
```

`filter_suggestion` 与 `rephrase` 至少一个非空。自动追问轮次计在活动字段 `grill_rounds`，上限 3。

## 界面

本 Task 不实现页面布局。追问文本出现在对话回复中。T11 把对话放在右栏，并把 `CLARIFYING` 时的左表置为固定空态文案。

## 模块

- `backend/src/collabpilot/` 下新增 `campaign/goal.py`（校验与关键字段表）
- 系统提示补充：解析时只输出约定 JSON，不调用尚未注册的搜索工具
