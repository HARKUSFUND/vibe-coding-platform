"""Resultat domain entity - Laboratory analysis results."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Resultat:
    """Laboratory analysis result entity."""

    id: Optional[int] = None
    prescription_ligne_id: Optional[int] = None
    examen_id: int = 0
    examen_nom: str = ""
    code_loinc: str = ""
    patient_id: int = 0
    don_id: Optional[int] = None  # Si résultat lié à un don
    
    # Valeur du résultat
    valeur_numerique: Optional[float] = None
    valeur_texte: Optional[str] = None
    unite_mesure: str = ""
    
    # Interprétation
    valeur_min_reference: Optional[float] = None
    valeur_max_reference: Optional[float] = None
    interpretation: str = ""  # Normal, Bas, Élevé, Critique...
    drapeau: str = ""  # H (high), L (low), HH (very high), LL (very low)
    
    # Validation
    statut: str = "saisi"  # saisi, valide_interne, valide_biologiste, rendu
    date_saisie: datetime = field(default_factory=datetime.now)
    saisie_par: Optional[int] = None  # User ID
    date_validation_interne: Optional[datetime] = None
    valide_interne_par: Optional[int] = None
    date_validation_biologiste: Optional[datetime] = None
    valide_biologiste_par: Optional[int] = None
    signature_electronique: Optional[str] = None  # Hash de signature
    date_signature: Optional[datetime] = None
    
    # Automate
    automate_id: Optional[int] = None
    resultat_brut: Optional[str] = None
    date_reception_automate: Optional[datetime] = None
    
    # Alertes
    est_critique: bool = False
    alerte_envoyee: bool = False
    date_alerte: Optional[datetime] = None
    
    # Commentaires
    commentaire_technique: str = ""
    commentaire_biologiste: str = ""
    observations: str = ""
    
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None

    @property
    def est_valide(self) -> bool:
        """Check if result is validated by biologist."""
        return self.statut in ["valide_interne", "valide_biologiste", "rendu"]

    @property
    def peut_etre_valide(self) -> bool:
        """Check if result can be validated."""
        return (
            self.statut == "saisi"
            and (self.valeur_numerique is not None or self.valeur_texte is not None)
        )

    def calculer_drapeau(self) -> str:
        """Calculate flag based on reference values."""
        if self.valeur_numerique is None:
            return ""
        
        drapeau = ""
        if self.valeur_critique_basse and self.valeur_numerique < self.valeur_critique_basse:
            drapeau = "LL"
        elif self.valeur_critique_haute and self.valeur_numerique > self.valeur_critique_haute:
            drapeau = "HH"
        elif self.valeur_min_reference and self.valeur_numerique < self.valeur_min_reference:
            drapeau = "L"
        elif self.valeur_max_reference and self.valeur_numerique > self.valeur_max_reference:
            drapeau = "H"
        
        self.drapeau = drapeau
        return drapeau

    def interpreter(self) -> str:
        """Generate interpretation text."""
        if not self.valeur_numerique:
            return ""
        
        if self.drapeau == "LL" or self.drapeau == "HH":
            self.interpretation = "Critique"
            self.est_critique = True
        elif self.drapeau == "L":
            self.interpretation = "Bas"
        elif self.drapeau == "H":
            self.interpretation = "Élevé"
        else:
            self.interpretation = "Normal"
        
        return self.interpretation

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "examen_nom": self.examen_nom,
            "valeur": self.valeur_numerique or self.valeur_texte,
            "unite_mesure": self.unite_mesure,
            "interpretation": self.interpretation,
            "drapeau": self.drapeau,
            "statut": self.statut,
        }
