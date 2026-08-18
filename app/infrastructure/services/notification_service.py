import logging
import uuid

from sqlalchemy.orm import Session

from app.infrastructure.database.models.notification_model import NotificationModel

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, db: Session) -> None:
        self._db = db

    def send(self, *, user_id: uuid.UUID, title: str, message: str, notification_type: str) -> NotificationModel:
        notification = NotificationModel(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
        )
        self._db.add(notification)
        logger.info(
            "notification_created",
            extra={"user_id": str(user_id), "title": title, "notification_type": notification_type},
        )
        return notification
