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

`scripts/scenario-overrides.ts` 在写文件前覆盖名字、帖子正文、发布时间和部分期望，保证名字不泄露结论、`creator_007`–`009` 只在放宽时间窗口后出现。改演示场景时改这个文件，重新生成后提交两个 JSON。

不改造数规则时，可以忽略整个 `tools/mockgen/`。
