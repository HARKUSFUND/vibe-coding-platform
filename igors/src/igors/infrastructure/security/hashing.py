"""Password hashing with bcrypt (cost factor 12)."""

import bcrypt
from loguru import logger

from ...config.settings import get_settings


class Hasher:
    """Bcrypt password hasher with configurable rounds."""

    def __init__(self, rounds: int = None):
        settings = get_settings()
        self.rounds = rounds or settings.bcrypt_rounds

    def hash(self, password: str) -> str:
        """Hash a password using bcrypt."""
        if not password:
            raise ValueError("Password cannot be empty")

        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt(rounds=self.rounds)
        hashed = bcrypt.hashpw(password_bytes, salt)
        return hashed.decode("utf-8")

    def verify(self, password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        try:
            password_bytes = password.encode("utf-8")
            hashed_bytes = hashed.encode("utf-8")
            return bcrypt.checkpw(password_bytes, hashed_bytes)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False


def hash_password(password: str, rounds: int = None) -> str:
    """Standalone function to hash a password."""
    hasher = Hasher(rounds)
    return hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Standalone function to verify a password."""
    hasher = Hasher()
    return hasher.verify(password, hashed)
