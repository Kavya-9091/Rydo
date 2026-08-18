from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str
    content: str


class LLMResponse(BaseModel):
    content: str
    metadata: dict = Field(default_factory=dict)


class RetrievedDocument(BaseModel):
    content: str
    metadata: dict = Field(default_factory=dict)
    score: float | None = None


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict = Field(default_factory=dict)
