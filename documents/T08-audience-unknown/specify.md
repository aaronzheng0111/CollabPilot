# Specify — 受众信息缺失

## 用户故事

平台没有受众画像时，系统显示未知，不填写年龄、性别或地区。这类创作者不因为人数不够而被当成适合直接塞进名单。

## 后端验收

1. Given `audience.status=unknown`，When 生成展示用的受众视图，Then `age_range`、`gender`、`regions`、`interests` 四项的值都是字符串「未知」，不是 null、0、空数组或「不限」。
2. Given 该创作者没有其他排除原因，When 模型判断，Then `decision=pending`，`unknowns` 含 `audience`。应用层若收到 `decision=fit` 且 `unknowns` 不含 `audience`，改为 `pending` 并记录 `rule_override=audience_unknown`。
3. Given 最终 fit 名单，When 用户尚未把某 pending 创作者手动标为可接受，Then 该创作者不在 fit 名单。
4. Given 展示，When 查看来源，Then 受众原文标 `[MOCK]`，覆盖判断标 `[RULE]`。
5. Given mock 数据中的 `creator_020`–`creator_023`，When 走完判断与本规则，Then 四人都不在 `fit_creators`；模型判为 fit 的人出现在 `pending_creators` 且带 `rule_override=audience_unknown`。

## 前端验收

6. Given `audience.status=unknown` 的创作者被选中，When 渲染「判断依据」面板，Then 受众四项都显示「未知」，旁边一句平台原文 `audience.note`，标 `[MOCK]`；页面上看不到任何猜测值。
7. Given 存在 `rule_override=audience_unknown`，When 渲染主表，Then 该行 `decision` 为「待确认」，旁边有「受众未知」胶囊，标 `[RULE]`。
8. Given 有 pending 创作者，When 渲染次级区，Then 有「待确认」列表，每行写明待确认的原因（例如「受众未知」「相关内容只有 1 条」），与 fit 名单分开显示。

## 边界

- 受众未知不是硬性全员淘汰。它阻止自动进入 fit，仍可显示在待确认列表。
- 「把 pending 手动标为可接受」的操作在 T09 的保存流程中完成，本 Task 只保证默认不进入 fit。
