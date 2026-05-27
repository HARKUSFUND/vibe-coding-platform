"""
Repository Patient - Accès aux données patients
Conforme CDC §4.1, §4.3
"""
from typing import Optional, List
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from igors.infrastructure.models.patient import PatientModel
from igors.core.domain.patient import Patient


class PatientRepository:
    """Repository pour la gestion des patients"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, patient: Patient) -> PatientModel:
        """Créer un nouveau patient"""
        db_patient = PatientModel(
            nir=patient.nir,
            nom=patient.nom,
            prenom=patient.prenom,
            date_naissance=patient.date_naissance,
            sexe=patient.sexe,
            telephone=patient.telephone,
            email=patient.email,
            adresse=patient.adresse,
            ville=patient.ville,
            code_postal=patient.code_postal,
            groupe_sanguin=patient.groupe_sanguin,
            facteur_rhesus=patient.facteur_rhesus,
            antecedents=patient.antecedents,
            traitements_en_cours=patient.traitements_en_cours,
            allergie=patient.allergie,
            medecin_traitant=patient.medecin_traitant,
            personne_a_prevenir=patient.personne_a_prevenir,
            telephone_personne_a_prevenir=patient.telephone_personne_a_prevenir,
            notes=patient.notes
        )
        self.session.add(db_patient)
        self.session.commit()
        self.session.refresh(db_patient)
        return db_patient
    
    def get_by_id(self, patient_id: int) -> Optional[PatientModel]:
        """Récupérer un patient par son ID"""
        return self.session.get(PatientModel, patient_id)
    
    def get_by_nir(self, nir: str) -> Optional[PatientModel]:
        """Récupérer un patient par son NIR"""
        stmt = select(PatientModel).where(PatientModel.nir == nir)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def search(self, search_term: str) -> List[PatientModel]:
        """Rechercher des patients par nom, prénom ou NIR"""
        stmt = select(PatientModel).where(
            or_(
                PatientModel.nom.ilike(f"%{search_term}%"),
                PatientModel.prenom.ilike(f"%{search_term}%"),
                PatientModel.nir.ilike(f"%{search_term}%")
            )
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[PatientModel]:
        """Récupérer tous les patients avec pagination"""
        stmt = select(PatientModel).offset(skip).limit(limit)
        return self.session.execute(stmt).scalars().all()
    
    def update(self, patient_id: int, patient_data: dict) -> Optional[PatientModel]:
        """Mettre à jour un patient"""
        db_patient = self.get_by_id(patient_id)
        if not db_patient:
            return None
        
        for key, value in patient_data.items():
            if hasattr(db_patient, key) and value is not None:
                setattr(db_patient, key, value)
        
        self.session.commit()
        self.session.refresh(db_patient)
        return db_patient
    
    def delete(self, patient_id: int) -> bool:
        """Supprimer un patient (soft delete via statut)"""
        db_patient = self.get_by_id(patient_id)
        if not db_patient:
            return False
        
        db_patient.statut = 'inactive'
        self.session.commit()
        return True
    
    def count(self) -> int:
        """Compter le nombre total de patients"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(PatientModel)
        return self.session.execute(stmt).scalar()
