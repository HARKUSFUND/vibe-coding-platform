"""PSL domain entity - Produits Sanguins Labiles."""

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Optional
from enum import Enum


class TypePSL(str, Enum):
    """Types de produits sanguins labiles."""

    CGR = "CGR"  # Concentré de Globules Rouges
    PFC = "PFC"  # Plasma Frais Congelé
    CPS = "CPS"  # Concentré de Plaquettes Standard
    CPA = "CPA"  # Concentré de Plaquettes d'Aphérèse
    SANG_TOTAL = "SANG_TOTAL"


@dataclass
class ProduitSanguin:
    """Blood product entity."""

    id: Optional[int] = None
    code_barres: str = ""
    type_produit: TypePSL = TypePSL.CGR
    don_id: Optional[int] = None
    
    # Caractéristiques
    groupe_abo: str = ""
    facteur_rhesus: bool = True
    phenotype: str = ""  # Kell, Duffy, Kidd...
    volume_ml: float = 0.0
    
    # Dates
    date_prelevement: datetime = field(default_factory=datetime.now)
    date_expiration: Optional[datetime] = None
    date_congelation: Optional[datetime] = None  # Pour PFC
    
    # Statut et stockage
    statut: str = "preleve"  # preleve, en_qualification, qualifie, disponible, reserve, delivre, utilise, detruit
    temperature_conservation: float = 4.0
    lieu_stockage: str = ""  # Chambre froide, congélateur...
    emplacement: str = ""
    
    # Qualification biologique
    qualification_vih: Optional[str] = None  # negatif, positif, indetermine
    qualification_vhb: Optional[str] = None
    qualification_vhc: Optional[str] = None
    qualification_syphilis: Optional[str] = None
    qualification_htlv: Optional[str] = None
    qualification_paludisme: Optional[str] = None
    date_qualification: Optional[datetime] = None
    qualifie_par: Optional[int] = None
    
    # Traçabilité
    numero_lot: str = ""
    etablissement_origine: str = ""
    date_reception: Optional[datetime] = None
    
    # Distribution
    date_delivrance: Optional[datetime] = None
    delivre_a: str = ""  # Service hospitalier
    prescription_id: Optional[int] = None
    patient_id: Optional[int] = None
    
    # Alertes
    alerte_expiration: bool = False
    rappel_produit: bool = False
    motif_rappel: str = ""
    
    observations: str = ""
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None

    @property
    def duree_conservation_jours(self) -> int:
        """Get conservation duration in days based on product type."""
        durees = {
            TypePSL.CGR: 42,  # 42 jours à +4°C
            TypePSL.PFC: 365,  # 1 an congelé
            TypePSL.CPS: 5,  # 5 jours à +22°C
            TypePSL.CPA: 5,  # 5 jours à +22°C
            TypePSL.SANG_TOTAL: 35,  # 35 jours à +4°C
        }
        return durees.get(self.type_produit, 35)

    def calculer_date_expiration(self) -> datetime:
        """Calculate expiration date based on product type."""
        if self.date_prelevement:
            jours = self.duree_conservation_jours
            self.date_expiration = self.date_prelevement + timedelta(days=jours)
        return self.date_expiration or datetime.now()

    @property
    def jours_restants(self) -> int:
        """Get remaining days before expiration."""
        if not self.date_expiration:
            return 0
        delta = self.date_expiration - datetime.now()
        return max(0, delta.days)

    @property
    def est_perime(self) -> bool:
        """Check if product is expired."""
        return self.jours_restants == 0 and self.statut != "utilise"

    @property
    def expire_bientot(self) -> bool:
        """Check if product expires soon (within 7 days)."""
        return 0 < self.jours_restants <= 7

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "code_barres": self.code_barres,
            "type_produit": self.type_produit.value,
            "groupe_abo": self.groupe_abo,
            "facteur_rhesus": "+" if self.facteur_rhesus else "-",
            "statut": self.statut,
            "date_expiration": self.date_expiration.isoformat() if self.date_expiration else None,
            "jours_restants": self.jours_restants,
        }
