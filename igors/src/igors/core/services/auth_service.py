"""Authentication and OTP services."""

from datetime import datetime, timedelta
from typing import Optional, Tuple
import pyotp
from loguru import logger

from ...config.settings import Settings, get_settings
from ...infrastructure.security.hashing import Hasher
from ...infrastructure.security.otp import OTPManager
from ...infrastructure.repositories.user_repo import UserRepository


class AuthService:
    """Authentication service with bcrypt and OTP support."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.user_repo = UserRepository()
        self.hasher = Hasher(rounds=self.settings.bcrypt_rounds)
        self.otp_manager = OTPManager(
            issuer=self.settings.otp_issuer,
            digits=self.settings.otp_digits,
            interval=self.settings.otp_interval,
        )

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """
        Authenticate user with username and password.
        Returns user dict if successful, None otherwise.
        """
        user = self.user_repo.get_by_username(username)
        if not user:
            logger.warning(f"Authentication failed: user {username} not found")
            return None

        if not user.get("actif", True):
            logger.warning(f"Authentication failed: user {username} is inactive")
            return None

        if not self.hasher.verify(password, user.get("password_hash", "")):
            logger.warning(f"Authentication failed: invalid password for {username}")
            return None

        # Return user without sensitive data
        return {
            "id": user["id"],
            "username": user["username"],
            "nom": user["nom"],
            "prenom": user["prenom"],
            "role": user["role"],
            "email": user.get("email"),
            "otp_actif": user.get("otp_actif", False),
        }

    def verify_otp(self, user_id: int, otp_code: str) -> bool:
        """Verify OTP code for user."""
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.get("otp_actif"):
            return False

        secret = user.get("otp_secret")
        if not secret:
            return False

        return self.otp_manager.verify(secret, otp_code)

    def setup_otp(self, user_id: int) -> Tuple[str, str]:
        """
        Setup OTP for user.
        Returns (secret, provisioning_uri).
        """
        secret = self.otp_manager.generate_secret()
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        provisioning_uri = self.otp_manager.get_provisioning_uri(
            secret, user.get("username", ""), user.get("email", "")
        )

        # Save secret to database
        self.user_repo.update(user_id, {"otp_secret": secret, "otp_actif": False})

        return secret, provisioning_uri

    def activate_otp(self, user_id: int, otp_code: str) -> bool:
        """Activate OTP after verification."""
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.get("otp_secret"):
            return False

        if self.otp_manager.verify(user["otp_secret"], otp_code):
            self.user_repo.update(user_id, {"otp_actif": True})
            return True
        return False

    def deactivate_otp(self, user_id: int) -> bool:
        """Deactivate OTP for user."""
        user = self.user_repo.get_by_id(user_id)
        if not user:
            return False

        self.user_repo.update(user_id, {"otp_actif": False, "otp_secret": None})
        return True


class OTPService:
    """Standalone OTP service for TOTP generation and verification."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self.otp_manager = OTPManager(
            issuer=self.settings.otp_issuer,
            digits=self.settings.otp_digits,
            interval=self.settings.otp_interval,
        )

    def generate_secret(self) -> str:
        """Generate a new OTP secret."""
        return self.otp_manager.generate_secret()

    def get_provisioning_uri(self, secret: str, username: str, email: str) -> str:
        """Get QR code provisioning URI."""
        return self.otp_manager.get_provisioning_uri(secret, username, email)

    def verify(self, secret: str, otp_code: str) -> bool:
        """Verify OTP code."""
        return self.otp_manager.verify(secret, otp_code)

    def get_current_otp(self, secret: str) -> str:
        """Get current OTP code (for testing/debugging)."""
        return self.otp_manager.get_current(secret)
