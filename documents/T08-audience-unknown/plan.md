# Plan — 受众信息缺失

## 契约

`enforce_audience_unknown(verdict, audience) -> verdict`

当 `audience.status==unknown` 且 decision 为 fit：输出 decision=`pending`，`unknowns` 追加 `audience`，`rule_override=audience_unknown`。

`audience_view(audience) -> dict`：null → 文案「未知」。禁止格式化成空字符串。前端只渲染这个视图，不自己处理 null。

## 状态

不新增状态。待确认列表字段 `pending_creators[]` 与 `fit_creators[]` 分开，每个 pending 项带 `pending_reason`（取自 `rule_override` 或模型 `unknowns` / `reasons` 的首条）。

## 界面

- `evidence_panel.py` 增加受众区块，读 `audience_view`。
- 主表对 `rule_override=audience_unknown` 的行加「受众未知」胶囊。
- `frontend/components/pending_list.py`：次级区「待确认」列表。

## 模块

- `backend/src/collabpilot/campaign/audience.py`
- `frontend/components/evidence_panel.py`、`frontend/components/pending_list.py`
