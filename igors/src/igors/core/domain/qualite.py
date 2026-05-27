"""Qualite domain entity - CQI, EEQ, CAPA."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional
from enum import Enum


class StatutCAPA(str, Enum):
    OUVERT = "ouvert"
    EN_COURS = "en_cours"
    RESOLU = "resolu"
    CLOS = "clos"


class TypeNonConformite(str, Enum):
    PRE_ANALYTIQUE = "pre_analytique"
    ANALYTIQUE = "analytique"
    POST_ANALYTIQUE = "post_analytique"
    EQUIPEMENT = "equipement"
    REACTIF = "reactif"
    PERSONNEL = "personnel"
    AUTRE = "autre"


@dataclass
class CQI:
    """Contrôle Qualité Interne - Westgard rules."""

    id: Optional[int] = None
    examen_id: int = 0
    examen_nom: str = ""
    automate_id: Optional[int] = None
    
    # Données du contrôle
    date_heure: datetime = field(default_factory=datetime.now)
    lot_controle: str = ""
    niveau_controle: str = ""  # N1, N2, N3...
    valeur_cible: float = 0.0
    valeur_mesuree: float = 0.0
    ecart_type_cible: float = 0.0
    
    # Règles de Westgard
    regle_1_2s: bool = False  # Warning
    regle_1_3s: bool = False  # Rejet
    regle_2_2s: bool = False
    regle_r_4s: bool = False
    regle_4_1s: bool = False
    regle_10x: bool = False
    
    # Statut
    statut: str = "accepte"  # accepte, rejete
    motif_rejet: str = ""
    action_corrective: str = ""
    
    valide_par: Optional[int] = None
    date_validation: Optional[datetime] = None
    observations: str = ""


@dataclass
class EEQ:
    """Évaluation Externe de la Qualité."""

    id: Optional[int] = None
    organisme_eeq: str = ""  # Laboratoire organisateur
    programme: str = ""
    annee: int = 0
    cycle: int = 0
    
    # Échantillons
    nombre_echantillons: int = 0
    examens_concernes: List[str] = field(default_factory=list)
    
    # Résultats
    date_reception_echantillons: Optional[date] = None
    date_limite_reponse: Optional[date] = None
    date_soumission_resultats: Optional[date] = None
    
    # Évaluation
    performance_globale: str = ""  # Excellent, Satisfaisant, Insatisfaisant
    score_percentile: float = 0.0
    ecarts_identifies: str = ""
    actions_correctives: str = ""
    
    rapport_recu: bool = False
    date_rapport: Optional[date] = None
    fichier_rapport: Optional[str] = None
    
    observations: str = ""
    date_creation: datetime = field(default_factory=datetime.now)


@dataclass
class CAPA:
    """Corrective and Preventive Action - Gestion des non-conformités."""

    id: Optional[int] = None
    numero_capa: str = ""  # Numéro unique
    type_non_conformite: TypeNonConformite = TypeNonConformite.AUTRE
    
    # Description
    titre: str = ""
    description: str = ""
    date_detection: date = field(default_factory=date.today)
    detecte_par: Optional[int] = None  # User ID
    service_concerne: str = ""
    
    # Analyse
    cause_racine: str = ""
    gravite: str = "moyenne"  # faible, moyenne, critique
    risque_recurrence: str = "faible"  # faible, moyen, élevé
    
    # Actions correctives
    action_immediate: str = ""
    date_action_immediate: Optional[date] = None
    responsable_action_immediate: Optional[int] = None
    
    # Actions préventives
    action_preventive: str = ""
    date_prevue: Optional[date] = None
    responsable_preventif: Optional[int] = None
    
    # Suivi
    statut: StatutCAPA = StatutCAPA.OUVERT
    date_resolution: Optional[date] = None
    efficacite_verifiee: bool = False
    date_verification: Optional[date] = None
    
    # Clôture
    clos_par: Optional[int] = None
    date_cloture: Optional[datetime] = None
    commentaires_cloture: str = ""
    
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None

    @property
    def jours_ouverture(self) -> int:
        """Get number of days since opening."""
        delta = date.today() - self.date_detection
        return delta.days

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "numero_capa": self.numero_capa,
            "titre": self.titre,
            "type_non_conformite": self.type_non_conformite.value,
            "statut": self.statut.value,
            "gravite": self.gravite,
            "jours_ouverture": self.jours_ouverture,
        }
