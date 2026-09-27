# Implement — 来源标注与提交材料

状态：`in_progress`（自动化用例 1–12 已通过；用例 9 计时走查与完整 DeepSeek 演示待人工）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T11。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `frontend/app.py`、`frontend/components/source_badge.py`（新）
- `frontend/tests/test_source_labels.py`（新）
- `backend/src/collabpilot/interfaces/cli.py`
- `backend/tests/integration/test_demo_reset.py`（新）
- `documents/T12-source-labels/design-note.md`、`demo-script.md`、`two-week-plan.md`（实现本 Task 时才写）
- 根目录 `README.md`（「快速开始」一节）


## 本 Task 补充约束

三份文档在规格阶段不要创建。设计说明不超过 900 字；两周计划不超过一页；演示脚本总时长 180–300 秒。

文档中出现的命令、文件路径、错误码都要在当时代码中真实存在，写完后逐条执行或检索核对。

## 实现记录

- CLI：`agent demo reset` 调用 `reset_demo_tables`，DELETE 会话/活动/渠道/草稿/跟进表行，不删库、不碰 `data/mock/`。
- 前端：`source_badge.py` 映射 origin → `[MOCK]`/`[LLM]`/`[RULE]`；标题下图例四类；草稿/跟进 caption 固定 `[MOCK-SEND]`。
- 文档：`design-note.md`（<900 字）、`demo-script.md`（10 步 240s + 无 Key 附录）、`two-week-plan.md`（4 项可重复验证）、根 README「快速开始」6 条命令。

## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
