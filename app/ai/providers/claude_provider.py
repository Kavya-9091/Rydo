from anthropic import AsyncAnthropic

from app.ai.providers.base import LLMProvider, ToolCallingResponse
from app.ai.schemas import ChatMessage, LLMResponse, ToolCall
from app.ai.tool_calling.schemas import ToolDefinition
from app.core.settings import get_settings


class ClaudeProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.anthropic_model
        self._client = AsyncAnthropic(api_key=settings.anthropic_api_key)

    async def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> LLMResponse:
        system = "\n".join(message.content for message in messages if message.role == "system")
        user_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in {"user", "assistant"}
        ]
        response = await self._client.messages.create(
            model=self._model,
            system=system or None,
            messages=user_messages,
            max_tokens=1000,
            temperature=temperature,
        )
        content = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        return LLMResponse(content=content, metadata={"provider": "claude"})

    async def generate_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        temperature: float = 0.1,
    ) -> ToolCallingResponse:
        system = "\n".join(message.content for message in messages if message.role == "system")
        user_messages = [
            {"role": message.role, "content": message.content}
            for message in messages
            if message.role in {"user", "assistant"}
        ]
        response = await self._client.messages.create(
            model=self._model,
            system=system or None,
            messages=user_messages,
            tools=[{"name": tool.name, "description": tool.description, "input_schema": tool.parameters} for tool in tools],
            max_tokens=1000,
            temperature=temperature,
        )
        text = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")
        tool_calls = [
            ToolCall(id=block.id, name=block.name, arguments=block.input or {})
            for block in response.content
            if getattr(block, "type", None) == "tool_use"
        ]
        return ToolCallingResponse(content=text, metadata={"provider": "claude"}, tool_calls=tool_calls)
