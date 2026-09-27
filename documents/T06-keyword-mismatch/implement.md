# Implement — 关键词命中但主题不符

状态：`not_started`

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T05。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/topic_match.py`（新）
- `backend/config/prompts/campaign.md`
- `backend/tests/unit/test_topic_match.py`（新）
- `backend/tests/eval/test_topic_eval.py`（新）
- `frontend/components/main_table.py`、`frontend/components/evidence_panel.py`
- `frontend/tests/test_evidence_panel.py`


## 本 Task 补充约束

主题是否相符只由模型判定。应用层禁止用关键词表、正则或 `scenario_tags` 判定主题不符。

最终候选的写入函数必须先调用 `validate_topic_verdicts`，再调用 `lock_topic_rejections`。校验失败的整条判断不进入名单，并在回复中告知哪位创作者需要重新判断。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
