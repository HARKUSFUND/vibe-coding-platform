"""Donneur domain entity."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class Sexe(str, Enum):
    MASCULIN = "M"
    FEMININ = "F"


class GroupeSanguin(str, Enum):
    A_POSITIF = "A+"
    A_NEGATIF = "A-"
    B_POSITIF = "B+"
    B_NEGATIF = "B-"
    AB_POSITIF = "AB+"
    AB_NEGATIF = "AB-"
    O_POSITIF = "O+"
    O_NEGATIF = "O-"


@dataclass
class Donneur:
    """Donneur de sang entity."""

    id: Optional[int] = None
    nir: Optional[str] = None  # Numéro d'identification unique (chiffré)
    nom: str = ""
    prenom: str = ""
    sexe: Sexe = Sexe.MASCULIN
    date_naissance: Optional[date] = None
    lieu_naissance: str = ""
    nationalite: str = "Ivoirienne"
    profession: str = ""
    telephone: str = ""
    email: Optional[str] = None
    adresse: str = ""
    ville: str = ""
    quartier: str = ""
    groupe_sanguin: Optional[GroupeSanguin] = None
    facteur_rhesus: bool = True
    date_premier_don: Optional[date] = None
    nombre_dons: int = 0
    date_dernier_don: Optional[date] = None
    eligible_don: bool = True
    contre_indications: str = ""
    consentement_signe: bool = False
    date_consentement: Optional[datetime] = None
    fichier_consentement: Optional[str] = None  # Path vers le scan
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None
    actif: bool = True

    @property
    def age(self) -> Optional[int]:
        """Calculate donor age."""
        if not self.date_naissance:
            return None
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )

    @property
    def est_majeur(self) -> bool:
        """Check if donor is adult (18+)."""
        return self.age is not None and self.age >= 18

    @property
    def peut_donner(self) -> bool:
        """Check if donor can donate."""
        if not self.est_majeur or not self.eligible_don:
            return False
        if self.date_dernier_don:
            jours_depuis_dernier_don = (date.today() - self.date_dernier_don).days
            # 8 semaines minimum entre deux dons
            if jours_depuis_dernier_don < 56:
                return False
        return True

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "nir": self.nir,
            "nom": self.nom,
            "prenom": self.prenom,
            "sexe": self.sexe.value,
            "date_naissance": self.date_naissance.isoformat() if self.date_naissance else None,
            "groupe_sanguin": self.groupe_sanguin.value if self.groupe_sanguin else None,
            "nombre_dons": self.nombre_dons,
            "eligible_don": self.eligible_don,
        }
