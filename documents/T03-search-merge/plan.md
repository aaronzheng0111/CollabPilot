# Plan — 搜索与跨平台合并

## 数据模型

```text
PlatformAccountRef
  platform: tiktok | instagram
  creator_id: str
  handle: str
  scenario_tags: str[]

MergedCreator
  creator_id: str
  display_name: str
  platforms: str[]
  tiktok: object | null
  instagram: object | null
```

加载器启动时读两个 JSON 一次，建 `creator_id → MergedCreator` 索引。

## 契约

- `search_creators`：`risk_level=read`。关键词匹配范围：`display_name`、`content_topics`、`profile.signature` 或 `profile.biography`、帖子标题或 caption。大小写不敏感。匹配方式为子串。
- `get_creator`：`risk_level=read`。未知 id 返回 `ok=false`、`error_code=not_found`。
- 路径：仓库根目录 `data/mock/tiktok_creators.json` 与 `instagram_creators.json`。禁止读 `backend/data/`。

## 状态

调用搜索的前置状态：`PARSED`。成功后活动状态改为 `SEARCHING`。

## 界面

无。

## 模块

- `backend/src/starter_agent/tools/builtin/search_creators.py`
- `backend/src/starter_agent/tools/builtin/get_creator.py`
- `backend/src/starter_agent/campaign/mock_store.py`
