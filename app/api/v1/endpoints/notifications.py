import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.infrastructure.database.models.notification_model import NotificationModel
from app.infrastructure.database.models.user_model import UserModel
from app.schemas.responses.notification_responses import NotificationResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("", response_model=list[NotificationResponse])
def list_notifications(
    unread_only: bool = False,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> list[NotificationResponse]:
    statement = select(NotificationModel).where(
        NotificationModel.user_id == current_user.id,
        NotificationModel.deleted_at.is_(None),
    )
    if unread_only:
        statement = statement.where(NotificationModel.is_read.is_(False))
    notifications = db.scalars(statement.order_by(NotificationModel.created_at.desc()).limit(50)).all()
    return [NotificationResponse.model_validate(notification) for notification in notifications]


@router.post("/{notification_id}/read", response_model=NotificationResponse)
def mark_notification_read(
    notification_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
) -> NotificationResponse:
    notification = db.get(NotificationModel, notification_id)
    if not notification or notification.deleted_at is not None or notification.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Notification not found")

    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return NotificationResponse.model_validate(notification)
