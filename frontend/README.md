# Frontend

Streamlit 工作台放在本目录。布局以 `documents/PLAN.md` 为准，视觉以 [`DESIGN.md`](DESIGN.md) 为准。

- 左栏：数据表。行随最近一次成功的工具结果替换；工具运行时显示加载层。表下是「待你决定」、进度、判断依据、渠道、草稿、跟进等次级区块
- 右栏：顶部工具状态栏，中部对话历史，底部输入框
- 需求处于追问阶段时，左表不展示达人，只显示「需求未完成，表格暂无筛选结果」
- 与 `backend/` 的 Agent Runtime 同进程调用
- 不直接读 `data/mock/`，只读后端工具结果和活动存储；不在这里存放 JSON 或会话库

## 视觉

`DESIGN.md` 是 Claude 设计系统的原文（来源：[VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md/blob/main/design-md/claude/DESIGN.md)），只读。它描述的是营销站，工作台怎么取用见 `documents/T11-dashboard/plan.md` 的「视觉映射」：奶油色底、衬线标题、深色工具状态栏与判断依据面板、珊瑚色只用于批准按钮。

主题落在 `.streamlit/config.toml`，主题键管不到的样式在 `theme.py`。色值只能取自 `DESIGN.md` 的 `colors`。

## 启动

```bash
cd frontend
uv run --project ../backend --extra ui streamlit run app.py
```
