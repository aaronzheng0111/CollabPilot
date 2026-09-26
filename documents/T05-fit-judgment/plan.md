# Plan — 匹配判断

## 契约

模型通过对话输出 `Verdict[]` JSON。应用层 `validate_verdicts(verdicts, merged_creators)` 核对 evidence id，并核对 `rank`。

`sort_verdicts` 的顺序固定为：`fit` 按 `rank` 升序，然后 `pending`，然后 `unfit`。应用层不另行打分，不用粉丝数代替 `rank`。

不提供把 `expected_ai_signals` 注入提示词的代码路径。`get_creator` 在 T03 已省略该字段；本 Task 再次断言提示词模板不含 `expected_ai_signals`。

## 状态

保持 `EVALUATING`。名单是否足够不在本 Task 判定。

## 模块

- `backend/src/starter_agent/campaign/verdict.py`
- 提示片段：要求 decision 只能是 fit/unfit/pending，必须引用 evidence id；fit 必须给出从 1 开始的连续 rank
