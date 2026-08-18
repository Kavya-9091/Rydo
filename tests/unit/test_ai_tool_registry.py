from app.ai.tool_calling.schemas import ToolDefinition, ToolExecutionContext, ToolResult
from app.ai.tool_calling.registry import ToolRegistry


def test_registry_executes_registered_tool() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(name="hello", description="test", parameters={"type": "object", "properties": {}}),
        lambda arguments, context: ToolResult(success=True, message="ok", data={"echo": arguments["value"]}),
    )

    result = registry.execute("hello", {"value": 42}, ToolExecutionContext(db=object(), user=object()))

    assert result.success is True
    assert result.data["echo"] == 42


def test_registry_returns_error_for_unknown_tool() -> None:
    result = ToolRegistry().execute("missing", {}, ToolExecutionContext(db=object(), user=object()))

    assert result.success is False
    assert "Unknown tool" in result.message
