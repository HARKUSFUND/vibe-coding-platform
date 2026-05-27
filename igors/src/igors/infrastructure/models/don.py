"""Don (blood donation) model for donation tracking."""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class DonModel(Base):
    """Blood donation table linking donor to collection and bags."""

    __tablename__ = "dons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Donation reference
    code_don: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    
    # Foreign keys
    donneur_id: Mapped[int] = mapped_column(Integer, ForeignKey("donneurs.id"), nullable=False)
    collecte_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("collectes.id"), nullable=True)
    realise_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Donation details
    type_don: Mapped[str] = mapped_column(String(20), nullable=False)  # Sang total, Plasma, Plaquettes
    volume_preleve: Mapped[float] = mapped_column(Float, nullable=True)  # en mL
    date_don: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    heure_don: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    lieu_collecte: Mapped[str] = mapped_column(String(100), nullable=True)
    
    # Pre-donation checks
    poids_donueur: Mapped[float] = mapped_column(Float, nullable=True)  # en kg
    tension_arterielle: Mapped[str] = mapped_column(String(20), nullable=True)  # ex: "12/8"
    pouls: Mapped[int] = mapped_column(Integer, nullable=True)  # bpm
    hemoglobine: Mapped[float] = mapped_column(Float, nullable=True)  # g/dL
    
    # Status
    statut: Mapped[str] = mapped_column(String(30), default="EN_ATTENTE")  # EN_ATTENTE, VALIDE, EXCLU, TRANSFORME
    motif_exclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    # Qualification biologique (CDC requirement)
    qualif_biologique: Mapped[bool] = mapped_column(Boolean, default=False)
    date_qualif: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    qualifie_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Anonymisation VIH (CDC requirement)
    vih_anonymise: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Audit
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_modification: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relationships
    donneur = relationship("DonneurModel", back_populates="dons")
    poches = relationship("PocheModel", back_populates="don", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        """Convert donation to dictionary."""
        return {
            "id": self.id,
            "code_don": self.code_don,
            "donneur_id": self.donneur_id,
            "type_don": self.type_don,
            "volume_preleve": self.volume_preleve,
            "date_don": self.date_don.isoformat() if self.date_don else None,
            "statut": self.statut,
            "qualif_biologique": self.qualif_biologique,
        }

    def __repr__(self) -> str:
        return f"<Don(id={self.id}, code='{self.code_don}', date='{self.date_don}')>"
