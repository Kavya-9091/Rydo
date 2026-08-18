import uuid

from app.core.security import UserRole
from app.infrastructure.services.jwt_service import jwt_service


def test_access_token_contains_subject_and_role() -> None:
    user_id = uuid.uuid4()
    token = jwt_service.create_access_token(user_id=user_id, role=UserRole.CUSTOMER)
    payload = jwt_service.decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == UserRole.CUSTOMER.value
