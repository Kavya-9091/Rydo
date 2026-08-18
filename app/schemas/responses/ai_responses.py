import uuid

from pydantic import BaseModel

from app.schemas.common import TimestampedResponse


class AIConversationResponse(TimestampedResponse):
    id: uuid.UUID
    user_id: uuid.UUID | None
    ride_id: uuid.UUID | None
    conversation_type: str
    status: str
    user_message: str
    assistant_message: str | None
    metadata_json: dict | None


class AIChatResponse(BaseModel):
    reply: str
    toolExecuted: str | None = None
    rideId: uuid.UUID | None = None
    conversationId: uuid.UUID
    metadata: dict | None = None


class AIProviderStatusResponse(BaseModel):
    provider: str
    configured: bool
    model: str
