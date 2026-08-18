from app.ai.providers.base import LLMProvider, ToolCallingResponse
from app.ai.schemas import ChatMessage, LLMResponse
from app.ai.tool_calling.schemas import ToolDefinition


class LocalFallbackProvider(LLMProvider):
    async def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> LLMResponse:
        user_message = next((message.content for message in reversed(messages) if message.role == "user"), "")
        return LLMResponse(
            content=_fallback_reply(user_message),
            metadata={"provider": "local_fallback", "reason": "llm_api_key_not_configured"},
        )

    async def generate_with_tools(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDefinition],
        temperature: float = 0.1,
    ) -> ToolCallingResponse:
        response = await self.generate(messages, temperature=temperature)
        return ToolCallingResponse(content=response.content, metadata=response.metadata, tool_calls=[])


def _fallback_reply(user_message: str) -> str:
    normalized = user_message.lower()
    if any(word in normalized for word in ["book", "ride", "go", "pickup", "destination"]):
        return (
            "I can help with that. For live AI booking, configure your OpenAI or Claude API key. "
            "For now, use the Book screen to choose pickup, destination, vehicle, and confirm the ride."
        )
    if "fare" in normalized or "price" in normalized:
        return "Fare estimates are available on the Book screen after you choose pickup, destination, and vehicle."
    if "payment" in normalized:
        return "You can pay for completed rides from the Payment screen."
    return "Hi. I am Rydo Assistant. I can help with rides, fares, trip status, payments, and support."
