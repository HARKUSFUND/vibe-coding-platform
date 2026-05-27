"""
Modèle ORM pour la communication avec les automates.
Conforme CDC §4.4 (ASTM E1381/E1394, HL7)
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import String, Text, DateTime, Boolean, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import Base


class AutomateModel(Base):
    """Table des automates de laboratoire."""
    __tablename__ = "automates"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    fabricant: Mapped[str] = mapped_column(String(100))
    modele: Mapped[str] = mapped_column(String(100))
    numero_serie: Mapped[Optional[str]] = mapped_column(String(100))
    
    # Configuration communication
    protocole: Mapped[str] = mapped_column(String(20), default="ASTM")  # ASTM, HL7, PROPRIETAIRE
    port_serie: Mapped[Optional[str]] = mapped_column(String(50))  # COM1, COM2, etc.
    baud_rate: Mapped[Optional[int]] = mapped_column(Integer, default=9600)
    adresse_ip: Mapped[Optional[str]] = mapped_column(String(50))
    port_tcp: Mapped[Optional[int]] = mapped_column(Integer)
    
    # Paramètres ASTM
    sender_id: Mapped[Optional[str]] = mapped_column(String(50))  # ID émetteur
    receiver_id: Mapped[Optional[str]] = mapped_column(String(50))  # ID récepteur
    
    # Statut
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    statut_connection: Mapped[str] = mapped_column(String(20), default="DECONNECTE")
    dernier_ping: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Métadonnées
    date_installation: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_derniere_maintenance: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_modification: Mapped[Optional[datetime]] = mapped_column(DateTime, onupdate=datetime.utcnow)

    # Relations
    mapping_examens: Mapped[List["AutomateExamenMappingModel"]] = relationship(
        "AutomateExamenMappingModel", back_populates="automate", cascade="all, delete-orphan"
    )
    logs_communication: Mapped[List["AutomateLogModel"]] = relationship(
        "AutomateLogModel", back_populates="automate", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Automate(code='{self.code}', nom='{self.nom}', protocole='{self.protocole}')>"


class AutomateExamenMappingModel(Base):
    """Table de mapping entre codes automate et examens laboratoire."""
    __tablename__ = "automate_examen_mapping"

    id: Mapped[int] = mapped_column(primary_key=True)
    automate_id: Mapped[int] = mapped_column(ForeignKey("automates.id"), nullable=False)
    examen_id: Mapped[int] = mapped_column(ForeignKey("examens.id"), nullable=False)
    
    # Codes automate
    code_automate: Mapped[str] = mapped_column(String(50), nullable=False)  # Code tel qu'envoyé par l'automate
    nom_automate: Mapped[Optional[str]] = mapped_column(String(100))  # Nom tel qu'affiché par l'automate
    
    # Configuration
    unite_automate: Mapped[Optional[str]] = mapped_column(String(50))  # Unité de mesure automate
    facteur_conversion: Mapped[Optional[float]] = mapped_column(default=1.0)  # Pour conversion unités
    decimales: Mapped[Optional[int]] = mapped_column(Integer, default=2)
    
    # Statut
    actif: Mapped[bool] = mapped_column(Boolean, default=True)
    validation_auto: Mapped[bool] = mapped_column(Boolean, default=False)  # Validation automatique si OK
    
    # Métadonnées
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cree_par: Mapped[Optional[str]] = mapped_column(String(50))

    # Relations
    automate: Mapped["AutomateModel"] = relationship("AutomateModel", back_populates="mapping_examens")
    examen: Mapped["ExamenModel"] = relationship("ExamenModel", back_populates="mappings_automates")

    def __repr__(self) -> str:
        return f"<Mapping(automate_id={self.automate_id}, code_automate='{self.code_automate}')>"


class AutomateLogModel(Base):
    """Journal des communications avec les automates (audit trail)."""
    __tablename__ = "automate_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    automate_id: Mapped[int] = mapped_column(ForeignKey("automates.id"), nullable=False)
    
    # Type d'événement
    type_evenement: Mapped[str] = mapped_column(String(50), nullable=False)
    # CONNECTION, DECONNECTION, WORKLIST_REQUEST, RESULTAT_RECU, ERREUR, etc.
    
    # Données brutes
    donnees_brutes: Mapped[Optional[str]] = mapped_column(Text)  # Message ASTM/HL7 brut
    direction: Mapped[str] = mapped_column(String(10))  # ENVOI, RECEPTION
    
    # Statut
    statut: Mapped[str] = mapped_column(String(20), default="SUCCES")  # SUCCES, ECHEC, TIMEOUT
    message_erreur: Mapped[Optional[str]] = mapped_column(Text)
    
    # Contexte
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id"))
    don_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dons.id"))
    numero_commande: Mapped[Optional[str]] = mapped_column(String(50))  # Worklist query ID
    
    # Timestamp
    horodatage: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    # Relations
    automate: Mapped["AutomateModel"] = relationship("AutomateModel", back_populates="logs_communication")

    def __repr__(self) -> str:
        return f"<AutomateLog(automate_id={self.automate_id}, type='{self.type_evenement}', date='{self.horodatage}')>"


class WorklistQueueModel(Base):
    """File d'attente pour les requêtes worklist (Host Query)."""
    __tablename__ = "worklist_queue"

    id: Mapped[int] = mapped_column(primary_key=True)
    automate_id: Mapped[int] = mapped_column(ForeignKey("automates.id"), nullable=False)
    
    # Informations patient/donneur
    patient_id: Mapped[Optional[int]] = mapped_column(ForeignKey("patients.id"))
    don_id: Mapped[Optional[int]] = mapped_column(ForeignKey("dons.id"))
    
    # Identifiants
    numero_commande: Mapped[str] = mapped_column(String(50), unique=True)
    barcode: Mapped[Optional[str]] = mapped_column(String(50))  # Code-barres tube/poche
    
    # Examens demandés
    examens_codes: Mapped[str] = mapped_column(Text)  # Liste des codes examens (JSON ou CSV)
    
    # Statut
    statut: Mapped[str] = mapped_column(String(20), default="EN_ATTENTE")
    # EN_ATTENTE, ENVOYEE, ACQUITEE, ANNULEE
    date_demande: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    date_envoi: Mapped[Optional[datetime]] = mapped_column(DateTime)
    date_acquittement: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    # Erreurs
    nombre_tentatives: Mapped[int] = mapped_column(Integer, default=0)
    derniere_erreur: Mapped[Optional[str]] = mapped_column(Text)

    def __repr__(self) -> str:
        return f"<WorklistQueue(numero_commande='{self.numero_commande}', statut='{self.statut}')>"


# Import tardif pour éviter les circular imports
from .examen import ExamenModel
from .patient import PatientModel
from .don import DonModel
