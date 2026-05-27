"""Electronic signature with timestamp for biological validation."""

import hashlib
import hmac
from datetime import datetime
from typing import Optional
from loguru import logger

from ...config.settings import get_settings


class ElectronicSignature:
    """
    Electronic signature for biological validation.
    Compliant with CDC requirements for traceability.
    """

    def __init__(self, secret_key: Optional[str] = None):
        settings = get_settings()
        self.secret_key = secret_key or settings.secret_key

    def sign(
        self,
        user_id: int,
        document_type: str,
        document_id: int,
        content_hash: str,
        timestamp: Optional[datetime] = None,
    ) -> str:
        """
        Create an electronic signature.
        
        Args:
            user_id: ID of the signing user
            document_type: Type of document (resultat, don, validation...)
            document_id: ID of the document
            content_hash: SHA-256 hash of the document content
            timestamp: Signature timestamp (default: now)
        
        Returns:
            Signature string (base64-encoded HMAC)
        """
        if timestamp is None:
            timestamp = datetime.now()

        # Create signature data
        data_to_sign = f"{user_id}:{document_type}:{document_id}:{content_hash}:{timestamp.isoformat()}"
        
        # Generate HMAC-SHA256 signature
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            data_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        logger.info(f"Electronic signature created for {document_type}:{document_id} by user {user_id}")
        return signature

    def verify(
        self,
        user_id: int,
        document_type: str,
        document_id: int,
        content_hash: str,
        timestamp: datetime,
        signature: str,
    ) -> bool:
        """
        Verify an electronic signature.
        
        Returns:
            True if signature is valid, False otherwise
        """
        try:
            # Recreate signature data
            data_to_sign = f"{user_id}:{document_type}:{document_id}:{content_hash}:{timestamp.isoformat()}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.secret_key.encode("utf-8"),
                data_to_sign.encode("utf-8"),
                hashlib.sha256,
            ).hexdigest()

            # Compare signatures securely
            is_valid = hmac.compare_digest(signature, expected_signature)
            
            if is_valid:
                logger.info(f"Signature verified for {document_type}:{document_id}")
            else:
                logger.warning(f"Invalid signature for {document_type}:{document_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Signature verification error: {e}")
            return False

    @staticmethod
    def hash_content(content: str) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def sign_resultat(
        self,
        user_id: int,
        resultat_id: int,
        valeur: str,
        examen_nom: str,
        patient_id: int,
    ) -> tuple:
        """
        Sign a laboratory result.
        
        Returns:
            (signature, timestamp) tuple
        """
        timestamp = datetime.now()
        
        # Create content string
        content = f"{resultat_id}:{examen_nom}:{valeur}:{patient_id}:{timestamp.isoformat()}"
        content_hash = self.hash_content(content)
        
        signature = self.sign(user_id, "resultat", resultat_id, content_hash, timestamp)
        
        return signature, timestamp

    def sign_validation(
        self,
        biologiste_id: int,
        validation_type: str,
        element_id: int,
        elements_valides: list,
    ) -> tuple:
        """
        Sign a biological validation batch.
        
        Returns:
            (signature, timestamp) tuple
        """
        timestamp = datetime.now()
        
        # Create content from validated elements
        elements_str = ",".join(str(e) for e in elements_valides)
        content = f"{validation_type}:{element_id}:{elements_str}:{timestamp.isoformat()}"
        content_hash = self.hash_content(content)
        
        signature = self.sign(biologiste_id, validation_type, element_id, content_hash, timestamp)
        
        return signature, timestamp
