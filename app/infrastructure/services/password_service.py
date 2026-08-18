from passlib.context import CryptContext


class PasswordService:
    def __init__(self) -> None:
        self._context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._context.hash(password)

    def verify_password(self, plain_password: str, password_hash: str) -> bool:
        return self._context.verify(plain_password, password_hash)


password_service = PasswordService()
