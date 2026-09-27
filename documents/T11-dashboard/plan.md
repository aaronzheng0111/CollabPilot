# Plan — 工作台集成与视觉验收

## 布局

`frontend/app.py`：`st.columns([3, 2])`。

- 左栏：主表 `st.data_editor`；其下按 specify 用例 3 的顺序排列次级区块，每个区块来自 `frontend/components/` 的一个函数。
- 右栏：顶部工具状态栏，中部对话历史，底部 `st.chat_input`。

列宽左大于右。对话不在左栏。

## 契约

- 后端新增只读聚合 `ApplicationService.get_workbench_state(campaign_id) -> WorkbenchState`，页面每次 rerun 只调用它一次。
- 进程内调用 `ApplicationService`。`on_event` 写入 `st.session_state.tool_status` 与 `st.session_state.table_rows` 后 `st.rerun()`。
- `tool.started`：`tool_status.state=running`，`tool_status.name` 为工具名，左表显示加载层。
- `tool.completed` 且 `ok=true`：按 `documents/PLAN.md` 的工具到表格映射替换 `table_rows`，状态为 `succeeded`。
- `tool.completed` 且 `ok=false`：不替换 `table_rows`，状态为 `failed`。
- 页面读取 `WorkbenchState` 与事件，不直接解析达人 JSON。
- `CLARIFYING` 时忽略旧行，主表位置只渲染 `需求未完成，表格暂无筛选结果`。
- 启动命令写在 `frontend/README.md`。

## 视觉映射

来源：`frontend/DESIGN.md`。它描述的是 Claude 营销站，本页是产品工作台，取用规则如下。

| 工作台元素 | DESIGN.md 依据 | 取值 |
|------------|----------------|------|
| 页面底色 | `colors.canvas` | `#faf9f5`，写入 `theme.backgroundColor` |
| 主文字 | `colors.ink`、`colors.body` | 标题 `#141413`，正文 `#3d3d3a` |
| 次要文字 | `colors.muted`、`colors.muted-soft` | 说明 `#6c6a64`，脚注 `#8e8b82` |
| 分隔线与边框 | `colors.hairline` | `#e6dfd8`，写入 `theme.borderColor` |
| 次级区卡片 | `components.feature-card` | 底色 `surface-card #efe9de`，圆角 `rounded.lg 12px`，内边距 `spacing.lg 24px`（工作台比营销页紧凑，不用 32px） |
| 主表 | `colors.canvas` + `hairline` | 表底 `canvas`，表头 `surface-soft #f5f0e8`，行分隔 `hairline-soft #ebe6df` |
| 工具状态栏 | `components.product-mockup-card-dark` | 底色 `surface-dark #181715`，文字 `on-dark`，圆角 `rounded.lg`，内边距 `spacing.md 16px` |
| 判断依据面板 | `components.code-window-card` | 外层 `surface-dark`，帖子原文块 `surface-dark-soft #1f1e1b`，id 用等宽字体 |
| 状态圆点 | `accent-amber`、`success`、`error`、`on-dark-soft` | running `#e8a55a`，完成 `#5db872`，失败 `#c64545`，空闲 `#a09d96` |
| 批准按钮 | `components.button-primary` | 底色 `primary #cc785c`，按下 `primary-active #a9583e`，文字 `on-primary`，高 40px，圆角 `rounded.md 8px` |
| 其他按钮 | `components.button-secondary` | 底色 `canvas`，1px `hairline` 边框，文字 `ink` |
| 输入框 | `components.text-input`、`text-input-focused` | 底色 `canvas`，边框 `hairline`；聚焦时边框 `primary`，外圈 3px `primary` 15% 透明度 |
| 用户消息 | `colors.surface-soft` | 气泡底色 `#f5f0e8` |
| 助手消息 | `colors.canvas` + `hairline` | 无底色，1px 边框 |
| 决策胶囊 | `components.badge-pill` | 合适：`success` 圆点；待确认：`warning #d4a017` 圆点；不合适：`muted` 圆点 |

### 来源标签样式

| 标签 | 样式 |
|------|------|
| `[MOCK]` | `badge-pill`：底色 `surface-card`，文字 `ink` |
| `[RULE]` | `badge-pill` 变体：底色 `canvas`，1px `hairline` 边框，文字 `body` |
| `[LLM]` | 深色胶囊：底色 `surface-dark-elevated #252320`，文字 `on-dark`，后接等宽字体 `deepseek-chat` |
| `[MOCK-SEND]` | `badge-pill`：底色 `surface-soft`，文字 `muted` |

标签不用珊瑚色。珊瑚色只留给需要用户按下的批准动作。

### 字体

Copernicus 与 StyreneB 是授权字体，按 DESIGN.md「Note on Font Substitutes」替换，并补中文字形：

- 衬线（页面标题、区块标题，字重 400，字距 -0.3px）：`"Tiempos Headline", "Cormorant Garamond", "Noto Serif SC", "Songti SC", serif`
- 无衬线（正文、表格、按钮）：`Inter, "PingFang SC", "Noto Sans SC", -apple-system, "Segoe UI", sans-serif`
- 等宽（id、工具名、代码）：`"JetBrains Mono", ui-monospace, monospace`

字号：页面标题 `display-sm 28px`；区块标题 22px（`title-lg` 的字号，衬线字体）；正文与表格 `body-sm 14px`；标签 `caption 13px`。

### 不照搬的部分

- 不用 hero、96px 分段间距、珊瑚色通栏卡片、深色页脚；工作台区块间距用 `spacing.md 16px`。
- 不加 DESIGN.md 未定义的悬停样式，按钮只有默认与按下两态。
- 不引入第四种底色；cream、cream-card、dark 三种即全部。

### 落地方式

- `frontend/.streamlit/config.toml` 的 `[theme]`：`base="light"`、`primaryColor`、`backgroundColor`、`secondaryBackgroundColor`、`textColor`、`borderColor`、`font`、`headingFont`、`codeFont`、`baseRadius`。Streamlit 版本需支持这些键，实现时在 `backend/pyproject.toml` 的 `ui` extra 固定下限版本。
- `frontend/theme.py`：`inject_theme()` 用一段 CSS 覆盖主题键管不到的部分（状态栏、依据面板、胶囊、聊天气泡、批准按钮选择器）。CSS 中的色值只能引用上表。
- 字体文件不打包；网络不可用时退回系统字体，布局不变。

## 状态

展示 T02–T14 已定义的状态枚举，不新增活动状态名。工具状态仅 `idle | running | succeeded | failed`。

## 模块

- `backend/src/collabpilot/application.py`（`get_workbench_state`）
- `frontend/app.py`、`frontend/theme.py`、`frontend/.streamlit/config.toml`
- `frontend/components/*.py`
- `frontend/tests/test_workbench.py`、`frontend/tests/test_theme_tokens.py`
