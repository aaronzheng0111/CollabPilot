# Plan — 受众信息缺失

## 契约

`enforce_audience_unknown(verdict, audience) -> verdict`

当 `audience.status==unknown` 且 decision 为 fit：输出 decision=`pending`，`unknowns` 追加 `audience`，`rule_override=audience_unknown`。

渲染映射：null → 文案「未知」。禁止格式化成空字符串。

## 状态

不新增状态。待确认列表字段 `pending_creators[]` 与 `fit_creators[]` 分开。

## 模块

- `backend/src/collabpilot/campaign/audience.py`
