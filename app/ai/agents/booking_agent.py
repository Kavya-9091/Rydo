from app.ai.agents.base import Agent
from app.ai.prompts.booking_prompts import BOOKING_SYSTEM_PROMPT
from app.ai.providers.base import LLMProvider
from app.ai.schemas import ChatMessage, LLMResponse


class BookingAgent(Agent):
    def __init__(self, llm: LLMProvider) -> None:
        self._llm = llm

    async def run(self, message: str) -> LLMResponse:
        return await self._llm.generate(
            [
                ChatMessage(role="system", content=BOOKING_SYSTEM_PROMPT),
                ChatMessage(role="user", content=message),
            ]
        )
