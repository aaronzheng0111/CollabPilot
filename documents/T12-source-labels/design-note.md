# 设计说明

数据来源是仓库里只读的 `data/mock/`（TikTok / Instagram JSON）。运行时经 `mock_store.load()` 剔除测试答案字段，界面和模型都看不到 `scenario_tags`、`expected_ai_signals`。达人行标 `[MOCK]`。

模型判断全部走 DeepSeek `deepseek-chat`，标 `[LLM]`：解析合作目标、适合度与主题、人数不足时的再搜策略、三封邀请草稿、跟进事项。应用层只做校验与锁定（已合作排除、引用必须是帖子原文、主题不符锁定、受众未知改判待确认、策略不得放开锁定字段），标 `[RULE]`。

任务状态存在 SQLite `backend/data/agent.db`：会话消息、活动、已确认渠道、草稿、跟进。同一目标指纹会复用活动，不重复推荐已排除者。

用户审核集中在「待你决定」：确认假设、接受不足人数、保存名单、排除创作者、确认渠道、保存草稿、批准草稿、记录/记下跟进。未批准返回 `approval_required`。

沟通渠道只展示 mock `contact` 里已有的值，未知就标「未知」，不编造。渠道确认和跟进都不发出站外消息；草稿区标 `[MOCK-SEND]`，没有发送按钮，也没有 `SENDING` 状态。

把模型拿掉之后：目标解析停在输入；判断步骤回复 `model_unavailable`、不产生候选名单；再搜返回 `model_strategy_required`、不自动改条件；草稿与跟进都不生成。规则层不会用粉丝数排序来凑一份名单。
