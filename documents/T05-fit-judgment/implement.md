# Implement — 匹配判断

状态：`in_progress`（自动化用例 1–14 已通过，eval 用例 12 用真 Key 跑过 2 次均通过；等人工走查后改 `verified`）

## 约束

- Python 3.11。后端只改 `backend/`。界面只改 `frontend/`。模拟达人 JSON 只读 `data/mock/`，本 Task 不改 JSON 内容。
- 模型调用走现有 OpenAI-compatible Provider。演示 provider 为 `deepseek`，模型为 `deepseek-chat`。
- 不新增真实发送、真实平台 OAuth、小红书/B站/抖音。
- 工具输出标 `[MOCK]` 或 `[RULE]`。模型生成的判断和草稿标 `[LLM]`，并写入 `data_origin=real_model_output` 与 `model_name`。
- 禁止把 `expected_ai_signals` 当作模型结论展示。
- 前序 Task：T04。前序未 `verified` 时不得开始本 Task 的代码。

## 允许修改

- `backend/src/collabpilot/campaign/verdict.py`
- `backend/tests/unit/test_verdict.py`
- 活动提示词文件（新建 `backend/config/prompts/campaign.md`）
- `backend/tests/eval/test_fit_eval.py`（新）与 `pyproject.toml` 中 pytest 的 `eval` 标记
- `frontend/components/main_table.py`、`frontend/components/evidence_panel.py`（新）
- `frontend/tests/test_evidence_panel.py`（新）


## 本 Task 补充约束

单测使用手写 Verdict fixture 与 mock_store 样本，不调用 DeepSeek。eval 用例调用 DeepSeek，默认不跑。

评测不通过时改提示词，不加规则兜底，不读测试答案字段补救。

## 实现记录

- `campaign/verdict.py`（纯函数）：`Verdict`/`Recency`/`RejectedVerdict`/`VerdictBatch`；`validate_verdicts(raw, candidates, window_days, model_name)` 逐条校验：`evidence_ids` 与 `related_post_ids` 必须属于该创作者（否则该条 `evidence_not_found`），fit 缺任一为 `evidence_required`，非候选人 `not_in_candidates`，schema 不符 `schema_invalid`；fit 的 rank 必须是 1..n 连续不重复、非 fit 的 rank 必须 null，否则整批 `rank_invalid`（`accepted=[]`）。`recency` 由应用层按 `related_post_ids` 的 `age_days` 计算；`data_unknowns()` 在 GPM 全部未知 / 受众 unknown 时把 `gpm`、`audience` 并入 `unknowns`。`sort_verdicts` 只按 fit-rank → pending → unfit 排序，模块内没有按粉丝/GPM/命中数排序的代码（单测用正则锁定）。
- `candidate_payload()` 给模型看的精简视图（帖子只留 `post_id/age_days/text`，evidence 去掉测试字段，合作记录只留品牌/产品/是否本品/日期）；`render_campaign_prompt()` 渲染 `config/prompts/campaign.md`（占位符：品牌、产品、`key_features`、`exclusion_rules`=目标排除条件 ∪ mock brand 的 `exclusion_rules`、`target_audience`、`window_days`、`base_date`）；`render_candidates_message()` 把候选 JSON 放进 user 消息，以 `【候选创作者】` 开头。
- 判断步骤不走工具循环：`ApplicationService.evaluate_candidates(campaign, provider, model)` 单独调一次模型（`tools=[]`），提取 fenced JSON → 校验，整批失败重试一次；Provider 异常转 `ModelUnavailable`（`code=model_unavailable`）。`chat()` 在工具循环后若 `needs_evaluation(campaign)`（PARSED、stage=EVALUATING、有 `last_filter`、`verdicts is None`）自动运行，向 `on_event` 发 `tool.started/completed`（name=`evaluate_candidates`），把 `[LLM] <model>` 摘要或 `model_unavailable` / `verdicts_invalid` 说明追加到回复末尾。`apply_hard_filters` 每次写 `last_filter` 时把 `verdicts` 清空，所以 T07 再搜后会重新判断。
- `Campaign` 新增 `verdicts`、`verdict_rejected`、`verdict_model_name`、`verdict_error`。模型不可用时 `verdicts` 保持 None、stage 停在 `EVALUATING`，主表仍是 `kept` 行，没有任何备用名单。
- `ModelConfig.max_output_tokens=8192`（示例配置同步），`OpenAICompatibleProvider` 传 `max_tokens`：22 条 Verdict 的 JSON 超过 DeepSeek 默认 4096 输出上限会被截断。`campaign.md` 同时要求 reasons ≤ 2 条、evidence_ids ≤ 3。
- 评测调参记录：首次 eval 中 creator_005 被判 unfit，原因是 mock 数据里该条 `evidence.product_name="Mock竞品翻译"` 与帖子原文（LinguaGo）冲突、且半年前有已结束的竞品合作。按「只改提示词」的约束，在 `campaign.md` 补两条：以帖子原文为准、`product_name` 只是机器标注；竞品合作只有 `content_published_at` 距基准日 ≤ 90 天或帖子仍在推广竞品才算活跃。改后连续 2 次 eval 通过。
- `campaign/workbench.py`：`verdict_rows()`（fit 按 rank 置顶、其后 pending、unfit；被拒绝的创作者 decision 显示 `—` 排末尾，来源 `[MOCK] [RULE] [LLM]`）、`evidence_view()`（理由、引用帖子原文与 `age_days`、`recency`、`unknowns`、`model_name`）。
- 前端：`components/evidence_panel.py` 深色面板（`.cp-evidence`，`surface-dark`），用 `st.selectbox("查看判断依据")` 选创作者（默认 rank 1），未知项渲染为「未知：gpm」胶囊；主表 `decision` 列显示中文、`rank` 列；`app.py` 只在有 verdicts 时渲染面板。`goal.md` 加第 10 条：对话里不要自行点评/排序，判断由应用层附在回复末尾。
- Mock provider：识别 `【候选创作者】` 开头的判断请求，把每位候选人都回成 `pending`（引用其第一条 evidence id），不判 fit、不给 rank——只为无 Key 时跑通链路与界面，不冒充判断。
- 偏离说明：(1) `decision` 列在 `st.dataframe` 里是纯文本，胶囊样式只用在判断依据面板与未知项，因为 dataframe 单元格无法套 `badge-pill`；(2) 「选中主表中一位创作者」用面板上方的下拉框实现，AppTest 不支持 dataframe 行选择；(3) 关键词「翻译」的首轮候选里 011–015 只命中 011，其余四位需要模型选用其他关键词（如「AI」「语言」）才会进入名单。
- 允许清单之外改动的文件：`campaign/goal.py`、`campaign/workbench.py`、`application.py`、`settings.py`、`config/config.example.yaml`、`config/prompts/goal.md`、`providers/mock.py`、`providers/openai_compatible.py`、`providers/registry.py`、`tools/builtin/apply_hard_filters.py`、`tests/eval/conftest.py`、`frontend/app.py`、`frontend/theme.py`、`frontend/tests/test_main_table.py`、`frontend/tests/test_excluded_table.py`（适配 mock 链式判断）。


## 门禁

- 本 Task 状态为 `not_started` 或 `blocked` 时，禁止编写本 Task 的业务代码。
- `verify.md` 全部用例通过后，把状态改为 `verified`。
- 未 `verified` 时，禁止把下一个 Task 标为 `in_progress`。
- 验收失败：先改本目录 `specify.md`，再改 `plan.md` 与 `tasks.md`，最后才改代码。
