import uuid
from datetime import datetime

from app.schemas.common import TimestampedResponse


class NotificationResponse(TimestampedResponse):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    message: str
    notification_type: str
    is_read: bool
    deleted_at: datetime | None
