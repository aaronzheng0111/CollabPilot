# Specify — 受众信息缺失

## 用户故事

平台没有受众画像时，系统显示未知，不填写年龄、性别或地区。这类创作者不因为人数不够而被当成适合直接塞进名单。

## 验收标准

1. Given `audience.status=unknown`，When 展示该创作者，Then 年龄、性别、地区、兴趣四处都显示「未知」，界面上看不到猜测值。
2. Given 同一条数据的 `age_range` 等字段为 null，When 渲染，Then 不把 null 显示成 0、空数组或「不限」。
3. Given 该创作者没有其他排除原因，When 模型判断，Then `decision=pending`，`unknowns` 含 `audience`。应用层若收到 `decision=fit` 且 `unknowns` 不含 `audience`，改为 `pending` 并记录 `rule_override=audience_unknown`。
4. Given 最终 fit 名单，When 用户尚未把某 pending 创作者手动标为可接受，Then 该创作者不在 fit 名单。
5. Given 展示，When 查看来源，Then 受众原文标 `[MOCK]`，覆盖判断标 `[RULE]`。

## 边界

- 受众未知不是硬性全员淘汰。它阻止自动进入 fit，仍可显示在待确认列表。
