# Specify — 合格不足与再搜

## 用户故事

严格筛选后合格人数少于目标 10。系统说明缺口。第二轮搜索条件必须来自 DeepSeek 提出的策略，应用层只校验是否合法。不得把已合作或关键词不符的人补进名单。没有模型策略时不自动改窗口。

## 验收标准

1. Given 首轮 `decision=fit` 且未被 T04/T06 排除的创作者人数小于 `target_count`，When 结束首轮，Then 状态变为 `INSUFFICIENT`，回复含「合格 {n}/10」和「缺口 {10-n}」，且 n 与名单长度一致。
2. Given 首轮 `window_days=30` 且没有模型输出的 `RetryStrategy`，When 请求第二轮，Then 返回 `error_code=model_strategy_required`，不创建 `index=2` 的搜索，也不把窗口改成某个写死的天数。
3. Given 第二次搜索结束，When 生成名单，Then 已合作创作者人数为 0，`keyword_mismatch` 人数为 0。
4. Given 第二轮合格人数仍小于 10，When 展示，Then 状态为 `CANDIDATES_READY`，并出现待决定项「是否接受当前人数」。在用户回答前不进入草稿。
5. Given 用户拒绝接受，When 处理该回答，Then 不把 unfit 或 pending 改成 fit 来补满 10。
6. Given 整个流程，When 计数搜索轮次，Then 自动再搜次数为 1。第三轮必须等用户明确要求。
7. Given 模型输出 `RetryStrategy`，且 `changes` 只含允许字段之一（`window_days`、`min_followers`、`keywords`），新值与首轮不同，并带非空 `reason`，When 校验通过，Then 第二轮按该策略搜索，`data_origin=real_model_output`，`model_name=deepseek-chat`，回复写出每个变更字段的旧值、新值和 `reason`。
8. Given 模型策略把 `include_own_brand` 或 `include_keyword_mismatch` 设为 true，或修改这两个字段，When 校验，Then 返回 `rule_locked`，不搜索。

## 边界

- 首轮期望数据下合格人数小于 10。规格不把具体人数写死为 6，避免数据和规则绑死；测试断言「小于 target_count」以及「第二轮仍小于 target_count」。
