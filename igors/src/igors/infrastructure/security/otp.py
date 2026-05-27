"""OTP (One Time Password) management using TOTP."""

import pyotp
from loguru import logger


class OTPManager:
    """TOTP-based OTP manager compliant with CDC requirements."""

    def __init__(self, issuer: str = "IGORS", digits: int = 6, interval: int = 30):
        self.issuer = issuer
        self.digits = digits
        self.interval = interval

    def generate_secret(self) -> str:
        """Generate a new random secret for TOTP."""
        secret = pyotp.random_base32()
        logger.info("New OTP secret generated")
        return secret

    def get_provisioning_uri(self, secret: str, username: str, email: str) -> str:
        """
        Generate provisioning URI for QR code.
        This URI can be used with Google Authenticator, Authy, etc.
        """
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        uri = totp.provisioning_uri(
            name=email,
            issuer_name=self.issuer,
        )
        logger.info(f"Provisioning URI generated for {username}")
        return uri

    def verify(self, secret: str, otp_code: str, valid_window: int = 1) -> bool:
        """
        Verify an OTP code.
        
        Args:
            secret: The user's TOTP secret
            otp_code: The OTP code to verify
            valid_window: Number of intervals to check (default: 1 before/after)
        
        Returns:
            True if valid, False otherwise
        """
        try:
            totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
            is_valid = totp.verify(otp_code, valid_window=valid_window)
            
            if is_valid:
                logger.info("OTP verification successful")
            else:
                logger.warning("OTP verification failed")
            
            return is_valid
        except Exception as e:
            logger.error(f"OTP verification error: {e}")
            return False

    def get_current(self, secret: str) -> str:
        """Get current OTP code (for testing/debugging only)."""
        totp = pyotp.TOTP(secret, digits=self.digits, interval=self.interval)
        return totp.now()

    def get_qr_code_data(self, secret: str, username: str, email: str) -> dict:
        """
        Get data needed to generate QR code.
        
        Returns:
            Dictionary with provisioning_uri and other metadata
        """
        return {
            "secret": secret,
            "provisioning_uri": self.get_provisioning_uri(secret, username, email),
            "issuer": self.issuer,
            "username": username,
            "digits": self.digits,
            "interval": self.interval,
        }
