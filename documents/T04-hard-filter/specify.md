# Specify — 硬过滤

## 用户故事

搜索之后，系统用规则去掉已经与本品牌合作过的创作者，以及平台不在目标 `platforms` 里的账号。规则不调用模型。

## 输入 / 输出

- 工具 `apply_hard_filters(creator_ids: string[])`。
- 输出：`kept[]`、`removed[]`。`removed` 每项含 `creator_id`、`reason`（`own_brand_cooperated` 或 `platform_mismatch`）。

## 验收标准

1. Given 某创作者任一平台的 `cooperation_history` 里存在 `is_current_brand=true`，When 过滤，Then 该 `creator_id` 进入 `removed`，reason 为 `own_brand_cooperated`，其所有平台账号都不在 `kept`。
2. Given 某创作者 `scenario_tags` 含 `own_brand_cooperated` 但合作数组为空，When 过滤，Then 同样按 `own_brand_cooperated` 排除。
3. Given 目标 `platforms` 只有 `tiktok`，When 过滤一个只有 Instagram 账号的创作者，Then reason 为 `platform_mismatch`。
4. Given 目标含两个平台，When 过滤一个跨平台创作者且未合作本品牌，Then 该创作者在 `kept`，账号仍为两个。
5. Given 过滤结果，When 查看来源标记，Then 为 `[RULE]`，`data_origin` 不是 `real_model_output`。
6. Given 已合作创作者，When 后续人数不足，Then 本工具的规则定义不变：不得提供「放宽已合作」参数。

## 边界

- 不在本 Task 判断主题是否匹配。关键词不匹配留到 T06。
