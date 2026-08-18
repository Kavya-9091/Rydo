from app.ai.embeddings.base import EmbeddingService
from app.ai.prompts.support_prompts import SUPPORT_SYSTEM_PROMPT
from app.ai.providers.base import LLMProvider
from app.ai.schemas import ChatMessage, LLMResponse, RetrievedDocument
from app.ai.vectorstores.base import VectorStore


class RAGService:
    def __init__(self, *, llm: LLMProvider, embeddings: EmbeddingService, vector_store: VectorStore) -> None:
        self._llm = llm
        self._embeddings = embeddings
        self._vector_store = vector_store

    async def answer(self, question: str, limit: int = 5) -> tuple[LLMResponse, list[RetrievedDocument]]:
        query_embedding = (await self._embeddings.embed_texts([question]))[0]
        documents = self._vector_store.query(query_embedding, limit=limit)
        context = "\n\n".join(document.content for document in documents)
        response = await self._llm.generate(
            [
                ChatMessage(role="system", content=SUPPORT_SYSTEM_PROMPT),
                ChatMessage(role="user", content=f"Context:\n{context}\n\nQuestion:\n{question}"),
            ]
        )
        return response, documents

    async def index_documents(self, documents: list[str], ids: list[str], metadatas: list[dict] | None = None) -> None:
        embeddings = await self._embeddings.embed_texts(documents)
        self._vector_store.add_documents(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)
