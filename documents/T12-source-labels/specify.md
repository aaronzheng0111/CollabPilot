# Specify — 来源标注与提交材料

## 用户故事

观看演示的人能区分模拟数据、规则、模型输出。评审拿到仓库后，能照着启动说明跑起来，照着演示脚本在 3〜5 分钟内看完核心流程，并读到一页设计说明和「再给两周」的计划。

## 后端验收

1. Given 已跑过演示的本地库，When 执行 `uv run agent demo reset`，Then 清空 `backend/data/agent.db` 中的会话、活动、渠道、草稿、跟进表，不改 `data/mock/`；再次打开页面是空会话。

## 前端验收

2. Given 左表任意一条达人、帖子或 GPM，When 查看该行，Then 可见标签 `[MOCK]`。
3. Given 一条 Verdict、RetryStrategy、Draft 或 FollowUp，When 查看，Then 可见 `[LLM]` 和 `deepseek-chat`。
4. Given 已合作排除、主题不符锁定或受众未知改判，When 查看该行，Then 可见 `[RULE]`。
5. Given 草稿区，When 查看，Then 可见 `[MOCK-SEND]` 或等价句子「不会发送」，且没有发送动作。
6. Given 界面文本，When 搜索 API Key，Then 页面源码与渲染文本都不包含密钥。
7. Given 页面顶部，When 查看，Then 有一行图例说明四类标签的含义：`[MOCK]` 模拟数据、`[RULE]` 应用层规则、`[LLM]` DeepSeek 实时输出、`[MOCK-SEND]` 不会发送。

## 提交材料验收

8. Given `documents/T12-source-labels/design-note.md`，When 阅读，Then 覆盖六件事：数据来源、模型判断、状态存储、用户审核、沟通渠道、跟进合作；写明渠道确认和跟进都不发出站外消息；列出「把模型拿掉后哪一步会停下」。全文不超过 900 字。
9. Given `documents/T12-source-labels/demo-script.md`，When 阅读，Then 按 T11 用例 21 的 10 步组织，每步写明：画面、讲解词、要让观众看到的判断及其来源标签、预计秒数；总时长在 180–300 秒之间。脚本至少包含三处专门展示：关键词命中但主题不符的原文引用、合格不足时模型提出的策略与旧值新值、受众未知显示「未知」。
10. Given 演示脚本，When 查找「拿掉模型」演示，Then 有一步说明如何在不配置 Key 的情况下重跑并看到 `model_unavailable`，说明页面此时不产生候选名单。
11. Given `documents/T12-source-labels/two-week-plan.md`，When 阅读，Then 不超过一页，列出 3–5 项优先事项；每项写明为什么优先、做什么、如何验证有效，验证方式是可重复的检查（例如评测集上的一致率、人工评分的双人一致、演示走查的步骤数），不是主观描述。
12. Given 仓库根目录 `README.md`，When 按「快速开始」一节操作，Then 从克隆到打开页面不超过 6 条命令；包含配置 `DEEPSEEK_API_KEY`、安装依赖、启动页面、运行单元测试、运行 `eval` 评测、重置演示数据；并链接设计说明、演示脚本、两周计划。

## 边界

- 不制作演示视频。演示脚本是题目允许的「等效的现场演示脚本」。
- 不改变 T04–T10 的判定结果，只加标签、重置命令和说明文档。
