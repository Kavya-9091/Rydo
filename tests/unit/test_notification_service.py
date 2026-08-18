import uuid

from app.infrastructure.services.notification_service import NotificationService


class FakeSession:
    def __init__(self) -> None:
        self.added = []

    def add(self, value) -> None:
        self.added.append(value)


def test_notification_service_persists_notification() -> None:
    db = FakeSession()
    user_id = uuid.uuid4()

    notification = NotificationService(db).send(
        user_id=user_id,
        title="Ride completed",
        message="Please proceed to payment.",
        notification_type="ride_completed",
    )

    assert notification.user_id == user_id
    assert notification.title == "Ride completed"
    assert notification.notification_type == "ride_completed"
    assert notification.is_read is None
    assert db.added == [notification]
