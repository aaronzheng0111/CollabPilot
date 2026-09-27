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

打开 <http://localhost:8501>。默认 provider 是 `deepseek`，需要 `backend/.env` 里的 `DEEPSEEK_API_KEY`；没有 Key 时发消息会显示 `missing_api_key`。不用 Key 试页面，可以换成 mock 配置启动：

```bash
cd backend
sed -e 's/default_provider: deepseek/default_provider: mock/' \
    -e 's/default_model: deepseek-chat/default_model: collabpilot-mock/' \
    config/config.example.yaml > /tmp/collabpilot-mock.yaml
cd ../frontend
COLLABPILOT_CONFIG=/tmp/collabpilot-mock.yaml uv run --project ../backend --extra ui streamlit run app.py
```

会话 id 写在地址栏 `?session=`，带着它刷新或重新打开即可续聊。

## 测试

```bash
cd frontend
uv run --project ../backend --extra ui --extra dev pytest tests
```
