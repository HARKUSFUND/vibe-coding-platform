"""
Modèles ORM pour les résultats d'analyses biologiques.
CDC §4.5: Résultats avec validation et signature électronique.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, Numeric, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional

from igors.infrastructure.database.base import Base


class ResultatModel(Base):
    """Table des résultats d'analyses."""
    __tablename__ = "resultats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    
    # Liens vers patient et examen
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False, index=True)
    examen_id: Mapped[int] = mapped_column(Integer, ForeignKey("examens.id"), nullable=False, index=True)
    prescription_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("prescriptions.id"), index=True)
    
    # Lien vers le don (si applicable - transfusion)
    don_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dons.id"), index=True)
    
    # Valeurs du résultat
    valeur_numerique: Mapped[Optional[float]] = mapped_column(Numeric(15, 6))
    valeur_texte: Mapped[Optional[str]] = mapped_column(String(500))  # Pour résultats qualitatifs
    valeur_calculee: Mapped[Optional[float]] = mapped_column(Numeric(15, 6))  # Si calculé (ex: ratio)
    
    # Unité et références
    unite: Mapped[Optional[str]] = mapped_column(String(50))
    reference_basse: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    reference_haute: Mapped[Optional[float]] = mapped_column(Numeric(10, 4))
    
    # Drapeaux et alertes
    drapeau: Mapped[Optional[str]] = mapped_column(String(10))  # H (High), L (Low), HH, LL, etc.
    est_critique: Mapped[bool] = mapped_column(Boolean, default=False)  # Résultat critique
    est_anormal: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Validation (CDC §4.5)
    statut_validation: Mapped[str] = mapped_column(String(20), default='en_attente', index=True)
    # 'en_attente', 'valide', 'rejete', 'annule'
    
    validateur_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    date_validation: Mapped[Optional[datetime]] = mapped_column(DateTime)
    commentaire_validation: Mapped[Optional[str]] = mapped_column(Text)
    
    # Signature électronique (CDC §4.5)
    signature_electronique: Mapped[Optional[str]] = mapped_column(Text)
    hash_signature: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Rejet
    rejecteur_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    date_rejet: Mapped[Optional[datetime]] = mapped_column(DateTime)
    motif_rejet: Mapped[Optional[str]] = mapped_column(Text)
    
    # Automate
    automate_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("automates.id"))
    resultat_brut: Mapped[Optional[str]] = mapped_column(String(500))  # Valeur brute de l'automate
    flag_automate: Mapped[Optional[str]] = mapped_column(String(100))  # Flags de l'automate
    
    # Dates
    date_prelevement: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_reception: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    date_analyse: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_resultat: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Technique
    technicien_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    poste_travail: Mapped[Optional[str]] = mapped_column(String(100))
    lot_reactif: Mapped[Optional[str]] = mapped_column(String(100))
    date_peremption_reactif: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Contrôle qualité
    cqi_valide: Mapped[bool] = mapped_column(Boolean, default=True)
    regle_westgard_violee: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Commentaire biologiste
    commentaire: Mapped[Optional[str]] = mapped_column(Text)
    
    # Service/département
    service_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("services.id"))
    
    # Audit
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    date_modification: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.now)
    created_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id"))
    
    # Contrainte unique pour éviter les doublons
    __table_args__ = (
        UniqueConstraint('patient_id', 'examen_id', 'date_analyse', name='uq_patient_examen_date'),
    )
    
    # Relations
    patient = relationship("PatientModel", back_populates="resultats")
    examen = relationship("ExamenModel", back_populates="resultats")
    validateur = relationship("UserModel", foreign_keys=[validateur_id], backref="resultats_valides")
    technicien = relationship("UserModel", foreign_keys=[technicien_id], backref="resultats_techniques")
    don = relationship("DonModel", back_populates="resultats")
    prescription = relationship("PrescriptionModel", back_populates="resultats")
    
    def __repr__(self):
        return f"<Resultat(id={self.id}, patient={self.patient_id}, examen={self.examen_id}, valeur={self.valeur_numerique})>"
    
    @property
    def valeur_formatee(self) -> str:
        """Retourner la valeur formatée pour affichage."""
        if self.valeur_texte:
            return self.valeur_texte
        if self.valeur_numerique is not None:
            return f"{self.valeur_numerique:.2f}"
        return "N/A"
    
    @property
    def interpretation(self) -> str:
        """Interpréter le résultat par rapport aux références."""
        if self.valeur_numerique is None:
            return "N/A"
        
        if self.reference_basse and self.valeur_numerique < self.reference_basse:
            return "BAS"
        if self.reference_haute and self.valeur_numerique > self.reference_haute:
            return "HAUT"
        return "Normal"


class HistoriqueResultatModel(Base):
    """Historique des modifications de résultats (audit trail)."""
    __tablename__ = "historique_resultats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resultat_id: Mapped[int] = mapped_column(Integer, ForeignKey("resultats.id"), nullable=False, index=True)
    
    # Ancienne et nouvelle valeurs
    ancienne_valeur: Mapped[Optional[str]] = mapped_column(String(500))
    nouvelle_valeur: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Type de modification
    type_modification: Mapped[str] = mapped_column(String(50))  # 'valeur', 'validation', 'commentaire', etc.
    
    # Qui a modifié
    utilisateur_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    raison_modification: Mapped[Optional[str]] = mapped_column(Text)
    
    # Date
    date_modification: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False)
    
    # Relation
    resultat = relationship("ResultatModel", backref="historique")
    
    def __repr__(self):
        return f"<HistoriqueResultat(resultat={self.resultat_id}, date={self.date_modification})>"
