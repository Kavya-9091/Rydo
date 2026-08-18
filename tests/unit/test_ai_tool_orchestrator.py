import pytest

from app.ai.providers.base import LLMProvider, ToolCallingResponse
from app.ai.schemas import ChatMessage, LLMResponse, ToolCall
from app.ai.tool_calling.orchestrator import RideAssistantOrchestrator
from app.ai.tool_calling.registry import ToolRegistry
from app.ai.tool_calling.schemas import ToolDefinition, ToolExecutionContext, ToolResult


class FakeToolCallingLLM(LLMProvider):
    async def generate(self, messages: list[ChatMessage], temperature: float = 0.2) -> LLMResponse:
        return LLMResponse(content="Your fare is INR 123.", metadata={})

    async def generate_with_tools(self, messages, tools, temperature=0.1) -> ToolCallingResponse:
        return ToolCallingResponse(
            content="",
            metadata={},
            tool_calls=[ToolCall(id="call-1", name="estimate_fare", arguments={"vehicle_type": "sedan"})],
        )


@pytest.mark.asyncio
async def test_orchestrator_executes_tool_and_returns_final_response() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(name="estimate_fare", description="Estimate fare", parameters={"type": "object", "properties": {}}),
        lambda arguments, context: ToolResult(success=False, message="Missing required fare details"),
    )

    response = await RideAssistantOrchestrator(FakeToolCallingLLM(), registry).run(
        "estimate fare",
        ToolExecutionContext(db=object(), user=object()),
    )

    assert response.content == "Your fare is INR 123."
    assert response.metadata["tool_results"][0]["tool"] == "estimate_fare"
    assert response.metadata["orchestration_steps"][0]["name"] == "receive_message"
    assert response.metadata["orchestration_steps"][-1]["name"] == "generate_final_response"
