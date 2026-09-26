# Mock 达人数据

Agent 与 Demo **只读本目录的 JSON**。不要在这里预置模型判断或触达草稿。

## 文件

| 文件 | 用途 |
|------|------|
| [`mock/tiktok_creators.json`](mock/tiktok_creators.json) | TikTok 账号、帖子、合作、GPM、搜索/连接快照 |
| [`mock/instagram_creators.json`](mock/instagram_creators.json) | Instagram 账号、媒体、合作、扩展 GPM、搜索/连接快照 |

同一达人用相同 `creator_id` 和 `display_name` 关联。顶层都有 `meta.is_mock: true`。

## Python 读取（Agent 用这个）

```python
import json
from pathlib import Path

mock = Path("data/mock")
tiktok = json.loads((mock / "tiktok_creators.json").read_text(encoding="utf-8"))
instagram = json.loads((mock / "instagram_creators.json").read_text(encoding="utf-8"))

by_id = {}
for c in tiktok["creators"]:
    by_id.setdefault(c["creator_id"], {})["tiktok"] = c
for c in instagram["creators"]:
    by_id.setdefault(c["creator_id"], {})["instagram"] = c
```

## 数据来源标记

| `data_origin` | 含义 |
|---------------|------|
| `mock_seed` / `mock_api_response` | JSON 内的模拟数据 |
| `real_model_output` | **不预置在 JSON**；Demo 运行时由 DeepSeek 生成再标记 |

缺失字段用 `null` 或 `"unknown"`，不编造。

## 规模（seed `20260926`）

TikTok 23 账号、Instagram 21 账号、34 个 Creator、10 个跨平台。合格候选首轮约 6、二轮合计约 9（仍不足 10）。含关键词干扰、已合作排除、受众未知、GPM 缺失等异常样本。

## 重新生成（可选）

**日常跑 Agent 不需要这一步。** 只有要改造数规则时才用。

生成脚本在 [`../tools/mockgen/`](../tools/mockgen/)（TypeScript）。输出仍是本目录的两个 JSON，**不是**给 Agent 编译用的类型包。

```bash
cd tools/mockgen && npm install && npm run generate:mock
```

字段细节、GPM 公式、异常测法见下方各节；局限：不解决真实平台授权，不实际发消息。

## GPM

```
gpm = gmv_30d / impressions_30d * 1000
```

已知：`gpm_origin: "mock_seed"`。缺失：`null` + `gpm_origin: "unknown"`。

## 异常场景怎么找

| 场景 | 怎么定位 |
|------|----------|
| 关键词命中但主题不匹配 | `scenario_tags` 含 `keyword_mismatch` |
| 合格不足 10 | 首轮约 6、二轮约 9 个强候选标签 |
| 受众缺失 | `audience.status === "unknown"` |
| GPM 缺失 | `metrics.gpm_origin === "unknown"` |
| 已合作本品牌 | `cooperation_history[].is_current_brand === true` |
| API 401 | `search_snapshots` 里 `api_error_tt_001` / `api_error_ig_001` |
