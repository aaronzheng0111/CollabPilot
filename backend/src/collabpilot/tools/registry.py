from __future__ import annotations

from collabpilot.domain.errors import ConfigurationError
from collabpilot.tools.base import Tool
from collabpilot.tools.builtin.time_tool import GetCurrentTimeTool


class ToolRegistry:
    def __init__(self, enabled: list[str]):
        available: dict[str, Tool] = {
            GetCurrentTimeTool.name: GetCurrentTimeTool(),
        }
        unknown = set(enabled) - set(available)
        if unknown:
            raise ConfigurationError(f"Unknown enabled tools: {sorted(unknown)}")
        self._tools = {name: available[name] for name in enabled}

    def list(self) -> list[Tool]:
        return list(self._tools.values())

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def schemas(self) -> list[dict]:
        return [tool.schema() for tool in self.list()]

