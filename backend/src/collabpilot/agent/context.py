from pathlib import Path

from collabpilot.domain.models import Message


class ContextBuilder:
    def __init__(self, identity_path: Path, system_prompt_path: Path):
        self.identity_path = identity_path
        self.system_prompt_path = system_prompt_path

    def build(self, history: list[Message]) -> list[Message]:
        identity = self.identity_path.read_text(encoding="utf-8")
        template = self.system_prompt_path.read_text(encoding="utf-8")
        system = template.replace("{identity}", identity)
        return [Message(role="system", content=system), *history]

