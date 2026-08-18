from openai import AsyncOpenAI

from app.ai.providers.base import LLMProvider, ToolCallingResponse
from app.ai.schemas import ChatMessage, LLMResponse, ToolCall
from app.ai.tool_calling.schemas import ToolDefinition
from app.core.settings import get_settings


class OpenAIProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.openai_model
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> LLMResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[message.model_dump() for message in messages],
            temperature=temperature,
        )
        return LLMResponse(content=response.choices[0].message.content or "", metadata={"provider": "openai"})

    async def generate_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        temperature: float = 0.1,
    ) -> ToolCallingResponse:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[message.model_dump() for message in messages],
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters,
                    },
                }
                for tool in tools
            ],
            tool_choice="auto",
            temperature=temperature,
        )
        message = response.choices[0].message
        return ToolCallingResponse(
            content=message.content or "",
            metadata={"provider": "openai"},
            tool_calls=[
                ToolCall(id=call.id, name=call.function.name, arguments=__import__("json").loads(call.function.arguments or "{}"))
                for call in message.tool_calls or []
            ],
        )
