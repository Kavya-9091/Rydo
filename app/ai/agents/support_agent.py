from app.ai.agents.base import Agent
from app.ai.rag.rag_service import RAGService
from app.ai.schemas import LLMResponse


class SupportAgent(Agent):
    def __init__(self, rag_service: RAGService) -> None:
        self._rag_service = rag_service

    async def run(self, message: str) -> LLMResponse:
        response, documents = await self._rag_service.answer(message)
        response.metadata["sources"] = [document.metadata for document in documents]
        return response
