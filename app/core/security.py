from enum import StrEnum


class UserRole(StrEnum):
    CUSTOMER = "customer"
    DRIVER = "driver"
    ADMIN = "admin"


class UserStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"
