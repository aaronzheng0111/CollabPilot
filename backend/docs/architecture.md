# Architecture

```text
CLI / FastAPI
      |
ApplicationService
      |
AgentRuntime ---- ToolRegistry / ToolPolicy
      |
ProviderRegistry
      |
Mock or OpenAI-compatible provider

ApplicationService ---- SQLiteSessionStore
```

The interfaces share one application service. Provider-specific request formats
stay behind provider adapters, and tool execution is bounded by policy and hard
runtime budgets.

