from abc import ABC, abstractmethod

from app.ai.schemas import ChatMessage


class ConversationMemory(ABC):
    @abstractmethod
    async def append(self, conversation_id: str, message: ChatMessage) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_recent(self, conversation_id: str, limit: int = 10) -> list[ChatMessage]:
        raise NotImplementedError
