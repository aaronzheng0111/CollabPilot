# Implement — 合格不足与再搜

状态：`in_progress`（自动化用例 1–10、12–14 已通过，eval 用例 11 用真 Key 跑过 1 次通过；等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T06。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/retry.py`
- `backend/src/collabpilot/campaign/decisions.py`
- `backend/tests/unit/test_retry.py`
- `backend/tests/eval/test_retry_eval.py`（新）
- `frontend/components/progress_panel.py`（新）、`frontend/components/pending_decisions.py`
- `frontend/tests/test_progress_panel.py`（新）


## 本 Task 补充约束

合格人数统计单位是 creator_id，不是平台账号。


## 实现记录

- `campaign/retry.py`：`ALLOWED_FIELDS={window_days,min_followers,keywords}`，`LOCKED_FIELDS` 含 `include_own_brand`/`include_keyword_mismatch`。无策略 → `model_strategy_required`；越权字段 → `rule_locked`。`MAX_AUTO_RETRIES=1`。源码不写死 `window_days=90`。`_coerce_change` 把 `window_days` 转 int、把 JSON 字符串关键词收成 list。`append_search_round` / `qualified_lines`（「合格 n/10」「缺口 m」）/ `accept_short_list_label`。
- 再搜与判断一样走应用层，不进工具循环：`evaluate_candidates` 之后 `_maybe_search_retry`。不足且 `auto_retries<1` 时读 `config/prompts/retry.md` + `RoundSummary` JSON 要策略；合法则改搜索参数、再跑 `search_creators`+`apply_hard_filters`（发工具事件）、再判断。第二次仍不足 → `CANDIDATES_READY` + `pending_decision=accept_short_list`，草稿为空。拒绝该决定不把 unfit 改成 fit。
- 状态：`EVALUATING → INSUFFICIENT → RETRYING → CANDIDATES_READY`。`Campaign` 增 `search_rounds`、`retry_strategy`、`auto_retries`、`retry_error`、`drafts`。
- `retry.md`：只允许三字段；`keywords` 必须是数组；`outside_window_hits` 提示覆盖 40–90 天帖子。JSON 示例里 `new_value` 写 90 仅作提示，代码不读该数字。`campaign.md` 补：用本轮 `window_days` 算窗口内，不要用 30 天卡住放宽后的轮次。`goal.md` 第 11 条：再搜策略由应用层请求。
- 前端：`progress_panel.py` 进度表 +「调整了什么」；`pending_decisions.py` 用 `decision_label`（「当前合格 n 位，少于目标 10 位，是否接受」）。Mock provider 对【再搜策略】不给策略，UI fixture 保持首轮 22 行。
- eval（2026-09-27，`deepseek-chat`，1 次）：首轮 fit=6（001–006）；策略 `window_days` 30→90，`keywords` `['翻译']`→`['翻译','本地化','字幕翻译']`；第二轮 fit=8（001–004、006–009），缺口 2，`accept_short_list`。005 未进第二轮 fit。PLAN 期望 6→9，本轮满足「第二轮合格人数大于首轮」。

允许清单之外改动的文件：`campaign/goal.py`（阶段与 SearchRound/RetryStrategy）、`application.py`、`campaign/workbench.py`、`providers/mock.py`、`config/prompts/retry.md`、`config/prompts/goal.md`、`config/prompts/campaign.md`、`tools/builtin/search_creators.py`（keywords 字符串守卫）、`frontend/app.py`、T05/T03/T04 测试（mock 链式判断后 stage 可为 `INSUFFICIENT`；判断请求次数 +1）。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
