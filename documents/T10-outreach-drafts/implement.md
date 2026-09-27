# Implement — 触达草稿

状态：`in_progress`（自动化用例 1–13 与 eval 用例 10 已通过；等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T13。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/drafts.py`
- `backend/src/collabpilot/infrastructure/campaign_store.py`（drafts 表）
- `backend/tests/unit/test_drafts.py`
- `backend/tests/eval/test_drafts_eval.py`（新）
- `backend/src/collabpilot/campaign/decisions.py`
- `frontend/components/draft_cards.py`（新）、`frontend/components/pending_decisions.py`
- `frontend/tests/test_draft_cards.py`（新）


## 本 Task 补充约束

正文引用必须来自工具返回的 title 或 caption 子串，校验时检查 cited_post_id，不检查营销措辞好坏。


## 实现记录

- `campaign/drafts.py`：`validate_drafts` 要求恰好 3 封、body/cited_post_id 互异、帖子属于该创作者、正文含 ≥8 字原文、`channel` 等于已确认渠道且正文含 `CHANNEL_LABELS`。失败整批不保存。少于 3 人或缺渠道时不调模型（`need_three_creators` / `channel_unconfirmed`）。
- 写草稿是 application 层独立调用，`temperature=creative_temperature`（0.85），提示词 `config/prompts/drafts.md`。校验通过后排队 `save_drafts`；`user_approved` 后写入 SQLite `drafts` 表，状态 `pending_review`，阶段 `DRAFT_REVIEW`。无 `SENDING`。`approve_draft` / `reject_draft` 只改状态。
- 前端：`draft_cards.py` feature-card；「生成 3 封草稿」secondary 触发生成并排队保存；保存后「待你决定」每封「审核草稿：{name}」含批准/退回；固定 caption「草稿不会发送 [MOCK-SEND]」。无发送按钮。

允许清单之外改动的文件：`application.py`、`campaign/goal.py`（`DRAFTING`/`DRAFT_REVIEW`、`draft_error`）、`campaign/retry.py`（阶段文案）、`campaign/workbench.py`、`tools/policy.py`、`tools/registry.py`、`tools/builtin/save_drafts.py`、`tools/builtin/approve_draft.py`、`settings.py`、`config/config.example.yaml`、`config/prompts/drafts.md`、`providers/mock.py`、`frontend/app.py`、`frontend/theme.py`。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
