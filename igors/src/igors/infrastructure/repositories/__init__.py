"""Repositories module - Data access layer."""

from .user_repo import UserRepository
from .donneur_repo import DonneurRepository
from .patient_repo import PatientRepository
from .don_repo import DonRepository
from .poche_repo import PocheRepository
from .examen_repo import ExamenRepository
from .resultat_repo import ResultatRepository
from .prescription_repo import PrescriptionRepository
from .automate_repo import AutomateRepository

__all__ = [
    "UserRepository",
    "DonneurRepository", 
    "PatientRepository",
    "DonRepository",
    "PocheRepository",
    "ExamenRepository",
    "ResultatRepository",
    "PrescriptionRepository",
    "AutomateRepository",
]
