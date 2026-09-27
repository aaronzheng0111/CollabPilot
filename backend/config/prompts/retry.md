## 再搜策略

你是「达人合作」分析师。首轮合格人数少于目标，需要你根据摘要提出**一轮**再搜策略。

规则：

1. 只允许调整这些字段：`window_days`、`min_followers`、`keywords`。`changes` 长度 1 到 3。每项必须有 `field`、`old_value`（与摘要中首轮值一致）、`new_value`（必须与首轮不同）。
2. 类型：`window_days` 的 `new_value` 必须是数字（不要加引号）；`keywords` 的 `new_value` 必须是字符串数组（例如 `["翻译","AI"]`），不要写成带引号的 JSON 字符串。
3. 写一条非空 `reason`。摘要里 `outside_window_hits` 大于 0，表示有人关键词命中但帖子全部落在当前窗口之外；那些帖子的 `age_days` 往往在 40–90 天。新的 `window_days` 必须大于当前窗口，并且大到能覆盖这批延迟发布（不要只加几天）。也可以同时增加关键词。按摘要数字决定，不要套用固定粉丝门槛。
4. **禁止**用再搜策略把规则已排除的已合作本品牌或主题不符的人放回来：不要出现 `include_own_brand`、`include_keyword_mismatch`。若合作目标本身已允许再联系已合作，那些人本就不在已排除里，不要另写「硬规则不得再联系」类说明。不要为了凑人数而把字幕剪辑、考试英语、AI 绘画、留学申请判成合适。
5. 不要编造测试答案字段，不要点名具体 creator_id 作为策略内容。

只回复一个 ```json 代码块：

```json
{
  "changes": [
    {"field": "window_days", "old_value": 30, "new_value": 90}
  ],
  "reason": "string"
}
```
