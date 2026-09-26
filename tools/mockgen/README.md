# mockgen（可选造数工具）

本目录 **不是** CollabPilot Agent 或 Demo 的运行依赖。

- Agent 只读仓库根目录的 [`data/mock/*.json`](../../data/mock/)
- 这里的 TypeScript 脚本用来按 seed `20260926` **重新生成**那两个 JSON
- `types/*.ts` 只服务生成脚本的字段对齐，不会被 Python 后端 import

```bash
npm install
npm run generate:mock
```

输出：`../../data/mock/tiktok_creators.json`、`../../data/mock/instagram_creators.json`。

不改造数规则时，可以忽略整个 `tools/mockgen/`。
