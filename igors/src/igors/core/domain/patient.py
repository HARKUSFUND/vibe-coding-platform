"""Patient domain entity."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional


@dataclass
class Patient:
    """Patient entity for laboratory analysis."""

    id: Optional[int] = None
    nir: Optional[str] = None  # Numéro d'identification unique (chiffré)
    nom: str = ""
    prenom: str = ""
    sexe: str = ""  # M/F
    date_naissance: Optional[date] = None
    lieu_naissance: str = ""
    nationalite: str = "Ivoirienne"
    telephone: str = ""
    email: Optional[str] = None
    adresse: str = ""
    ville: str = ""
    quartier: str = ""
    profession: str = ""
    situation_matrimoniale: str = ""
    groupe_sanguin: Optional[str] = None
    facteur_rhesus: Optional[bool] = None
    antecedents_medicaux: str = ""
    traitements_en_cours: str = ""
    allergies: str = ""
    medecin_traitant: str = ""
    structure_prise_charge: str = ""
    numero_dossier: str = ""  # Numéro de dossier médical
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None
    actif: bool = True

    @property
    def age(self) -> Optional[int]:
        """Calculate patient age."""
        if not self.date_naissance:
            return None
        today = date.today()
        return today.year - self.date_naissance.year - (
            (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day)
        )

    @property
    def est_majeur(self) -> bool:
        """Check if patient is adult (18+)."""
        return self.age is not None and self.age >= 18

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "nir": self.nir,
            "nom": self.nom,
            "prenom": self.prenom,
            "sexe": self.sexe,
            "date_naissance": self.date_naissance.isoformat() if self.date_naissance else None,
            "age": self.age,
            "groupe_sanguin": self.groupe_sanguin,
        }
