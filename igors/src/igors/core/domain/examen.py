"""Examen domain entity - Referentiel des examens (LOINC)."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Examen:
    """Laboratory examination entity with LOINC coding."""

    id: Optional[int] = None
    code_loinc: str = ""  # Code LOINC standard
    nom_court: str = ""  # Nom usuel
    nom_complet: str = ""  # Nom officiel
    type_examen: str = ""  # Biochimie, Hematologie, Immunologie...
    unite_mesure: str = ""  # g/L, mmol/L, UI/L...
    delai_rendu_heures: float = 24.0  # Délai attendu
    prix: float = 0.0
    actif: bool = True
    
    # Valeurs de référence
    valeur_min_adulte: Optional[float] = None
    valeur_max_adulte: Optional[float] = None
    valeur_min_enfant: Optional[float] = None
    valeur_max_enfant: Optional[float] = None
    valeur_critique_basse: Optional[float] = None
    valeur_critique_haute: Optional[float] = None
    
    # Configuration automates
    code_automate: str = ""  # Code sur l'automate
    automate_id: Optional[int] = None
    type_echantillon: str = "serum"  # serum, plasma, sang_total, urines...
    volume_necessaire_ml: float = 5.0
    temperature_conservation: float = 4.0
    
    # Validation
    necessite_validation_manuelle: bool = False
    regles_validation: str = ""  # JSON avec règles de validation
    
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None

    def get_valeurs_reference(self, est_adulte: bool = True) -> tuple:
        """Get reference values based on patient age."""
        if est_adulte:
            return self.valeur_min_adulte, self.valeur_max_adulte
        return self.valeur_min_enfant, self.valeur_max_enfant

    def est_dans_normes(self, valeur: float, est_adulte: bool = True) -> bool:
        """Check if value is within normal range."""
        min_val, max_val = self.get_valeurs_reference(est_adulte)
        if min_val is None or max_val is None:
            return True
        return min_val <= valeur <= max_val

    def est_valeur_critique(self, valeur: float) -> bool:
        """Check if value is critical (panic value)."""
        if self.valeur_critique_basse and valeur < self.valeur_critique_basse:
            return True
        if self.valeur_critique_haute and valeur > self.valeur_critique_haute:
            return True
        return False

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "code_loinc": self.code_loinc,
            "nom_court": self.nom_court,
            "nom_complet": self.nom_complet,
            "unite_mesure": self.unite_mesure,
            "valeur_min_adulte": self.valeur_min_adulte,
            "valeur_max_adulte": self.valeur_max_adulte,
        }
