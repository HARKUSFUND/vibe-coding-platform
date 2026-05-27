"""SQLAlchemy ORM models for IGORS database."""

from .user import User
from .donneur import DonneurModel
from .patient import PatientModel
from .don import DonModel, TubeModel, TypePSLModel
from .poche import PocheModel, QualificationBiologique
from .examen import ExamenModel, GroupeExamensModel, GroupeExamenAssoc
from .resultat import ResultatModel, HistoriqueResultatModel

# Import other models as they are created
# from .prescription import PrescriptionModel
# from .automate import AutomateModel
# from .qualite import CQIModel, EEQModel, CAPAModel, NonConformiteModel
# from .prescripteur import PrescripteurModel
# from .audit import AuditLogModel

__all__ = [
    "User",
    "DonneurModel",
    "PatientModel",
    "DonModel",
    "TubeModel",
    "TypePSLModel",
    "PocheModel",
    "QualificationBiologique",
    "ExamenModel",
    "GroupeExamensModel",
    "GroupeExamenAssoc",
    "ResultatModel",
    "HistoriqueResultatModel",
]
