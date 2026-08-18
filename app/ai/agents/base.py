from abc import ABC, abstractmethod

from app.ai.schemas import LLMResponse


class Agent(ABC):
    @abstractmethod
    async def run(self, message: str) -> LLMResponse:
        raise NotImplementedError
