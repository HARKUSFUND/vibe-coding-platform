"""Donneur model for blood donor management."""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class DonneurModel(Base):
    """Blood donor table with encrypted NIR and consent tracking."""

    __tablename__ = "donneurs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identity (NIR should be encrypted at application level)
    nir: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    sexe: Mapped[str] = mapped_column(String(1), nullable=False)  # 'M' or 'F'
    date_naissance: Mapped[date] = mapped_column(Date, nullable=False)
    lieu_naissance: Mapped[str] = mapped_column(String(100), nullable=True)
    nationalite: Mapped[str] = mapped_column(String(50), default="Ivoirienne")
    profession: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Contact
    telephone: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adresse: Mapped[str] = mapped_column(Text, nullable=True)
    ville: Mapped[str] = mapped_column(String(100), nullable=False)
    quartier: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Blood type
    groupe_sanguin: Mapped[str] = mapped_column(String(3), nullable=True, index=True)  # A+, B-, etc.
    facteur_rhesus: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Donation history
    date_premier_don: Mapped[date | None] = mapped_column(Date, nullable=True)
    nombre_dons: Mapped[int] = mapped_column(Integer, default=0)
    date_dernier_don: Mapped[date | None] = mapped_column(Date, nullable=True)
    
    # Eligibility
    eligible_don: Mapped[bool] = mapped_column(Boolean, default=True)
    contre_indications: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Consent (CDC requirement)
    consentement_signe: Mapped[bool] = mapped_column(Boolean, default=False)
    date_consentement: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    fichier_consentement: Mapped[str | None] = mapped_column(String(500), nullable=True)  # Path to scanned consent
    
    # Status
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_modification: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)
    cree_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    modifie_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    dons = relationship("DonModel", back_populates="donneur", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert donor to dictionary."""
        return {
            "id": self.id,
            "nir": self.nir,
            "nom": self.nom,
            "prenom": self.prenom,
            "sexe": self.sexe,
            "date_naissance": self.date_naissance.isoformat() if self.date_naissance else None,
            "groupe_sanguin": self.groupe_sanguin,
            "nombre_dons": self.nombre_dons,
            "eligible_don": self.eligible_don,
            "consentement_signe": self.consentement_signe,
            "actif": self.actif,
        }

    def __repr__(self) -> str:
        return f"<Donneur(id={self.id}, nom='{self.nom}', prenom='{self.prenom}', groupe='{self.groupe_sanguin}')>"
