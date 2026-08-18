from app.ai.tool_calling.schemas import ToolDefinition, ToolExecutionContext, ToolHandler, ToolResult


class ToolRegistry:
    def __init__(self) -> None:
        self._definitions: dict[str, ToolDefinition] = {}
        self._handlers: dict[str, ToolHandler] = {}

    def register(self, definition: ToolDefinition, handler: ToolHandler) -> None:
        self._definitions[definition.name] = definition
        self._handlers[definition.name] = handler

    def definitions(self) -> list[ToolDefinition]:
        return list(self._definitions.values())

    def execute(self, name: str, arguments: dict, context: ToolExecutionContext) -> ToolResult:
        handler = self._handlers.get(name)
        if handler is None:
            return ToolResult(success=False, message=f"Unknown tool: {name}")
        try:
            return handler(arguments, context)
        except Exception as exc:
            context.db.rollback()
            return ToolResult(success=False, message="Tool execution failed", data={"error": str(exc), "tool": name})
