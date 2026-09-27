# Plan — 搜索与跨平台合并

## 数据模型

```text
PlatformAccountRef
  platform: tiktok | instagram
  creator_id: str
  handle: str
  follower_count: int

MergedCreator
  creator_id: str
  display_name: str
  platforms: str[]
  tiktok: object | null
  instagram: object | null

SearchMeta
  is_mock: true
  keywords: str[]
  window_days: int
  min_followers: int | null
  outside_window_hits: int
```

加载器启动时读两个 JSON 一次，剔除测试答案字段后建 `creator_id → MergedCreator` 索引。

## 测试答案字段

`ORACLE_FIELDS = scenario_tags, expected_ai_signals, product_usage_evidence[].product_relation, product_usage_evidence[].confidence`。

- `mock_store.load()` 返回的对象不含这些字段，是运行时唯一入口。
- `mock_store.load_oracle()` 只给 `backend/tests/` 用，返回 `creator_id → {scenario_tags, expected_ai_signals}`。
- 帖子时间统一换算为 `age_days`，基准日取 JSON `meta.generated_at`，不取系统当前时间，保证演示可重复。

## 契约

- `search_creators`：`risk_level=read`。关键词匹配范围：`display_name`、`content_topics`、`profile.signature` 或 `profile.biography`、窗口内帖子标题或 caption。大小写不敏感，子串匹配。账号在窗口内没有任何帖子则不返回。
- `get_creator`：`risk_level=read`。未知 id 返回 `ok=false`、`error_code=not_found`。
- 路径：仓库根目录 `data/mock/tiktok_creators.json` 与 `instagram_creators.json`。禁止读 `backend/data/`。

## 状态

调用搜索的前置状态：`PARSED`。成功后活动状态改为 `SEARCHING`。活动记录 `last_search: {keywords, window_days, min_followers, creator_ids}`，T07 用它作为首轮参数。

## 界面

- `components/main_table.py` 增加 `search_creators` 的行映射（见 PLAN.md「左表何时变化」）。
- 加载层：`running` 时在主表上叠一层半透明 `surface-soft`，文案「正在执行 search_creators…」。
- 主表上方一行 `caption` 字号小字：`关键词 … · 窗口 30 天 · 粉丝门槛 无`。

## 模块

- `backend/src/collabpilot/tools/builtin/search_creators.py`
- `backend/src/collabpilot/tools/builtin/get_creator.py`
- `backend/src/collabpilot/campaign/mock_store.py`
- `frontend/components/main_table.py`
