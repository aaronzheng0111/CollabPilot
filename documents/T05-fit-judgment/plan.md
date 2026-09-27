# Plan — 匹配判断

## 契约

模型通过对话输出 `Verdict[]` JSON。应用层 `validate_verdicts(verdicts, merged_creators)` 核对 evidence id、related_post_ids 与 `rank`，并计算 `recency`。

`sort_verdicts` 的顺序固定为：`fit` 按 `rank` 升序，然后 `pending`，然后 `unfit`。应用层不另行打分，不用粉丝数代替 `rank`。

不提供把测试答案字段注入提示词的代码路径。`get_creator` 在 T03 已剔除这些字段；本 Task 再次断言提示词模板不含它们。

模型不可用时 `evaluate_candidates` 抛出 `ModelUnavailable`，调用方把它转成 `model_unavailable` 回复，不走任何备用排序。

## 提示片段

- decision 只能是 fit / unfit / pending，必须引用 evidence id；fit 必须给出从 1 开始的连续 rank。
- 输入包含品牌 `key_features`、`exclusion_rules`、`target_audience`，以及每条帖子的 `age_days`。
- 排序原则：先看是否真实使用本品，再看近期持续发布相关内容，最后看受众与数据；信息缺失写进 `unknowns`，不猜。
- 对昵称或话题含关键词的账号，必须根据帖子内容填写 `topic_match`。

## 状态

保持 `EVALUATING`。名单是否足够不在本 Task 判定。

## 界面

- 主表增加 `decision`、`rank` 列；`decision` 用 `badge-pill` 显示中文。
- `frontend/components/evidence_panel.py`：次级区「判断依据」，样式为 `product-mockup-card-dark`（深色面板），帖子原文用 `code` 字体显示 id、`body-sm` 显示正文。

## 评测

`backend/tests/eval/test_fit_eval.py`，pytest 标记 `eval`，默认不跑。运行：`uv run pytest -m eval`。用 `load_oracle()` 对照结果，打印不一致的 creator_id 与模型理由。

## 模块

- `backend/src/collabpilot/campaign/verdict.py`
- `backend/config/prompts/campaign.md`
- `frontend/components/main_table.py`、`frontend/components/evidence_panel.py`
