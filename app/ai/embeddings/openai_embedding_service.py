from openai import AsyncOpenAI

from app.ai.embeddings.base import EmbeddingService
from app.core.settings import get_settings


class OpenAIEmbeddingService(EmbeddingService):
    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.openai_embedding_model
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        response = await self._client.embeddings.create(model=self._model, input=texts)
        return [item.embedding for item in response.data]
