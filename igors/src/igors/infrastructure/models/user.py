"""User model for authentication and authorization."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from ..database.base import Base


class User(Base):
    """User table for authentication with bcrypt and OTP support."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    telephone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    # OTP fields
    otp_actif: Mapped[bool] = mapped_column(Boolean, default=False)
    otp_secret: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Account status
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_modification: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)
    date_derniere_connexion: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Audit
    cree_par: Mapped[int | None] = mapped_column(Integer, nullable=True)
    modifie_par: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def to_dict(self) -> dict:
        """Convert user to dictionary (without sensitive data)."""
        return {
            "id": self.id,
            "username": self.username,
            "nom": self.nom,
            "prenom": self.prenom,
            "role": self.role,
            "email": self.email,
            "telephone": self.telephone,
            "actif": self.actif,
            "otp_actif": self.otp_actif,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "date_derniere_connexion": self.date_derniere_connexion.isoformat() if self.date_derniere_connexion else None,
        }

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>"
