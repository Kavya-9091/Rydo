from app.ai.agents.booking_agent import BookingAgent
from app.ai.agents.fare_agent import FareAgent
from app.ai.agents.support_agent import SupportAgent
from app.ai.agents.trip_summary_agent import TripSummaryAgent
from app.ai.embeddings.openai_embedding_service import OpenAIEmbeddingService
from app.ai.providers.factory import get_llm_provider
from app.ai.rag.rag_service import RAGService
from app.ai.schemas import LLMResponse
from app.ai.vectorstores.chroma_store import ChromaVectorStore


class AIOrchestrator:
    def __init__(self) -> None:
        llm = get_llm_provider()
        rag = RAGService(llm=llm, embeddings=OpenAIEmbeddingService(), vector_store=ChromaVectorStore())
        self._booking_agent = BookingAgent(llm)
        self._support_agent = SupportAgent(rag)
        self._fare_agent = FareAgent(llm)
        self._summary_agent = TripSummaryAgent(llm)

    async def run(self, intent: str, message: str) -> LLMResponse:
        if intent == "ride_booking":
            return await self._booking_agent.run(message)
        if intent == "customer_support":
            return await self._support_agent.run(message)
        if intent == "trip_summary":
            return await self._summary_agent.run(message)
        return await self._fare_agent.run(message)
