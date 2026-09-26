# Specify — 来源标注与设计说明

## 用户故事

观看演示的人能区分模拟数据、规则、模型输出。设计说明一页内写清数据从哪来、哪些判断是模型做的、状态存在哪、哪些动作要人审核。

## 验收标准

1. Given 左表任意一条达人、帖子或 GPM，When 查看该行，Then 可见标签 `[MOCK]`。
2. Given 一条 Verdict 或 Draft，When 查看该行，Then 可见 `[LLM]` 和 `deepseek-chat`。
3. Given 已合作排除或关键词排除，When 查看该行，Then 可见 `[RULE]`。
4. Given 草稿区，When 查看，Then 可见 `[MOCK-SEND]` 或等价句子「不会发送」，且没有发送动作。
5. Given 仓库文件 `documents/T12-source-labels/design-note.md`，When 阅读，Then 文档覆盖六件事：数据来源、模型判断、状态存储、用户审核、沟通渠道、跟进合作；并写明渠道确认和跟进都不发出站外消息。全文不超过 900 字。
6. Given 界面文本，When 搜索 API Key，Then 页面源码与渲染文本都不包含密钥。

## 边界

- 不制作演示视频。
- 不改变 T04–T10 的判定结果，只加标签和说明文档。
