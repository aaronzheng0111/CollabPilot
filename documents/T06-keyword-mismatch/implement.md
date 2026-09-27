# Implement — 关键词命中但主题不符

状态：`in_progress`（自动化用例 1–9 已通过，eval 用例 6 用真 Key 跑过 1 次通过；等人工走查后改 `verified`）

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

## 实现记录

- `campaign/topic_match.py`（纯函数）：`validate_topic_verdicts` 在 T05 `validate_verdicts` 之后运行。`mismatch` 且非 `unfit` → `topic_conflict`；`unclear` 且 `fit` 同样 `topic_conflict`。`mismatch` 要求非空 `mismatch_topic`、`quote` ≤80 字且是 `evidence_ids` 中某条 `recent_posts` 标题/caption 的原文子串，否则 `quote_not_found`。`lock_topic_rejections` 把 mismatch `creator_id` 追加到 `Campaign.topic_rejected_ids` 并写 `rule=true` 的 `TopicLock`。`fit_creator_ids` 只取 `decision=fit` 且不在锁定名单中的人，源码不含 GPM 升级路径。
- 交给模型前减去 `topic_rejected_ids` 与 T04 `own_brand_cooperated`：`search_creators` 从本轮结果里摘掉锁定 id，display 写「已有 N 位此前判定不符，未重复评估」；`evaluate_candidates` 同样不把这些人放进候选 JSON。写入名单前先 topic 校验再 lock。
- `campaign.md` 补强：昵称/话题命中不算相关，字幕剪辑/应试/AI 绘画/留学申请必须 `mismatch`，GPM 不能把不符改成 fit。
- 前端：主表 `topic` 列纯文本「主题不符：{mismatch_topic}」（dataframe 单元格无法套胶囊，与 T05 相同）；判断依据面板用 `cp-pill` 显示主题不符与 `[LLM]` quote/帖子 id，下方「已锁定，不再推荐」`[RULE]`，无「加回名单」。
- eval（2026-09-27，`deepseek-chat`，1 次）：001–006 全 `match`+`fit`；011–015 全 `mismatch`+`unfit`（影视字幕剪辑 / 语言考试 / AI绘画 / 留学申请 / 语言考试），`rejected=[]`，锁定 011–015。

允许清单之外改动的文件：`campaign/goal.py`（`topic_rejected_ids` / `TopicLock`）、`campaign/verdict.py`（`RejectCode` 增加 topic 两项）、`application.py`、`campaign/workbench.py`、`tools/builtin/search_creators.py`、`frontend/theme.py`、`tests/eval/test_fit_eval.py`（`evaluate_candidates` 现返回 skipped 计数）。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
