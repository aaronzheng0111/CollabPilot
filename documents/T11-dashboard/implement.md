# Implement — 工作台集成与视觉验收

状态：`not_started`

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T14。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/application.py`（`get_workbench_state`）
- `backend/tests/integration/test_workbench_state.py`（新）
- `frontend/app.py`、`frontend/theme.py`、`frontend/.streamlit/config.toml`
- `frontend/components/*.py`（只调整装配与样式，不改业务含义）
- `frontend/tests/test_workbench.py`、`frontend/tests/test_theme_tokens.py`（新）
- `frontend/README.md`
- `backend/pyproject.toml` 的 optional extra `ui`（固定 streamlit 下限版本）
- `documents/T11-dashboard/screenshots/`（新）


## 本 Task 补充约束

`frontend/DESIGN.md` 只读。视觉取值只能来自 T11 `plan.md` 的「视觉映射」，映射表之外的新样式先改 `plan.md` 再写代码。

渲染测试可以用 Streamlit AppTest。若环境没有浏览器，AppTest 通过即算用例 2–19 自动化通过；用例 20、21 必须有截图。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
