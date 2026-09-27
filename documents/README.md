# 规格包索引

一次只实现一个 Task。按 [PLAN.md](PLAN.md) 的实现顺序，而不是文件夹编号。当前 Task 的 `verify.md` 全部通过并被标为 `verified` 之后，才能把下一个 Task 标为 `in_progress`。

计划正文：[PLAN.md](PLAN.md)。需求变更先改该 Task 的 `specify.md`，再改 `plan.md`、`tasks.md`，最后才改代码。

| 顺序 | 目录 | 状态 | 一句话 |
|------|------|------|--------|
| 1 | [T01-session-runtime](T01-session-runtime/) | verified | 会话、DeepSeek、工具事件、运行预算；页面骨架与主题 |
| 2 | [T02-goal-parsing](T02-goal-parsing/) | in_progress | 解析目标；含糊时追问并推荐过滤或改写；「待你决定」卡片 |
| 3 | [T03-search-merge](T03-search-merge/) | in_progress（自动化通过，待人工走查） | 按时间窗口搜索并按创作者合并 |
| 4 | [T04-hard-filter](T04-hard-filter/) | in_progress（自动化通过，待人工走查） | 已合作与平台硬过滤 |
| 5 | [T05-fit-judgment](T05-fit-judgment/) | in_progress（自动化与 eval 通过，待人工走查） | 模型判断适合度并排序 |
| 6 | [T06-keyword-mismatch](T06-keyword-mismatch/) | in_progress（自动化与 eval 通过，待人工走查） | 模型判定关键词命中但主题不符 |
| 7 | [T07-insufficient-retry](T07-insufficient-retry/) | in_progress（自动化与 eval 通过，待人工走查） | 由模型提出再搜策略 |
| 8 | [T08-audience-unknown](T08-audience-unknown/) | in_progress（自动化通过，待人工走查） | 受众缺失标未知 |
| 9 | [T09-save-dedup](T09-save-dedup/) | in_progress（自动化通过，待人工走查） | 保存名单并去重 |
| 10 | [T13-contact-channels](T13-contact-channels/) | in_progress（自动化通过，待人工走查） | 确认沟通渠道，不发送 |
| 11 | [T10-outreach-drafts](T10-outreach-drafts/) | in_progress（自动化与 eval 通过，待人工走查） | 三封草稿，引用已确认渠道 |
| 12 | [T14-follow-up](T14-follow-up/) | in_progress（自动化通过，待人工走查） | 批准草稿后的跟进事项，不发送 |
| 13 | [T11-dashboard](T11-dashboard/) | in_progress（自动化通过，待人工走查） | 整页集成与 Claude 视觉验收 |
| 14 | [T12-source-labels](T12-source-labels/) | in_progress（自动化通过，待人工走查） | 来源标注与提交材料 |

每个目录内五份文件：

- `specify.md`：验收标准，分后端验收与前端验收
- `plan.md`：数据模型与契约
- `tasks.md`：原子步骤，分后端任务与前端任务
- `implement.md`：代码约束（未评估通过前不写该 Task 的业务代码）
- `verify.md`：验证与失败时如何改规格

产品范围以 `docs/AI笔试题目.md` 为准。模拟达人在 `data/mock/`，其中哪些字段只供测试使用见 PLAN.md 的「模拟数据与测试答案」。Agent 运行时在 `backend/`。界面在 `frontend/`，视觉规范是 `frontend/DESIGN.md`。
