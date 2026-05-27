"""Don domain entity - Association entre donneur, tubes et poches."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional
from enum import Enum


class StatutDon(str, Enum):
    PLANIFIE = "planifie"
    EN_COURS = "en_cours"
    TERMINE = "termine"
    ANNULE = "annule"


class TypeDon(str, Enum):
    SANG_TOTAL = "sang_total"
    PLASMA = "plasma"
    PLAQUETTES = "plaquettes"
    GLOBULES_ROUGES = "globules_rouges"


@dataclass
class Tube:
    """Tube de prélèvement."""

    id: Optional[int] = None
    don_id: Optional[int] = None
    code_barres: str = ""
    type_tube: str = ""  # EDTA, sec, héparine...
    volume_ml: float = 0.0
    date_prelevement: datetime = field(default_factory=datetime.now)
    preleve_par: Optional[int] = None  # User ID
    statut: str = "preleve"
    observations: str = ""


@dataclass
class Poche:
    """Poche de sang ou produit sanguin."""

    id: Optional[int] = None
    don_id: Optional[int] = None
    code_barres: str = ""
    type_produit: str = ""  # CPS, PFC, CGR...
    volume_ml: float = 0.0
    groupe_abo: str = ""
    facteur_rhesus: bool = True
    date_prelevement: datetime = field(default_factory=datetime.now)
    date_expiration: Optional[datetime] = None
    statut: str = "preleve"  # preleve, qualifie, disponible, utilise, detruit
    qualification_virologique: Optional[str] = None  # VIH, VHB, VHC, Syphilis...
    resultat_qualification: Optional[str] = None  # negatif, positif, indetermine
    stockage_temperature: float = 4.0  # Température de conservation
    observations: str = ""


@dataclass
class Don:
    """Don de sang entity."""

    id: Optional[int] = None
    donneur_id: int = 0
    code_don: str = ""  # Code unique du don
    type_don: TypeDon = TypeDon.SANG_TOTAL
    statut: StatutDon = StatutDon.PLANIFIE
    date_don: date = field(default_factory=date.today)
    heure_debut: Optional[datetime] = None
    heure_fin: Optional[datetime] = None
    lieu_collecte: str = ""
    equipe_collecte: str = ""
    poids_donneur: float = 0.0
    tension_arterielle: str = ""  # Format "12/8"
    pouls: int = 0
    temperature: float = 36.5
    hemoglobine_pre_don: float = 0.0  # g/dL
    volume_prevu_ml: float = 450.0
    volume_reel_ml: float = 0.0
    anticoagulant: str = "CPDA-1"
    incidents: str = ""
    observations: str = ""
    preleve_par: Optional[int] = None  # User ID
    valide_par: Optional[int] = None  # User ID
    date_validation: Optional[datetime] = None
    tubes: List[Tube] = field(default_factory=list)
    poches: List[Poche] = field(default_factory=list)
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None

    @property
    def duree_minutes(self) -> Optional[int]:
        """Calculate donation duration in minutes."""
        if not self.heure_debut or not self.heure_fin:
            return None
        delta = self.heure_fin - self.heure_debut
        return int(delta.total_seconds() / 60)

    @property
    def est_complete(self) -> bool:
        """Check if donation is complete with all required data."""
        return (
            self.statut == StatutDon.TERMINE
            and self.volume_reel_ml > 0
            and len(self.tubes) > 0
            and len(self.poches) > 0
        )

    def ajouter_tube(
        self,
        code_barres: str,
        type_tube: str,
        volume_ml: float,
        preleve_par: Optional[int] = None,
    ) -> Tube:
        """Add a tube to the donation."""
        tube = Tube(
            don_id=self.id,
            code_barres=code_barres,
            type_tube=type_tube,
            volume_ml=volume_ml,
            preleve_par=preleve_par,
        )
        self.tubes.append(tube)
        return tube

    def ajouter_poche(
        self,
        code_barres: str,
        type_produit: str,
        volume_ml: float,
        groupe_abo: str,
        facteur_rhesus: bool,
    ) -> Poche:
        """Add a blood bag to the donation."""
        poche = Poche(
            don_id=self.id,
            code_barres=code_barres,
            type_produit=type_produit,
            volume_ml=volume_ml,
            groupe_abo=groupe_abo,
            facteur_rhesus=facteur_rhesus,
        )
        self.poches.append(poche)
        return poche

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "code_don": self.code_don,
            "donneur_id": self.donneur_id,
            "type_don": self.type_don.value,
            "statut": self.statut.value,
            "date_don": self.date_don.isoformat(),
            "volume_reel_ml": self.volume_reel_ml,
            "hemoglobine_pre_don": self.hemoglobine_pre_don,
        }
