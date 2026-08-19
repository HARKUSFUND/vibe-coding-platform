# -*- coding: utf-8 -*-
"""
patient_repo.py — Repository pour l'accès aux données des patients

Pattern Repository avec SQLAlchemy 2.0
"""

from typing import List, Optional

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from ..models.patient import PatientModel


class PatientRepository:
    """Repository pour les opérations CRUD sur les patients."""

    def __init__(self, session: Session):
        self.session = session

    def create(self, patient: 'Patient') -> 'Patient':
        """Crée un nouveau patient."""
        from ..domain.patient import Patient as PatientEntity
        
        model = PatientModel(
            Pa_code=patient.Pa_code,
            Pa_nom=patient.Pa_nom,
            Pa_prenom=patient.Pa_prenom,
            Pa_sexe=patient.Pa_sexe,
            Pa_dnaissance=patient.Pa_dnaissance,
            Pa_contact=patient.Pa_contact,
            Pa_adresse=patient.Pa_adresse,
            Pa_groupe_sanguin=patient.Pa_groupe_sanguin,
            Pa_antecedents=patient.Pa_antecedents,
        )
        
        self.session.add(model)
        self.session.commit()
        self.session.refresh(model)
        
        return self._to_entity(model)

    def update(self, code: str, patient: 'Patient') -> 'Patient':
        """Met à jour un patient existant."""
        model = self.session.get(PatientModel, code)
        if not model:
            raise ValueError(f"Patient {code} introuvable")
        
        model.Pa_nom = patient.Pa_nom
        model.Pa_prenom = patient.Pa_prenom
        model.Pa_sexe = patient.Pa_sexe
        model.Pa_dnaissance = patient.Pa_dnaissance
        model.Pa_contact = patient.Pa_contact
        model.Pa_adresse = patient.Pa_adresse
        model.Pa_groupe_sanguin = patient.Pa_groupe_sanguin
        model.Pa_antecedents = patient.Pa_antecedents
        
        self.session.commit()
        self.session.refresh(model)
        
        return self._to_entity(model)

    def delete(self, code: str) -> bool:
        """Supprime un patient."""
        model = self.session.get(PatientModel, code)
        if not model:
            return False
        
        self.session.delete(model)
        self.session.commit()
        return True

    def get_by_code(self, code: str) -> Optional['Patient']:
        """Récupère un patient par son code."""
        from ..domain.patient import Patient as PatientEntity
        
        model = self.session.get(PatientModel, code)
        if not model:
            return None
        
        return self._to_entity(model)

    def get_all(self) -> List['Patient']:
        """Récupère tous les patients."""
        from ..domain.patient import Patient as PatientEntity
        
        stmt = select(PatientModel).order_by(PatientModel.Pa_nom)
        models = self.session.execute(stmt).scalars().all()
        
        return [self._to_entity(m) for m in models]

    def search(self, query: str) -> List['Patient']:
        """Recherche des patients par nom, prénom ou code."""
        from ..domain.patient import Patient as PatientEntity
        
        query_pattern = f"%{query}%"
        stmt = select(PatientModel).where(
            or_(
                PatientModel.Pa_code.ilike(query_pattern),
                PatientModel.Pa_nom.ilike(query_pattern),
                PatientModel.Pa_prenom.ilike(query_pattern),
            )
        ).order_by(PatientModel.Pa_nom)
        
        models = self.session.execute(stmt).scalars().all()
        return [self._to_entity(m) for m in models]

    def _to_entity(self, model: PatientModel) -> 'Patient':
        """Convertit un modèle ORM en entité métier."""
        from ..domain.patient import Patient as PatientEntity
        
        return PatientEntity(
            Pa_code=model.Pa_code,
            Pa_nom=model.Pa_nom,
            Pa_prenom=model.Pa_prenom,
            Pa_sexe=model.Pa_sexe,
            Pa_dnaissance=model.Pa_dnaissance,
            Pa_contact=model.Pa_contact,
            Pa_adresse=model.Pa_adresse,
            Pa_groupe_sanguin=model.Pa_groupe_sanguin,
            Pa_antecedents=model.Pa_antecedents,
        )
