from app.ai.agents.base import Agent
from app.ai.providers.base import LLMProvider
from app.ai.schemas import ChatMessage, LLMResponse


class TripSummaryAgent(Agent):
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(self, message: str) -> LLMResponse:
        return await self._llm.generate(
            [
                ChatMessage(role="system", content="Create concise, factual trip summaries for a ride booking platform."),
                ChatMessage(role="user", content=message),
            ]
        )
