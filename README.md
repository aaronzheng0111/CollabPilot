# CollabPilot

AI 达人合作工作台 Demo。品牌用自然语言描述合作目标；Agent 搜索模拟达人、判断适合度、不足时调整再搜，用户审核后生成触达草稿。

## 目录（本阶段已提交）

| 目录 | 职责 |
|------|------|
| [`data/`](data/) | 模拟达人 JSON（TikTok / Instagram）与读取说明 |
| [`tools/mockgen/`](tools/mockgen/) | 确定性 Mock 生成脚本与 TypeScript 类型 |
| [`documents/`](documents/) | T01–T12 规格包。一次只实现一个 Task，Verify 通过后再做下一个 |

详细字段与异常场景见 [`data/README.md`](data/README.md)。

## 重新生成

```bash
cd tools/mockgen && npm install && npm run generate:mock
```

Seed：`20260926`（确定性，重复生成结果一致）。输出：`data/mock/tiktok_creators.json`、`data/mock/instagram_creators.json`。

---

## Sprint 0 — 模拟数据

第一步只交付可读取的平台模拟数据，不做 UI / Agent。品牌默认 **LinguaGo AI 翻译**；场景目标找 10 位创作者、排除已合作、为 3 位准备待审邀请草稿。

当前规模（seed `20260926`）：TikTok 23 账号、Instagram 21 账号、34 个 Creator、10 个跨平台（`creator_001`–`010`）。完全合格首轮 6 → 二轮合计 9（仍不足 10）。

### Stories（逐条）

**S0-01 双平台主 JSON**  
产出 `data/mock/tiktok_creators.json` 与 `data/mock/instagram_creators.json`；后续 Demo 只读这两个文件。

**S0-02 模拟与模型输出分离**  
JSON 内一律 `data_origin: mock_seed | mock_api_response`；不预置判断或触达草稿。真实模型输出运行时标 `real_model_output` + `model_name`。

**S0-03 缺失不编造**  
受众 / GPM 等缺失用 `null` 或 `"unknown"`，不 silently 补全。

**S0-04 Meta 声明**  
顶层 `meta`：`is_mock: true`、`platform`、`schema_version`、`seed`、`mock_disclaimer`。

**S0-05 字段对齐平台 API**  
TikTok 对齐 User / Video attributes；Instagram 对齐 Graph API User / Media；IG 无原生 GPM，用扩展 `metrics.gpm_30d`。

**S0-06 跨平台合并键**  
同一达人共用 `creator_id` + `display_name`；跨平台 ≥ 8（当前 10）。

**S0-07 规模门槛**  
每平台账号 ≥ 20；不同 Creator ≥ 30；两平台账号合计 ≥ 40。

**S0-08 确定性生成**  
`tools/mockgen/scripts/generate-mock-data.ts`，seed `20260926`，生成后自动校验验收清单。

**S0-09 合格不足 10（异常）**  
完全合格 ≤ 9；首轮约 6、二轮约 9；不放宽「已合作本品牌必须排除」，不把关键词干扰塞进名单。

**S0-10 关键词命中但主题不匹配（异常）**  
≥ 5 个 `keyword_mismatch` Creator，`expected_decision_hint: reject`（仅测试预言，不作模型判断展示）。

**S0-11 已合作本品牌**  
≥ 4 个 Creator，`cooperation_history[].is_current_brand === true`，整 Creator（两平台）应排除。

**S0-12 受众信息缺失（异常）**  
≥ 4 个 `audience.status === "unknown"` / tag `audience_unknown`。

**S0-13 GPM 已知与缺失**  
GPM 已知 ≥ 15 条账号；缺失 ≥ 5（`gpm_origin: "unknown"`）；公式 `gmv_30d / impressions_30d * 1000`；跨平台 GPM 差异大 ≥ 3（如 `001` / `008` / `010`）。

**S0-14 产品关系与竞品**  
类似产品/竞品使用者 ≥ 6；竞品深度合作中 ≥ 2（`exclusivity_risk`）；竞品合作已结束 ≥ 2；另含差评者 / 好评者 / 多产品中立测评等标签。

**S0-15 新人与合作效率**  
新人无历史但产品相关 ≥ 4；有合作效率数据（样品→发布周转等）≥ 6。

**S0-16 模拟搜索与账号连接**  
顶层 `search_snapshots` / `account_connection_snapshots`；含 ≥ 2 条 401 授权失败（`api_error_tt_001` / `api_error_ig_001`）。

**S0-17 类型与文档**  
`tools/mockgen/types/{domain,tiktokApi,instagramApi}.ts` + [`data/README.md`](data/README.md)（读取、合并、GPM、异常测法、局限）。
