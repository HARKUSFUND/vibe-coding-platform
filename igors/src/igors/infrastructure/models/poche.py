"""Poche (blood bag) model for blood product tracking."""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..database.base import Base


class PocheModel(Base):
    """Blood bag table for tracking blood products from collection to transfusion."""

    __tablename__ = "poches_sang"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Bag identification
    code_barre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    code_pochette: Mapped[str] = mapped_column(String(50), nullable=True)  # Code secondaire
    
    # Foreign keys
    don_id: Mapped[int] = mapped_column(Integer, ForeignKey("dons.id"), nullable=False)
    type_psl_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("types_psl.id"), nullable=True)
    
    # Blood product details
    type_produit: Mapped[str] = mapped_column(String(50), nullable=False)  # Culot globulaire, Plasma, Plaquettes
    volume: Mapped[float] = mapped_column(nullable=True)  # en mL
    groupe_abo: Mapped[str] = mapped_column(String(3), nullable=False, index=True)  # A, B, AB, O
    facteur_rhesus: Mapped[bool] = mapped_column(Boolean, nullable=False)  # True =+, False =-
    phenotype_etendu: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # Dates importantes (CDC requirement: conservation tracking)
    date_prelevement: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    date_expiration: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    date_transformation: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    
    # Status
    statut: Mapped[str] = mapped_column(String(30), default="EN_ATTENTE")  # EN_ATTENTE, QUALIFIE, DISPONIBLE, RESERVE, TRANSFUSE, PERIME, DETRUIT
    lieu_stockage: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Refrigerateur, Congelateur
    temperature_stockage: Mapped[float | None] = mapped_column(nullable=True)  # en °C
    
    # Qualification biologique
    resultat_vih: Mapped[str | None] = mapped_column(String(20), nullable=True)  # NEGATIF, POSITIF, INDETERMINE
    resultat_vhb: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resultat_vhc: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resultat_htlv: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resultat_syphilis: Mapped[str | None] = mapped_column(String(20), nullable=True)
    resultat_paludisme: Mapped[str | None] = mapped_column(String(20), nullable=True)
    
    qualif_biologique_statut: Mapped[str] = mapped_column(String(30), default="EN_ATTENTE")  # EN_ATTENTE, CONFORME, NON_CONFORME
    date_qualif: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    qualifie_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Tracking
    numero_lot: Mapped[str | None] = mapped_column(String(50), nullable=True)
    etablissement_origine: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Audit
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_modification: Mapped[datetime | None] = mapped_column(DateTime, onupdate=datetime.utcnow)
    cree_par: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)

    # Relationships
    don = relationship("DonModel", back_populates="poches")

    def to_dict(self) -> dict:
        """Convert blood bag to dictionary."""
        return {
            "id": self.id,
            "code_barre": self.code_barre,
            "type_produit": self.type_produit,
            "groupe_abo": self.groupe_abo,
            "facteur_rhesus": "+" if self.facteur_rhesus else "-",
            "date_expiration": self.date_expiration.isoformat() if self.date_expiration else None,
            "statut": self.statut,
            "qualif_biologique_statut": self.qualif_biologique_statut,
        }

    def __repr__(self) -> str:
        return f"<Poche(id={self.id}, code='{self.code_barre}', type='{self.type_produit}')>"


class TypePSLModel(Base):
    """Reference table for blood product types."""

    __tablename__ = "types_psl"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    duree_conservation_jours: Mapped[int] = mapped_column(Integer, nullable=True)
    temperature_min: Mapped[float | None] = mapped_column(nullable=True)  # °C
    temperature_max: Mapped[float | None] = mapped_column(nullable=True)  # °C
    actif: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<TypePSL(code='{self.code}', nom='{self.nom}')>"
