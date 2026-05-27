"""
Repository pour la gestion des prescriptions et prescripteurs.
Conforme CDC §4.1, §4.3
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from ...infrastructure.models.prescription import (
    PrescripteurModel,
    PrescriptionModel,
    ExamenPrescritModel
)
from ...core.domain.prescription import Prescripteur, Prescription


class PrescripteurRepository:
    """Repository pour les prescripteurs."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, prescripteur_id: int) -> Optional[PrescripteurModel]:
        """Récupérer un prescripteur par ID."""
        return self.session.get(PrescripteurModel, prescripteur_id)
    
    def get_by_code(self, code: str) -> Optional[PrescripteurModel]:
        """Récupérer un prescripteur par code."""
        stmt = select(PrescripteurModel).where(PrescripteurModel.code == code)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_all(self, actif_only: bool = True) -> List[PrescripteurModel]:
        """Récupérer tous les prescripteurs."""
        stmt = select(PrescripteurModel)
        if actif_only:
            stmt = stmt.where(PrescripteurModel.actif == True)
        stmt = stmt.order_by(PrescripteurModel.nom)
        return self.session.execute(stmt).scalars().all()
    
    def search(self, terme: str) -> List[PrescripteurModel]:
        """Rechercher des prescripteurs par nom, structure ou spécialité."""
        terme_lower = f"%{terme.lower()}%"
        stmt = select(PrescripteurModel).where(
            (func.lower(PrescripteurModel.nom).like(terme_lower)) |
            (func.lower(PrescripteurModel.prenom).like(terme_lower)) |
            (func.lower(PrescripteurModel.structure).like(terme_lower)) |
            (func.lower(PrescripteurModel.specialite).like(terme_lower))
        ).order_by(PrescripteurModel.nom)
        return self.session.execute(stmt).scalars().all()
    
    def create(self, prescripteur_data: dict) -> PrescripteurModel:
        """Créer un nouveau prescripteur."""
        prescripteur = PrescripteurModel(**prescripteur_data)
        self.session.add(prescripteur)
        self.session.flush()  # Pour obtenir l'ID
        return prescripteur
    
    def update(self, prescripteur_id: int, update_data: dict) -> Optional[PrescripteurModel]:
        """Mettre à jour un prescripteur."""
        prescripteur = self.get_by_id(prescripteur_id)
        if prescripteur:
            for key, value in update_data.items():
                if hasattr(prescripteur, key):
                    setattr(prescripteur, key, value)
            prescripteur.date_modification = datetime.utcnow()
        return prescripteur
    
    def delete(self, prescripteur_id: int) -> bool:
        """Supprimer (désactiver) un prescripteur."""
        prescripteur = self.get_by_id(prescripteur_id)
        if prescripteur:
            prescripteur.actif = False
            prescripteur.date_modification = datetime.utcnow()
            return True
        return False


class PrescriptionRepository:
    """Repository pour les prescriptions."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, prescription_id: int) -> Optional[PrescriptionModel]:
        """Récupérer une prescription par ID avec relations."""
        stmt = (
            select(PrescriptionModel)
            .where(PrescriptionModel.id == prescription_id)
            .options(
                joinedload(PrescriptionModel.patient),
                joinedload(PrescriptionModel.prescripteur),
                joinedload(PrescriptionModel.examens).joinedload(ExamenPrescritModel.examen)
            )
        )
        return self.session.execute(stmt).unique().scalar_one_or_none()
    
    def get_by_numero(self, numero: str) -> Optional[PrescriptionModel]:
        """Récupérer une prescription par numéro."""
        stmt = select(PrescriptionModel).where(PrescriptionModel.numero == numero)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_by_patient(self, patient_id: int) -> List[PrescriptionModel]:
        """Récupérer toutes les prescriptions d'un patient."""
        stmt = (
            select(PrescriptionModel)
            .where(PrescriptionModel.patient_id == patient_id)
            .order_by(PrescriptionModel.date_prescription.desc())
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_en_attente(self) -> List[PrescriptionModel]:
        """Récupérer les prescriptions en attente de réalisation."""
        stmt = (
            select(PrescriptionModel)
            .where(PrescriptionModel.statut == "ACTIVE")
            .order_by(PrescriptionModel.date_prescription)
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_urgentes(self) -> List[PrescriptionModel]:
        """Récupérer les prescriptions urgentes."""
        stmt = (
            select(PrescriptionModel)
            .where(
                (PrescriptionModel.statut == "ACTIVE") &
                (PrescriptionModel.urgence == True)
            )
            .order_by(PrescriptionModel.date_prescription)
        )
        return self.session.execute(stmt).scalars().all()
    
    def create(self, prescription_data: dict, examens: List[dict] = None) -> PrescriptionModel:
        """Créer une nouvelle prescription avec examens."""
        prescription = PrescriptionModel(**prescription_data)
        self.session.add(prescription)
        self.session.flush()
        
        # Ajouter les examens prescrits
        if examens:
            for examen_data in examens:
                examen_prescrit = ExamenPrescritModel(
                    prescription_id=prescription.id,
                    **examen_data
                )
                self.session.add(examen_prescrit)
        
        return prescription
    
    def update_statut(self, prescription_id: int, statut: str, 
                      date_realisation: datetime = None) -> Optional[PrescriptionModel]:
        """Mettre à jour le statut d'une prescription."""
        prescription = self.get_by_id(prescription_id)
        if prescription:
            prescription.statut = statut
            if date_realisation:
                prescription.date_realisation = date_realisation
            prescription.date_modification = datetime.utcnow()
        return prescription
    
    def get_stats_period(self, date_debut: datetime, date_fin: datetime) -> dict:
        """Obtenir des statistiques sur une période."""
        # Nombre total de prescriptions
        stmt_total = select(func.count(PrescriptionModel.id)).where(
            (PrescriptionModel.date_prescription >= date_debut) &
            (PrescriptionModel.date_prescription <= date_fin)
        )
        total = self.session.execute(stmt_total).scalar()
        
        # Par statut
        stmt_statut = select(
            PrescriptionModel.statut,
            func.count(PrescriptionModel.id)
        ).where(
            (PrescriptionModel.date_prescription >= date_debut) &
            (PrescriptionModel.date_prescription <= date_fin)
        ).group_by(PrescriptionModel.statut)
        par_statut = dict(self.session.execute(stmt_statut).all())
        
        # Urgentes vs normales
        stmt_urgentes = select(func.count(PrescriptionModel.id)).where(
            (PrescriptionModel.date_prescription >= date_debut) &
            (PrescriptionModel.date_prescription <= date_fin) &
            (PrescriptionModel.urgence == True)
        )
        urgentes = self.session.execute(stmt_urgentes).scalar()
        
        return {
            "total": total,
            "par_statut": par_statut,
            "urgentes": urgentes,
            "normales": total - urgentes
        }
