"""
Modèle ORM pour la journalisation des accès et actions (Audit Trail).
Conforme CDC §3.4, §5.4 - Traçabilité immuable
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from ..base import Base


class AuditLogModel(Base):
    """
    Table de journalisation des accès et actions utilisateur.
    Cette table est IMMUTABLE - aucune modification ou suppression n'est autorisée.
    Conforme aux exigences de traçabilité ISO 15189 et loi 2013-450.
    """
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Identification de l'action
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    # LOGIN, LOGOUT, CREATE, READ, UPDATE, DELETE, VALIDATION, SIGNATURE, EXPORT, etc.
    
    # Entité concernée
    entite: Mapped[Optional[str]] = mapped_column(String(50))  # PATIENT, DONNEUR, DON, RESULTAT, etc.
    entite_id: Mapped[Optional[int]] = mapped_column(Integer)  # ID de l'entité
    
    # Utilisateur ayant effectué l'action
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    username: Mapped[str] = mapped_column(String(50), nullable=False)  # Copie du username (au cas où user supprimé)
    
    # Détails de l'action
    description: Mapped[Optional[str]] = mapped_column(Text)
    donnees_avant: Mapped[Optional[str]] = mapped_column(Text)  # JSON état avant modification
    donnees_apres: Mapped[Optional[str]] = mapped_column(Text)  # JSON état après modification
    
    # Contexte technique
    adresse_ip: Mapped[Optional[str]] = mapped_column(String(50))  # IP du poste client
    nom_poste: Mapped[Optional[str]] = mapped_column(String(100))  # Nom du poste de travail
    user_agent: Mapped[Optional[str]] = mapped_column(String(200))  # Navigateur/application
    
    # Session
    session_id: Mapped[Optional[str]] = mapped_column(String(100))  # ID de session
    
    # Statut de l'action
    succes: Mapped[bool] = mapped_column(Boolean, default=True)
    message_erreur: Mapped[Optional[str]] = mapped_column(Text)
    
    # Horodatage (critique pour la traçabilité)
    horodatage: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Signature d'intégrité (pour garantir l'immuabilité)
    hash_precedent: Mapped[Optional[str]] = mapped_column(String(64))  # Hash du log précédent (chaîne de blocs)
    hash_actuel: Mapped[Optional[str]] = mapped_column(String(64))  # Hash de cet enregistrement

    def __repr__(self) -> str:
        return f"<AuditLog(id={self.id}, action='{self.action}', user='{self.username}', date='{self.horodatage}')>"


class SessionLogModel(Base):
    """Journal des sessions utilisateurs."""
    __tablename__ = "session_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Informations de session
    session_id: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    adresse_ip: Mapped[str] = mapped_column(String(50))
    nom_poste: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Authentification
    methode_auth: Mapped[str] = mapped_column(String(20), default="PASSWORD")  # PASSWORD, OTP, JWT
    otp_utilise: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Durées
    date_connexion: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_deconnexion: Mapped[Optional[datetime]] = mapped_column(DateTime)
    raison_deconnexion: Mapped[Optional[str]] = mapped_column(String(50))
    # VOLONTAIRE, TIMEOUT, EXPIRATION_TOKEN, DECONNECTE_ADMIN, ERREUR
    
    # Statut
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    def __repr__(self) -> str:
        return f"<SessionLog(user='{self.username}', session_id='{self.session_id}', active={self.active})>"


class AccesDonneesLogModel(Base):
    """
    Journal spécifique des accès aux données sensibles.
    Particulièrement important pour les résultats VIH (anonymisation CDC §4.2)
    et les informations personnelles des donneurs/patients.
    """
    __tablename__ = "acces_donnees_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    
    # Type de donnée accédée
    type_donnee: Mapped[str] = mapped_column(String(50), nullable=False)
    # RESULTAT_VIH, NIR, CONSENTEMENT, IDENTITE_DONNEUR, etc.
    
    # Entité concernée
    entite: Mapped[str] = mapped_column(String(50), nullable=False)
    entite_id: Mapped[int] = mapped_column(nullable=False)
    
    # Utilisateur
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    
    # Action
    action: Mapped[str] = mapped_column(String(20), nullable=False)  # CONSULTATION, EXPORT, IMPRESSION
    justification: Mapped[Optional[str]] = mapped_column(Text)  # Motif de l'accès (si requis)
    
    # Contexte
    contexte: Mapped[Optional[str]] = mapped_column(String(100))  # VALIDATION, URGENCE, RECHERCHE
    horodatage: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self) -> str:
        return f"<AccesDonneesLog(type='{self.type_donnee}', entite_id={self.entite_id}, user='{self.username}')>"


# Configuration spéciale pour rendre la table audit_logs immuable
# Ceci doit être appliqué au niveau de la base de données via migration:
# 
# ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_no_update 
#     CHECK (FALSE); -- Empêche tout UPDATE
# 
# ALTER TABLE audit_logs ADD CONSTRAINT chk_audit_no_delete
#     CHECK (FALSE); -- Empêche tout DELETE
#
# En pratique, on utilise des triggers PostgreSQL pour implémenter cette contrainte.
