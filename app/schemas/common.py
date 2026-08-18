import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class IdResponse(ORMBaseModel):
    id: uuid.UUID


class TimestampedResponse(ORMBaseModel):
    created_at: datetime
    updated_at: datetime
