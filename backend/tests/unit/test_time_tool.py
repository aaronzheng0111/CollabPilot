from uuid import uuid4

from collabpilot.tools.base import ToolContext
from collabpilot.tools.builtin.time_tool import GetCurrentTimeTool


async def test_get_current_time() -> None:
    result = await GetCurrentTimeTool().execute(
        {"timezone": "Asia/Shanghai"},
        ToolContext(session_id=uuid4(), turn_id=uuid4()),
    )
    assert result.ok
    assert result.data["timezone"] == "Asia/Shanghai"


async def test_invalid_timezone() -> None:
    result = await GetCurrentTimeTool().execute(
        {"timezone": "Mars/Olympus"},
        ToolContext(session_id=uuid4(), turn_id=uuid4()),
    )
    assert not result.ok
    assert result.error_code == "invalid_timezone"

