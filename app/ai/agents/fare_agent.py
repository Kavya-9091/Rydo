from app.ai.agents.base import Agent
from app.ai.providers.base import LLMProvider
from app.ai.schemas import ChatMessage, LLMResponse


class FareAgent(Agent):
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(self, message: str) -> LLMResponse:
        return await self._llm.generate(
            [
                ChatMessage(role="system", content="Explain ride fares clearly and recommend an economical vehicle when appropriate."),
                ChatMessage(role="user", content=message),
            ]
        )
