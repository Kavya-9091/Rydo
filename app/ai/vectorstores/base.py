from abc import ABC, abstractmethod

from app.ai.schemas import RetrievedDocument


class VectorStore(ABC):
    @abstractmethod
    def add_documents(self, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def query(self, query_embedding: list[float], limit: int = 5) -> list[RetrievedDocument]:
        raise NotImplementedError
