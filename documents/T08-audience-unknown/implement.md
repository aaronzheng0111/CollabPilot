# Implement — 受众信息缺失

状态：`in_progress`（自动化用例 1–8 已通过；本 Task 无 eval；等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T07。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/audience.py`
- `backend/tests/unit/test_audience.py`
- `frontend/components/evidence_panel.py`、`frontend/components/main_table.py`
- `frontend/components/pending_list.py`（新）
- `frontend/tests/test_pending_list.py`（新）


## 本 Task 补充约束

不要根据昵称或语言推断受众。


## 实现记录

- `campaign/audience.py`：`audience_view` 在 `status=unknown` 时四项一律字符串「未知」（不是 null/0/空数组/不限），原文标 `[MOCK]`。`enforce_audience_unknown` 在模型给出 `fit` 时改 `pending`、`unknowns` 追加 `audience`、`rule_override=audience_unknown`、清 rank。`apply_audience_overrides` 在 T05/T06 校验之后、写入名单之前调用。`fit_creators` 只含仍为 `fit` 的人；`pending_creators` 与之分开，原因取 override 或「受众未知」/模型 reasons。源码不读 nickname/signature。
- `evaluate_candidates` 在 topic 校验后套用覆盖。020–023 即使被模型标 fit 也不进 `fit_creators`，出现在 pending 且带 `rule_override`。手动标可接受留给 T09。
- 前端：判断依据面板受众四格 + `audience.note` `[MOCK]`；主表 `audience` 列纯文本「受众未知」（dataframe 无法套胶囊，与 T05/T06 相同）；次级区 `pending_list.py`「待确认」列表与 fit 名单分开。

允许清单之外改动的文件：`campaign/verdict.py`（`rule_override`）、`application.py`、`campaign/workbench.py`、`frontend/app.py`、`frontend/theme.py`、`frontend/tests/test_evidence_panel.py`（020–023 先写成 fit 再走覆盖）。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
