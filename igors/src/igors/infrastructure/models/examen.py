"""
Modèles ORM pour les examens de laboratoire (LOINC).
CDC §4.1: Référentiel examens avec codes LOINC et fourchettes de référence.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List

from igors.infrastructure.database.base import Base


class ExamenModel(Base):
    """Table des examens de laboratoire."""
    __tablename__ = "examens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code_loinc: Mapped[Optional[str]] = mapped_column(String(50), index=True)  # Code LOINC standard
    code_local: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # Code interne
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    nom_complet: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Type d'examen
    type_examen: Mapped[str] = mapped_column(String(50), default='biologie')  # biologie, hematologie, immunologie, etc.
    categorie: Mapped[Optional[str]] = mapped_column(String(100))  # NFS, Bilan hepatique, etc.
    
    # Unités et références
    unite: Mapped[Optional[str]] = mapped_column(String(50))
    reference_basse: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    reference_haute: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    
    # Seuils critiques (CDC §4.5)
    seuil_critique_bas: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    seuil_critique_haut: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    
    # Spécificités par âge/sexe
    reference_adulte_h: Mapped[Optional[str]] = mapped_column(String(100))  # Homme adulte
    reference_adulte_f: Mapped[Optional[str]] = mapped_column(String(100))  # Femme adulte
    reference_enfant: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Configuration automate
    automate_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("automates.id"))
    code_automate: Mapped[Optional[str]] = mapped_column(String(50))  # Code sur l'automate
    
    # Méthode analytique
    methode: Mapped[Optional[str]] = mapped_column(String(200))
    technique: Mapped[Optional[str]] = mapped_column(String(200))
    
    # Délais
    delai_rendu_heures: Mapped[Optional[int]] = mapped_column(Integer, default=24)  # Délai cible
    
    # Statut
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    disponible: Mapped[bool] = mapped_column(Boolean, default=True)  # Disponible à la prescription
    
    # Metadata
    description: Mapped[Optional[str]] = mapped_column(Text)
    remarques: Mapped[Optional[str]] = mapped_column(Text)
    
    # Audit
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    date_modification: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.now)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Relations
    resultats = relationship("ResultatModel", back_populates="examen", cascade="all, delete-orphan")
    automates = relationship("AutomateModel", back_populates="examens")
    
    def __repr__(self):
        return f"<Examen(id={self.id}, code='{self.code_local}', nom='{self.nom}')>"


class GroupeExamensModel(Base):
    """Groupes d'examens (profils, bilans)."""
    __tablename__ = "groupes_examens"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    # Prix (optionnel)
    prix: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    
    # Statut
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Audit
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    
    # Relation many-to-many avec examens
    examens = relationship(
        "ExamenModel",
        secondary="groupe_examen_assoc",
        back_populates="groupes"
    )
    
    def __repr__(self):
        return f"<GroupeExamens(id={self.id}, nom='{self.nom}')>"


# Table d'association pour la relation many-to-many
class GroupeExamenAssoc(Base):
    """Table d'association groupes/examens."""
    __tablename__ = "groupe_examen_assoc"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    groupe_id: Mapped[int] = mapped_column(Integer, ForeignKey("groupes_examens.id"), nullable=False)
    examen_id: Mapped[int] = mapped_column(Integer, ForeignKey("examens.id"), nullable=False)
    ordre: Mapped[Optional[int]] = mapped_column(Integer, default=0)  # Ordre d'affichage
    
    def __repr__(self):
        return f"<GroupeExamenAssoc(groupe={self.groupe_id}, examen={self.examen_id})>"


# Ajouter la relation inverse dans ExamenModel
ExamenModel.groupes = relationship(
    "GroupeExamensModel",
    secondary="groupe_examen_assoc",
    back_populates="examens"
)
