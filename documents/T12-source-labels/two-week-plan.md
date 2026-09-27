# 如果再给两周

## 1. 主题不符判断的稳定评测

为什么优先：演示里最能证明「不是关键词过滤器」的，是字幕剪辑 / 考试英语被判 unfit 且引用原文。现在靠一次 DeepSeek 调用，波动会让走查失败。
做什么：把 T06 eval 扩成固定 011–015 集合，每次跑 `uv run pytest -m eval -s tests/eval/test_topic_eval.py`，记录 mismatch 一致率。
如何验证：同一评测集连续 3 次，主题不符创作者集合与 oracle 的一致率 ≥ 80%，且每条仍带原文 quote。

## 2. 再搜策略可重复检查

为什么优先：人数不足时若策略乱跳，观众会以为在「调参凑数」。
做什么：固定首轮结果，对 T07 eval 断言 `changes` 只含 `window_days` / `min_followers` / `keywords`，并拒绝锁定字段。
如何验证：`uv run pytest -m eval -s tests/eval/test_retry_eval.py` 连续 3 次通过；人工走查「调整了什么」表旧值≠新值。

## 3. 草稿引用抽检

为什么优先：三封草稿是触达的唯一产出，引用一旦漂成套话，AI native 故事就塌了。
做什么：T10 eval 保存三封 body 与 `cited_post_id`，脚本检查 ≥8 字原文子串。
如何验证：`uv run pytest -m eval -s tests/eval/test_drafts_eval.py` 通过；两人对照帖子原文，引用一致率 3/3。

## 4. 无 Key 失败路径写成门禁

为什么优先：题目要看「拿掉模型工作流是否还在」。现在要靠手工拔 Key。
做什么：CI 增加不带 `DEEPSEEK_API_KEY` 的判断步，断言回复含 `model_unavailable` 且 `verdicts is None`。
如何验证：该 CI job 失败当且仅当产生了候选名单或写了草稿。
