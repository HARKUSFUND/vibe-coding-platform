"""Patient model for patient management."""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class PatientModel(Base):
    """Patient table for laboratory analysis tracking."""

    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Identity (NIR should be encrypted at application level)
    nir: Mapped[str | None] = mapped_column(String(100), unique=True, nullable=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    sexe: Mapped[str] = mapped_column(String(1), nullable=False)  # 'M' or 'F'
    date_naissance: Mapped[date] = mapped_column(Date, nullable=False)
    lieu_naissance: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Contact
    telephone: Mapped[str] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    adresse: Mapped[str] = mapped_column(Text, nullable=True)
    ville: Mapped[str] = mapped_column(String(100), nullable=True)
    quartier: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Medical info
    groupe_sanguin: Mapped[str | None] = mapped_column(String(3), nullable=True)
    facteur_rhesus: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    
    # Status
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_modification: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)
    cree_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    modifie_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    prescriptions = relationship("PrescriptionModel", back_populates="patient", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert patient to dictionary."""
        return {
            "id": self.id,
            "nir": self.nir,
            "nom": self.nom,
            "prenom": self.prenom,
            "sexe": self.sexe,
            "date_naissance": self.date_naissance.isoformat() if self.date_naissance else None,
            "groupe_sanguin": self.groupe_sanguin,
            "actif": self.actif,
        }

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, nom='{self.nom}', prenom='{self.prenom}')>"
