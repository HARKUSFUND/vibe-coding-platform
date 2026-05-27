"""
Modèle ORM pour les prescriptions médicales.
Conforme CDC §4.1, §4.3
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class PrescripteurModel(Base):
    """Table des prescripteurs (médecins, structures de santé)."""
    __tablename__ = "prescripteurs"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[Optional[str]] = mapped_column(String(100))
    structure: Mapped[str] = mapped_column(String(200))  # Hôpital, clinique, cabinet
    adresse: Mapped[Optional[str]] = mapped_column(Text)
    telephone: Mapped[Optional[str]] = mapped_column(String(20))
    email: Mapped[Optional[str]] = mapped_column(String(150))
    specialite: Mapped[Optional[str]] = mapped_column(String(100))
    numero_ordre: Mapped[Optional[str]] = mapped_column(String(50))  # Numéro d'ordre médical
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_modification: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relations
    prescriptions: Mapped[List["PrescriptionModel"]] = relationship(
        "PrescriptionModel", back_populates="prescripteur", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prescripteur(id={self.id}, code='{self.code}', nom='{self.nom}')>"


class PrescriptionModel(Base):
    """Table des prescriptions médicales."""
    __tablename__ = "prescriptions"

    id: Mapped[int] = mapped_column(primary_key=True)
    numero: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    patient_id: Mapped[int] = mapped_column(ForeignKey("patients.id"), nullable=False)
    prescripteur_id: Mapped[Optional[int]] = mapped_column(ForeignKey("prescripteurs.id"))
    
    # Informations prescription
    date_prescription: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    urgence: Mapped[bool] = mapped_column(Boolean, default=False)
    contexte_clinique: Mapped[Optional[str]] = mapped_column(Text)  # Motif, symptômes
    traitement_en_cours: Mapped[Optional[str]] = mapped_column(Text)
    
    # Source (import SI hospitalier ou saisie manuelle)
    source: Mapped[str] = mapped_column(String(50), default="MANUEL")  # MANUEL, IMPORT_SI, API
    reference_externe: Mapped[Optional[str]] = mapped_column(String(100))  # ID dans SI externe
    
    # Statut
    statut: Mapped[str] = mapped_column(String(20), default="ACTIVE")  # ACTIVE, REALISEE, ANNULEE
    date_realisation: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Métadonnées
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cree_par: Mapped[Optional[str]] = mapped_column(String(50))
    date_modification: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relations
    patient: Mapped["PatientModel"] = relationship("PatientModel", back_populates="prescriptions")
    prescripteur: Mapped[Optional["PrescripteurModel"]] = relationship(
        "PrescripteurModel", back_populates="prescriptions"
    )
    examens: Mapped[List["ExamenPrescritModel"]] = relationship(
        "ExamenPrescritModel", back_populates="prescription", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Prescription(numero='{self.numero}', patient_id={self.patient_id})>"


class ExamenPrescritModel(Base):
    """Table de liaison prescription <-> examens prescrits."""
    __tablename__ = "examens_prescrits"

    id: Mapped[int] = mapped_column(primary_key=True)
    prescription_id: Mapped[int] = mapped_column(ForeignKey("prescriptions.id"), nullable=False)
    examen_id: Mapped[int] = mapped_column(ForeignKey("examens.id"), nullable=False)
    
    # Priorité de l'examen
    priorite: Mapped[str] = mapped_column(String(20), default="NORMALE")  # NORMALE, URGENTE, STAT
    instructions: Mapped[Optional[str]] = mapped_column(Text)  # Instructions particulières
    
    # Statut de réalisation
    statut: Mapped[str] = mapped_column(String(20), default="A_FAIRE")  # A_FAIRE, EN_COURS, FAIT
    date_prelevement: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_resultat: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Relation avec résultat
    resultat_id: Mapped[Optional[int]] = mapped_column(ForeignKey("resultats.id"))

    # Relations
    prescription: Mapped["PrescriptionModel"] = relationship(
        "PrescriptionModel", back_populates="examens"
    )
    examen: Mapped["ExamenModel"] = relationship("ExamenModel", back_populates="prescriptions")

    def __repr__(self) -> str:
        return f"<ExamenPrescrit(prescription_id={self.prescription_id}, examen_id={self.examen_id})>"


# Import tardif pour éviter les circular imports
from .patient import PatientModel
from .examen import ExamenModel
