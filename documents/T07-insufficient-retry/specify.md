# Specify — 合格不足与再搜

## 用户故事

严格筛选后合格人数少于目标 10。系统说明缺口。第二轮搜索条件必须来自 DeepSeek 根据首轮结果提出的策略，应用层只校验是否合法。不得把已合作或主题不符的人补进名单。没有模型策略时不自动改窗口。第二轮仍不足时如实报告，由用户决定是否接受。

## 后端验收

1. Given 首轮 `decision=fit` 且未被 T04/T06 排除的创作者人数小于 `target_count`，When 结束首轮，Then 状态变为 `INSUFFICIENT`，回复含「合格 {n}/10」和「缺口 {10-n}」，且 n 与名单长度一致。
2. Given 首轮 `window_days=30` 且没有模型输出的 `RetryStrategy`，When 请求第二轮，Then 返回 `error_code=model_strategy_required`，不创建 `index=2` 的搜索，也不把窗口改成某个写死的天数。
3. Given 第二次搜索结束，When 生成名单，Then 已合作创作者人数为 0，`topic_rejected_ids` 中的人数为 0。
4. Given 第二轮合格人数仍小于 10，When 展示，Then 状态为 `CANDIDATES_READY`，`pending_decision=accept_short_list`。在用户回答前不进入草稿。
5. Given 用户拒绝接受，When 处理该回答，Then 不把 unfit 或 pending 改成 fit 来补满 10。
6. Given 整个流程，When 计数搜索轮次，Then 自动再搜次数为 1。第三轮必须等用户明确要求。
7. Given 模型输出 `RetryStrategy`，且 `changes` 只含允许字段之一（`window_days`、`min_followers`、`keywords`），新值与首轮不同，并带非空 `reason`，When 校验通过，Then 第二轮按该策略搜索，`data_origin=real_model_output`，`model_name=deepseek-chat`，回复写出每个变更字段的旧值、新值和 `reason`。
8. Given 模型策略把 `include_own_brand` 或 `include_keyword_mismatch` 设为 true，或修改这两个字段，When 校验，Then 返回 `rule_locked`，不搜索。
9. Given 请求策略时发给模型的输入，When 检查，Then 含首轮参数、合格人数、缺口、按原因汇总的未入选人数（已合作、主题不符、待确认各几位）和 `meta.outside_window_hits`；不含测试答案字段。
10. Given 单元测试注入策略 `window_days: 30→90`，When 在 mock 数据上执行第二轮，Then 新增候选包含 `creator_007`、`creator_008`、`creator_009`，且不含 `creator_011`–`creator_019`。
11. Given 标记为 `eval` 的 DeepSeek 集成测试，When 从首轮结果请求策略并执行第二轮，Then 策略通过校验，且第二轮合格人数大于首轮。策略原文与两轮人数写入 `verify.md` 备注。按 PLAN.md 的评测答案，期望 6/10 → 9/10。

## 前端验收

12. Given 已有一轮或两轮搜索，When 渲染次级区「进度」，Then 每轮一行：轮次、关键词、窗口天数、粉丝门槛、合格 n/10、缺口；当前状态（`INSUFFICIENT`、`RETRYING`、`CANDIDATES_READY`）以中文显示在区块标题。
13. Given 第二轮由模型策略触发，When 渲染，Then 有一张「调整了什么」表，每个变更字段一行：字段、旧值、新值、理由，表头带 `[LLM]` 与 `deepseek-chat`。
14. Given `pending_decision=accept_short_list`，When 渲染「待你决定」，Then 有一行「当前合格 {n} 位，少于目标 10 位，是否接受」，批准与拒绝两个按钮；此时草稿表为空。

## 边界

- 规格不把具体人数写成代码常量。单元测试断言「小于 target_count」以及「第二轮仍小于 target_count」的分支；具体 6 和 9 只出现在 eval 期望与演示脚本里。
