import chromadb

from app.ai.schemas import RetrievedDocument
from app.ai.vectorstores.base import VectorStore
from app.core.settings import get_settings


class ChromaVectorStore(VectorStore):
    def __init__(self, collection_name: str | None = None) -> None:
        settings = get_settings()
        self._client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port)
        self._collection = self._client.get_or_create_collection(collection_name or settings.chroma_collection_faqs)

    def add_documents(self, ids: list[str], documents: list[str], embeddings: list[list[float]], metadatas: list[dict] | None = None) -> None:
        self._collection.upsert(ids=ids, documents=documents, embeddings=embeddings, metadatas=metadatas)

    def query(self, query_embedding: list[float], limit: int = 5) -> list[RetrievedDocument]:
        result = self._collection.query(query_embeddings=[query_embedding], n_results=limit)
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            RetrievedDocument(content=doc, metadata=metadata or {}, score=distance)
            for doc, metadata, distance in zip(docs, metadatas, distances, strict=False)
        ]
