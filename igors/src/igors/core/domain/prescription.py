"""Prescription domain entity."""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional


@dataclass
class LignePrescription:
    """Single prescription line item."""

    id: Optional[int] = None
    prescription_id: Optional[int] = None
    examen_id: int = 0
    examen_nom: str = ""
    code_loinc: str = ""
    urgent: bool = False
    statut: str = "prescrit"  # prescrit, preleve, en_cours, valide, rendu
    date_prelevement: Optional[datetime] = None
    date_reception: Optional[datetime] = None
    date_validation: Optional[datetime] = None
    date_rendering: Optional[datetime] = None
    observations: str = ""


@dataclass
class Prescription:
    """Medical prescription for laboratory examinations."""

    id: Optional[int] = None
    numero_prescription: str = ""  # Numéro unique
    patient_id: int = 0
    patient_nom: str = ""
    patient_prenom: str = ""
    prescripteur_id: Optional[int] = None
    prescripteur_nom: str = ""
    structure_prescriptrice: str = ""
    date_prescription: date = field(default_factory=date.today)
    date_prelevement_prevu: Optional[date] = None
    type_prelevement: str = ""  # Prise de sang, urines, LCR...
    lieu_prelevement: str = ""
    contexte_clinique: str = ""
    diagnostic_suspecte: str = ""
    traitement_en_cours: str = ""
    lignes: List[LignePrescription] = field(default_factory=list)
    statut: str = "active"  # active, annulee, terminee
    priorite: str = "normale"  # normale, urgente, stat
    mode_entree: str = "manuelle"  # manuelle, import_si
    fichier_import: Optional[str] = None
    date_creation: datetime = field(default_factory=datetime.now)
    date_modification: Optional[datetime] = None

    @property
    def nombre_examens(self) -> int:
        """Get number of prescribed examinations."""
        return len(self.lignes)

    @property
    def examens_urgents(self) -> List[LignePrescription]:
        """Get urgent examinations."""
        return [l for l in self.lignes if l.urgent]

    def ajouter_examen(
        self,
        examen_id: int,
        examen_nom: str,
        code_loinc: str,
        urgent: bool = False,
    ) -> LignePrescription:
        """Add examination to prescription."""
        ligne = LignePrescription(
            prescription_id=self.id,
            examen_id=examen_id,
            examen_nom=examen_nom,
            code_loinc=code_loinc,
            urgent=urgent,
        )
        self.lignes.append(ligne)
        return ligne

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "numero_prescription": self.numero_prescription,
            "patient_id": self.patient_id,
            "patient_nom": self.patient_nom,
            "date_prescription": self.date_prescription.isoformat(),
            "nombre_examens": self.nombre_examens,
            "statut": self.statut,
        }
