import json

from redis.asyncio import Redis

from app.ai.memory.base import ConversationMemory
from app.ai.schemas import ChatMessage


class RedisConversationMemory(ConversationMemory):
    def __init__(self, redis: Redis, ttl_seconds: int = 86400) -> None:
        self._redis = redis
        self._ttl_seconds = ttl_seconds

    async def append(self, conversation_id: str, message: ChatMessage) -> None:
        key = self._key(conversation_id)
        await self._redis.rpush(key, message.model_dump_json())
        await self._redis.expire(key, self._ttl_seconds)

    async def get_recent(self, conversation_id: str, limit: int = 10) -> list[ChatMessage]:
        raw_messages = await self._redis.lrange(self._key(conversation_id), -limit, -1)
        return [ChatMessage(**json.loads(raw)) for raw in raw_messages]

    @staticmethod
    def _key(conversation_id: str) -> str:
        return f"ai:conversation:{conversation_id}:messages"
