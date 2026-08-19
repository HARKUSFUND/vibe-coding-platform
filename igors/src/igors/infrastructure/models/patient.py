# -*- coding: utf-8 -*-
"""
patient.py — Modèle ORM Patient pour PostgreSQL

Table: patients
"""

from datetime import datetime
from sqlalchemy import String, Date, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PatientModel(Base):
    """Modèle ORM pour la table patients."""
    
    __tablename__ = "patients"
    
    # Clé primaire (code patient)
    Pa_code: Mapped[str] = mapped_column(String(50), primary_key=True)
    
    # Informations personnelles
    Pa_nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    Pa_prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    Pa_sexe: Mapped[str] = mapped_column(String(1), default="M")
    Pa_dnaissance: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    
    # Coordonnées
    Pa_contact: Mapped[str] = mapped_column(String(50), nullable=True)
    Pa_adresse: Mapped[str] = mapped_column(String(255), nullable=True)
    
    # Informations médicales
    Pa_groupe_sanguin: Mapped[str] = mapped_column(String(10), nullable=True)
    Pa_antecedents: Mapped[str] = mapped_column(String(500), nullable=True, default="")
    
    # Relations
    prescriptions = relationship("PrescriptionModel", back_populates="patient", cascade="all, delete-orphan")
    resultats = relationship("ResultatModel", back_populates="patient", cascade="all, delete-orphan")
    
    def __repr__(self) -> str:
        return f"<Patient(Pa_code='{self.Pa_code}', Pa_nom='{self.Pa_nom}', Pa_prenom='{self.Pa_prenom}')>"
