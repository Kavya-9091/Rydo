from abc import ABC, abstractmethod

from app.ai.schemas import ChatMessage, LLMResponse, ToolCall
from app.ai.tool_calling.schemas import ToolDefinition


class ToolCallingResponse(LLMResponse):
    tool_calls: list[ToolCall] = []


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> LLMResponse:
        raise NotImplementedError

    async def generate_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        temperature: float = 0.1,
    ) -> ToolCallingResponse:
        response = await self.generate(messages, temperature=temperature)
        return ToolCallingResponse(content=response.content, metadata=response.metadata, tool_calls=[])
