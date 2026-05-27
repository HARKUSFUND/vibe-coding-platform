"""
Service Patient - Gestion des patients
Conforme CDC §4.1, §4.3 - Dossier patient et historique
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from igors.infrastructure.repositories.patient_repo import PatientRepository
from igors.infrastructure.repositories.resultat_repo import ResultatRepository
from igors.core.domain.patient import Patient


class PatientService:
    """Service métier pour la gestion des patients"""
    
    def __init__(self, session: Session):
        self.session = session
        self.patient_repo = PatientRepository(session)
        self.resultat_repo = ResultatRepository(session)
    
    def creer_patient(self, patient: Patient) -> Dict:
        """Créer un nouveau patient"""
        try:
            # Vérifier si le NIR existe déjà
            existing = self.patient_repo.get_by_nir(patient.nir)
            if existing:
                return {
                    'success': False,
                    'error': 'Un patient avec ce NIR existe déjà',
                    'patient_id': existing.id
                }
            
            db_patient = self.patient_repo.create(patient)
            return {
                'success': True,
                'patient_id': db_patient.id,
                'message': f'Patient {patient.nom} {patient.prenom} créé avec succès'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_patient(self, patient_id: int) -> Optional[Dict]:
        """Récupérer les informations d'un patient"""
        db_patient = self.patient_repo.get_by_id(patient_id)
        if not db_patient:
            return None
        
        return {
            'id': db_patient.id,
            'nir': db_patient.nir,
            'nom': db_patient.nom,
            'prenom': db_patient.prenom,
            'date_naissance': db_patient.date_naissance,
            'sexe': db_patient.sexe,
            'telephone': db_patient.telephone,
            'email': db_patient.email,
            'adresse': db_patient.adresse,
            'ville': db_patient.ville,
            'code_postal': db_patient.code_postal,
            'groupe_sanguin': db_patient.groupe_sanguin,
            'facteur_rhesus': db_patient.facteur_rhesus,
            'antecedents': db_patient.antecedents,
            'traitements_en_cours': db_patient.traitements_en_cours,
            'allergie': db_patient.allergie,
            'medecin_traitant': db_patient.medecin_traitant,
            'statut': db_patient.statut,
            'date_creation': db_patient.date_creation,
            'date_modification': db_patient.date_modification
        }
    
    def search_patients(self, search_term: str) -> List[Dict]:
        """Rechercher des patients"""
        db_patients = self.patient_repo.search(search_term)
        return [
            {
                'id': p.id,
                'nom': p.nom,
                'prenom': p.prenom,
                'nir': p.nir,
                'date_naissance': p.date_naissance,
                'sexe': p.sexe,
                'telephone': p.telephone
            }
            for p in db_patients
        ]
    
    def get_all_patients(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Récupérer tous les patients avec pagination"""
        db_patients = self.patient_repo.get_all(skip, limit)
        return [
            {
                'id': p.id,
                'nom': p.nom,
                'prenom': p.prenom,
                'nir': p.nir,
                'date_naissance': p.date_naissance,
                'sexe': p.sexe
            }
            for p in db_patients
        ]
    
    def update_patient(self, patient_id: int, patient_data: dict) -> Dict:
        """Mettre à jour un patient"""
        try:
            db_patient = self.patient_repo.update(patient_id, patient_data)
            if not db_patient:
                return {
                    'success': False,
                    'error': 'Patient non trouvé'
                }
            
            return {
                'success': True,
                'patient_id': db_patient.id,
                'message': 'Patient mis à jour avec succès'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def delete_patient(self, patient_id: int) -> Dict:
        """Supprimer (désactiver) un patient"""
        try:
            success = self.patient_repo.delete(patient_id)
            if not success:
                return {
                    'success': False,
                    'error': 'Patient non trouvé'
                }
            
            return {
                'success': True,
                'message': 'Patient désactivé avec succès'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_historique_resultats(self, patient_id: int, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Récupérer l'historique des résultats d'un patient"""
        db_resultats = self.resultat_repo.get_by_patient(patient_id, skip, limit)
        return [
            {
                'id': r.id,
                'examen_id': r.examen_id,
                'examen_nom': r.examen.nom if r.examen else None,
                'valeur': r.valeur_texte,
                'unite': r.unite,
                'date_prelevement': r.date_prelevement,
                'date_validation': r.date_validation,
                'statut': r.statut_validation
            }
            for r in db_resultats
        ]
    
    def get_patient_by_nir(self, nir: str) -> Optional[Dict]:
        """Récupérer un patient par son NIR"""
        db_patient = self.patient_repo.get_by_nir(nir)
        if not db_patient:
            return None
        
        return self.get_patient(db_patient.id)
    
    def count_patients(self) -> int:
        """Compter le nombre total de patients"""
        return self.patient_repo.count()
    
    def get_statistics(self) -> Dict:
        """Obtenir des statistiques sur les patients"""
        return {
            'total_patients': self.count_patients(),
            'patients_actifs': len([p for p in self.get_all_patients(limit=10000) if p.get('statut') == 'active']),
            'repartition_sexe': self._get_repartition_sexe(),
            'repartition_groupe_sanguin': self._get_repartition_groupe_sanguin()
        }
    
    def _get_repartition_sexe(self) -> Dict:
        """Répartition par sexe"""
        patients = self.get_all_patients(limit=10000)
        repartition = {'M': 0, 'F': 0, 'Autre': 0, 'Non renseigné': 0}
        for p in patients:
            sexe = p.get('sexe', 'Non renseigné')
            if sexe in repartition:
                repartition[sexe] += 1
            else:
                repartition['Non renseigné'] += 1
        return repartition
    
    def _get_repartition_groupe_sanguin(self) -> Dict:
        """Répartition par groupe sanguin"""
        patients = self.get_all_patients(limit=10000)
        repartition = {}
        for p in patients:
            groupe = p.get('groupe_sanguin', 'Inconnu')
            rhesus = p.get('facteur_rhesus', '')
            key = f"{groupe}{rhesus}" if groupe != 'Inconnu' else 'Inconnu'
            repartition[key] = repartition.get(key, 0) + 1
        return repartition
