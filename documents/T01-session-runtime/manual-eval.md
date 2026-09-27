# 人工测评 — 会话与 DeepSeek 运行时

对应 `specify.md` 用例 1–11。自动化结果见 `verify.md`；本文件只记录人工操作与观察。M3、M5 的真实 Key 检查通过后，才能把 `implement.md` 状态改为 `verified`。

## 准备

- 已装 `uv`、`sqlite3`（macOS 自带）。命令均在仓库根目录下的 `backend/` 或 `frontend/` 执行。
- 生成一份不需要 Key 的 mock 配置（只写到 `/tmp`，不改仓库）：

```bash
cd backend
uv sync --extra dev --extra ui
sed -e 's/default_provider: deepseek/default_provider: mock/' \
    -e 's/default_model: deepseek-chat/default_model: collabpilot-mock/' \
    config/config.example.yaml > /tmp/collabpilot-mock.yaml
```

- 需要真实模型的用例（M3、M5 第 2 步）：在 `backend/.env` 写入 `DEEPSEEK_API_KEY=你的 key`。

## 用例

### M1 新会话落库（用例 1）

```bash
cd backend
S=$(COLLABPILOT_CONFIG=/tmp/collabpilot-mock.yaml uv run agent chat "你好" 2>/dev/null | grep -o 'session=[0-9a-f-]*' | cut -d= -f2); echo $S
sqlite3 data/agent.db "select role, coalesce(name,''), substr(content,1,30) from messages where session_id='$S' order by created_at;"
```

期望：打印一个 UUID；查询输出两行，依次为 `user||你好`、`assistant||我是 CollabPilot…`。

### M2 续聊与工具消息落库（用例 1、2）

接 M1 的 `$S`：

```bash
COLLABPILOT_CONFIG=/tmp/collabpilot-mock.yaml uv run agent chat "现在几点？" --session $S 2>/dev/null | tail -1
sqlite3 data/agent.db "select role, coalesce(name,'') from messages where session_id='$S' order by created_at;"
```

期望：第一条命令末行含 `tools=1`；查询共 5 行，依次为 `user|`、`assistant|`、`user|`、`tool|get_current_time`、`assistant|`。

有 Key 时再测模型是否真的看到历史：

```bash
S2=$(uv run agent chat "我叫小林，请记住。" 2>/dev/null | grep -o 'session=[0-9a-f-]*' | cut -d= -f2)
uv run agent chat "我叫什么名字？" --session $S2 2>/dev/null
```

期望：第二轮回复中出现「小林」。

### M3 默认命中 DeepSeek（用例 3，需要 Key）

```bash
uv run agent model test --provider deepseek --model deepseek-chat
uv run agent chat "你好" 2>/dev/null
```

期望：第一条输出 `OK deepseek responded successfully (deepseek-chat)`；第二条末尾含 `provider=deepseek model=deepseek-chat`（命令没有传 `--provider`）。

### M4 缺 Key 不回落 mock（用例 3 边界）

临时移走 `backend/.env`（或确认其中没有 `DEEPSEEK_API_KEY`）后：

```bash
env -u DEEPSEEK_API_KEY uv run agent chat "你好" 2>/dev/null; echo "exit=$?"
```

期望：输出 `missing_api_key: Missing API key environment variable: DEEPSEEK_API_KEY`，`exit=1`，没有 mock 的自我介绍。

### M5 错误信息不含密钥（用例 7）

1. 假 Key（会真实请求 DeepSeek 并被拒）：

```bash
DEEPSEEK_API_KEY=sk-invalid-manual-check uv run agent chat "你好" > /tmp/cp-out.txt 2>&1; cat /tmp/cp-out.txt | tail -1
grep -c "sk-invalid-manual-check" /tmp/cp-out.txt logs/agent.jsonl
```

期望：末行为 `provider_authentication_error: Provider authentication failed`；`grep` 输出 `/tmp/cp-out.txt:0` 与 `logs/agent.jsonl:0`。

2. 真实 Key：完成 M3 后执行 `grep -c "$(grep DEEPSEEK_API_KEY .env | cut -d= -f2)" logs/agent.jsonl`，期望 `0`。

### M6 页面骨架与主题（用例 8、9）

```bash
cd frontend
COLLABPILOT_CONFIG=/tmp/collabpilot-mock.yaml uv run --project ../backend --extra ui streamlit run app.py
```

浏览器打开 <http://localhost:8501>，窗口宽度不小于 1200px。

期望：
- 左栏约占 3/5：上方是只有表头 `creator_id / display_name / platforms`、内容为 empty 的表格，下方是米色卡片「暂无内容」。
- 右栏约占 2/5，自上而下：深色状态栏「空闲」、对话区（空）、输入框「描述你的合作目标」。
- 页面底色奶油色、标题为衬线字体；`frontend/.streamlit/config.toml` 中 `backgroundColor=#faf9f5`、`primaryColor=#cc785c`、`textColor=#141413`。

### M7 状态栏随工具变化（用例 6、10）

在 M6 页面输入 `现在几点？` 并发送。

期望：状态栏变为绿点 + `get_current_time` + 「完成」；对话区依次为用户消息、可折叠的「工具结果 · get_current_time」、助手回复。mock 下「运行中」一闪而过，用 DeepSeek 时可以看到工具名旁的转圈指示（该中间态已由自动化用例覆盖）。

### M8 重开页面续聊（用例 11）

复制 M7 后地址栏的完整 URL（含 `?session=`），关闭标签页后在新标签页打开。

期望：状态栏为「空闲」，对话区按原顺序显示上一轮的用户消息、工具结果和助手回复。

### M9 页面上的缺 Key 错误（用例 7 界面）

停止 M6 的服务，确认没有 Key 后不带 mock 配置启动：

```bash
env -u DEEPSEEK_API_KEY uv run --project ../backend --extra ui streamlit run app.py
```

发送 `你好`。期望：对话区出现红色提示 `missing_api_key: Missing API key environment variable: DEEPSEEK_API_KEY`，不出现助手回复。

### M10 自动化回归

```bash
cd backend && uv run --extra dev pytest
cd ../frontend && uv run --project ../backend --extra ui --extra dev pytest tests
```

期望：两组全部通过，且过程中不访问 `api.deepseek.com`。

## 记录

| 用例 | 结果（通过 / 失败 / 未测） | 实际输出或备注 |
|------|---------------------------|----------------|
| M1 | | |
| M2 | 通过 | 真实 Key：续聊能记住「小林」（用户完成真实 Key 验证） |
| M3 | 通过 | 用户完成真实 Key 验证：`model test` OK，默认 chat 命中 deepseek / deepseek-chat |
| M4 | | |
| M5 | 通过 | 第 2 步：真实 Key 未出现在 `logs/agent.jsonl`（用户完成真实 Key 验证） |
| M6 | | |
| M7 | | |
| M8 | | |
| M9 | | |
| M10 | | |

测评人：用户　　日期：2026-09-27
