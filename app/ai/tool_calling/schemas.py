from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]


class ToolExecutionContext(BaseModel):
    model_config = {"arbitrary_types_allowed": True}

    db: Any
    user: Any
    request_context: dict[str, Any] = Field(default_factory=dict)


class ToolResult(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] = Field(default_factory=dict)


ToolHandler = Callable[[dict[str, Any], ToolExecutionContext], ToolResult]
