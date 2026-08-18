from typing import Any

from pydantic import BaseModel, Field


class AIMessageRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)


class AIChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=4000)
    context: dict[str, Any] = Field(default_factory=dict)


class TripSummaryRequest(BaseModel):
    ride_notes: str | None = Field(default=None, max_length=4000)
