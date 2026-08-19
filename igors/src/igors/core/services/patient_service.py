# -*- coding: utf-8 -*-
"""
patient_service.py — Service métier pour la gestion des patients

Fonctionnalités :
- CRUD complet des patients
- Calcul de l'âge
- Validation des données
- Historique des prescriptions

Architecture : Domain-Driven Design
"""

from datetime import datetime
from typing import List, Optional, Dict, Any

from ...infrastructure.repositories.patient_repo import PatientRepository
from ...core.domain.patient import Patient


class PatientService:
    """Service métier pour la gestion des patients."""

    def __init__(self, patient_repo: PatientRepository):
        self.patient_repo = patient_repo

    def create_patient(self, patient_data: Dict[str, Any]) -> Patient:
        """Crée un nouveau patient."""
        # Validation
        if not patient_data.get('Pa_nom'):
            raise ValueError("Le nom du patient est obligatoire")
        if not patient_data.get('Pa_prenom'):
            raise ValueError("Le prénom du patient est obligatoire")
        
        # Vérifier doublon code
        existing = self.patient_repo.get_by_code(patient_data.get('Pa_code', ''))
        if existing:
            raise ValueError(f"Le code patient {patient_data['Pa_code']} existe déjà")
        
        # Création entité
        patient = Patient(
            Pa_code=patient_data.get('Pa_code', f"PA{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            Pa_nom=patient_data.get('Pa_nom', '').upper(),
            Pa_prenom=patient_data.get('Pa_prenom', '').title(),
            Pa_sexe=patient_data.get('Pa_sexe', 'M'),
            Pa_dnaissance=self._parse_date(patient_data.get('Pa_dnaissance')),
            Pa_contact=patient_data.get('Pa_contact', ''),
            Pa_adresse=patient_data.get('Pa_adresse', ''),
            Pa_groupe_sanguin=patient_data.get('Pa_groupe_sanguin', ''),
            Pa_antecedents=patient_data.get('Pa_antecedents', ''),
        )
        
        # Sauvegarde
        return self.patient_repo.create(patient)

    def update_patient(self, code: str, patient_data: Dict[str, Any]) -> Patient:
        """Met à jour un patient existant."""
        existing = self.patient_repo.get_by_code(code)
        if not existing:
            raise ValueError(f"Patient {code} introuvable")
        
        # Mise à jour entité
        patient = Patient(
            Pa_code=code,
            Pa_nom=patient_data.get('Pa_nom', existing.Pa_nom).upper(),
            Pa_prenom=patient_data.get('Pa_prenom', existing.Pa_prenom).title(),
            Pa_sexe=patient_data.get('Pa_sexe', existing.Pa_sexe),
            Pa_dnaissance=self._parse_date(patient_data.get('Pa_dnaissance')) or existing.Pa_dnaissance,
            Pa_contact=patient_data.get('Pa_contact', existing.Pa_contact),
            Pa_adresse=patient_data.get('Pa_adresse', existing.Pa_adresse),
            Pa_groupe_sanguin=patient_data.get('Pa_groupe_sanguin', existing.Pa_groupe_sanguin),
            Pa_antecedents=patient_data.get('Pa_antecedents', existing.Pa_antecedents),
        )
        
        return self.patient_repo.update(code, patient)

    def delete_patient(self, code: str) -> bool:
        """Supprime un patient."""
        return self.patient_repo.delete(code)

    def get_patient(self, code: str) -> Optional[Patient]:
        """Récupère un patient par son code."""
        return self.patient_repo.get_by_code(code)

    def get_all_patients(self) -> List[Patient]:
        """Récupère tous les patients."""
        return self.patient_repo.get_all()

    def search_patients(self, query: str) -> List[Patient]:
        """Recherche des patients par nom, prénom ou code."""
        all_patients = self.patient_repo.get_all()
        query_lower = query.lower()
        
        return [
            p for p in all_patients
            if query_lower in p.Pa_code.lower()
            or query_lower in p.Pa_nom.lower()
            or query_lower in p.Pa_prenom.lower()
        ]

    def calculate_age(self, dnaissance: Optional[datetime]) -> int:
        """Calcule l'âge à partir de la date de naissance."""
        if not dnaissance:
            return 0
        
        today = datetime.now()
        age = today.year - dnaissance.year
        if (today.month, today.day) < (dnaissance.month, dnaissance.day):
            age -= 1
        return age

    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse une date depuis différents formats."""
        if not date_str:
            return None
        
        formats = ["%Y-%m-%d", "%d/%m/%Y", "%Y%m%d"]
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return None
