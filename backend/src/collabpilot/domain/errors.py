class AgentError(Exception):
    code = "agent_error"


class ConfigurationError(AgentError):
    code = "configuration_error"


class MissingApiKeyError(ConfigurationError):
    code = "missing_api_key"


class ProviderError(AgentError):
    code = "provider_error"


class ProviderAuthenticationError(ProviderError):
    code = "provider_authentication_error"


class ProviderRateLimitError(ProviderError):
    code = "provider_rate_limit_error"


class ProviderTimeoutError(ProviderError):
    code = "provider_timeout_error"


class RuntimeBudgetExceeded(AgentError):
    code = "runtime_budget_exceeded"


class ToolPolicyError(AgentError):
    code = "tool_policy_error"

