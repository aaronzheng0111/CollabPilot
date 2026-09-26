# Mock 数据说明

本目录为「AI 达人合作工作台 Demo」提供可直接读取的模拟数据。**不要在此预置真实模型判断或触达草稿。**

## 核心文件

| 文件 | 用途 |
|------|------|
| `mock/tiktok_creators.json` | TikTok 平台账号资料、帖子、合作、GPM、搜索/连接快照 |
| `mock/instagram_creators.json` | Instagram 平台账号资料、媒体、合作、扩展 GPM、搜索/连接快照 |

后续 Demo **直接读取这两个 JSON**，按 `creator_id` 合并跨平台达人。

## 如何读取

从仓库根目录：

```python
import json
from pathlib import Path

mock = Path("data/mock")
tiktok = json.loads((mock / "tiktok_creators.json").read_text())
instagram = json.loads((mock / "instagram_creators.json").read_text())

by_id = {}
for creator in tiktok["creators"]:
    by_id.setdefault(creator["creator_id"], {})["tiktok"] = creator
for creator in instagram["creators"]:
    by_id.setdefault(creator["creator_id"], {})["instagram"] = creator
```

类型定义见 `tools/mockgen/types/`：

- `domain.ts` — 通用领域类型、`data_origin`、产品关系枚举
- `tiktokApi.ts` — TikTok 接口 attributes 对齐
- `instagramApi.ts` — Instagram Graph API 命名对齐

## 重新生成（确定性）

```bash
cd tools/mockgen && npm run generate:mock
```

脚本：`tools/mockgen/scripts/generate-mock-data.ts`  
输出：`data/mock/`  
Seed：`20260926` — 每次生成结果一致。生成后自动打印统计并校验验收清单。

## 模拟数据 vs 真实模型输出

| 标记 | 含义 | 出现位置 |
|------|------|----------|
| `data_origin: "mock_seed"` | 种子生成的模拟达人/帖子/合作/GPM | 两个 JSON 内几乎全部业务字段 |
| `data_origin: "mock_api_response"` | 模拟平台 API 响应（含成功与 401） | `search_snapshots`、`account_connection_snapshots` |
| `data_origin: "real_model_output"` | **真实模型输出** | **不在 JSON 中预置**；Demo 运行时写入 |

顶层 `meta.is_mock: true`，并含 `mock_disclaimer`。

Demo 运行时若调用模型生成判断/草稿，必须附加：

```json
{
  "data_origin": "real_model_output",
  "model_name": "claude-sonnet-4-20250514",
  "generated_at": "2026-09-26T10:00:00Z"
}
```

> 以下为真实模型输出示例，非 Mock 数据。  
> （示例仅说明标记格式，勿写入 `mock/*.json`。）

## 字段对齐

### TikTok

`profile` 对齐 TikTok User attributes：`uid`、`unique_id`、`nickname`、`sec_uid`、`signature`、`follower_count`、`heart_count`、`video_count` 等。  
`recent_posts[]` 对齐 Video attributes：`video_id`、`share_url`、`create_time`、`stats.play_count` / `digg_count` 等。  
GPM 使用 `metrics.video_gpm`。

### Instagram

`profile` 对齐 Instagram Graph API User：`ig_id`、`username`、`name`、`biography`、`followers_count`、`media_count` 等。  
`recent_posts[]` 对齐 Media：`id`、`media_url`、`caption`、`permalink`、`media_type`、`like_count`、`comments_count`、`timestamp`。  
原生无 GPM，使用扩展字段 `metrics.gpm_30d`。

## GPM 计算

```
gpm = gmv_30d / impressions_30d * 1000
```

- 已知：`gpm_origin: "mock_seed"`，货币 `USD` / `CNY`
- 缺失：`gmv_30d` / `impressions_30d` / `video_gpm|gpm_30d` 为 `null`，`currency: "unknown"`，`gpm_origin: "unknown"`
- GPM 缺失降权，不编造、不直接排除；GPM 高但主题不匹配仍排除

跨平台 GPM 差异明显的 Creator（可用 `creator_id` 对比）：`creator_001`、`creator_008`、`creator_010`。

## 跨平台合并

同一达人在两个 JSON 中共享：

- `creator_id`（如 `creator_001`）
- `display_name`

至少 8 个跨平台 Creator（当前 seed 为 10 个：`creator_001`–`creator_010`）。

## 异常场景如何测试

| 场景 | 如何找数据 |
|------|------------|
| 关键词命中但主题不匹配 | `scenario_tags` 含 `keyword_mismatch`（≥5） |
| 合格不足 10 位 | `strong_candidate` 首轮 6 + `strong_candidate_round2` 共 9，仍不足 10 |
| 受众缺失 | `audience.status === "unknown"` 或 tag `audience_unknown` |
| GPM 缺失 | `metrics.gpm_origin === "unknown"` |
| 已合作本品牌 | `cooperation_history[].is_current_brand === true` |
| 竞品排他未知 | tag `competitor_exclusivity_unknown`，`exclusivity_risk: "possible"` |
| API 授权失败 | `search_snapshots` 中 `api_error_tt_001` / `api_error_ig_001`（401） |

首轮严格筛选约 6 位；二轮放宽后最多 9 位。系统应说明缺口原因（已合作、关键词干扰、受众缺失等），**不放宽「已合作本品牌必须排除」**，不把关键词干扰项塞进名单。

## 当前 seed 规模（20260926）

- TikTok 账号 ≥ 20，Instagram 账号 ≥ 20
- 不同 Creator ≥ 30，跨平台 ≥ 8
- 完全合格候选 ≤ 9（首轮 6，二轮合计 9）
- GPM 已知 ≥ 15，GPM 缺失 ≥ 5
- 模拟 API 错误 ≥ 2

## 局限

- **不解决**真实第三方平台（TikTok / Instagram）OAuth 授权
- **不实际发送**私信或邮件（触达仅 Demo 模拟）
- JSON 内 URL 均为 `mock://` 占位，无真实 CDN / 主页
- 受众画像、GPM、竞品排他条款在真实世界常需商业授权；此处仅模拟结构与缺失语义
