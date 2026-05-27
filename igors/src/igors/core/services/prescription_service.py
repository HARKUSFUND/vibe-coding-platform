"""
Service métier pour la gestion des prescriptions.
Conforme CDC §4.1, §4.3
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from ...core.domain.prescription import Prescription, Prescripteur
from ...infrastructure.repositories.prescription_repo import (
    PrescripteurRepository,
    PrescriptionRepository
)


class PrescriptionService:
    """Service métier pour les prescriptions."""
    
    def __init__(self, session: Session):
        self.session = session
        self.prescription_repo = PrescriptionRepository(session)
        self.prescripteur_repo = PrescripteurRepository(session)
    
    # === Gestion des prescripteurs ===
    
    def get_prescripteur(self, prescripteur_id: int) -> Optional[dict]:
        """Récupérer un prescripteur."""
        prescripteur = self.prescripteur_repo.get_by_id(prescripteur_id)
        if prescripteur:
            return {
                "id": prescripteur.id,
                "code": prescripteur.code,
                "nom": prescripteur.nom,
                "prenom": prescripteur.prenom,
                "structure": prescripteur.structure,
                "adresse": prescripteur.adresse,
                "telephone": prescripteur.telephone,
                "email": prescripteur.email,
                "specialite": prescripteur.specialite,
                "numero_ordre": prescripteur.numero_ordre,
                "actif": prescripteur.actif
            }
        return None
    
    def list_prescripteurs(self, actif_only: bool = True) -> List[dict]:
        """Lister tous les prescripteurs."""
        prescripteurs = self.prescripteur_repo.get_all(actif_only=actif_only)
        return [{
            "id": p.id,
            "code": p.code,
            "nom": p.nom,
            "prenom": p.prenom,
            "structure": p.structure,
            "specialite": p.specialite,
            "actif": p.actif
        } for p in prescripteurs]
    
    def search_prescripteurs(self, terme: str) -> List[dict]:
        """Rechercher des prescripteurs."""
        prescripteurs = self.prescripteur_repo.search(terme)
        return [{
            "id": p.id,
            "code": p.code,
            "nom": p.nom,
            "prenom": p.prenom,
            "structure": p.structure,
            "specialite": p.specialite,
            "telephone": p.telephone,
            "email": p.email
        } for p in prescripteurs]
    
    def create_prescripteur(self, data: dict, user_username: str) -> dict:
        """Créer un nouveau prescripteur."""
        # Générer un code unique
        base_code = data.get("nom", "PRES")[:4].upper()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        code = f"{base_code}_{timestamp}"
        
        prescripteur_data = {
            **data,
            "code": code,
            "actif": True
        }
        
        prescripteur = self.prescripteur_repo.create(prescripteur_data)
        
        # Log audit (à implémenter avec AuditService)
        # audit_service.log_action(...)
        
        return {
            "id": prescripteur.id,
            "code": prescripteur.code,
            "message": "Prescripteur créé avec succès"
        }
    
    def update_prescripteur(self, prescripteur_id: int, data: dict) -> Optional[dict]:
        """Mettre à jour un prescripteur."""
        prescripteur = self.prescripteur_repo.update(prescripteur_id, data)
        if prescripteur:
            return {"id": prescripteur.id, "message": "Prescripteur mis à jour"}
        return None
    
    def delete_prescripteur(self, prescripteur_id: int) -> bool:
        """Désactiver un prescripteur."""
        return self.prescripteur_repo.delete(prescripteur_id)
    
    # === Gestion des prescriptions ===
    
    def get_prescription(self, prescription_id: int) -> Optional[dict]:
        """Récupérer une prescription complète."""
        prescription = self.prescription_repo.get_by_id(prescription_id)
        if prescription:
            return self._prescription_to_dict(prescription)
        return None
    
    def get_prescription_by_numero(self, numero: str) -> Optional[dict]:
        """Récupérer une prescription par numéro."""
        prescription = self.prescription_repo.get_by_numero(numero)
        if prescription:
            return self._prescription_to_dict(prescription)
        return None
    
    def get_prescriptions_patient(self, patient_id: int) -> List[dict]:
        """Récupérer toutes les prescriptions d'un patient."""
        prescriptions = self.prescription_repo.get_by_patient(patient_id)
        return [self._prescription_to_dict(p) for p in prescriptions]
    
    def get_prescriptions_en_attente(self) -> List[dict]:
        """Récupérer les prescriptions en attente."""
        prescriptions = self.prescription_repo.get_en_attente()
        return [self._prescription_to_dict(p) for p in prescriptions]
    
    def get_prescriptions_urgentes(self) -> List[dict]:
        """Récupérer les prescriptions urgentes."""
        prescriptions = self.prescription_repo.get_urgentes()
        return [self._prescription_to_dict(p) for p in prescriptions]
    
    def create_prescription(self, data: dict, examens: List[dict], 
                           user_username: str) -> dict:
        """Créer une nouvelle prescription."""
        # Générer un numéro unique
        numero = f"PRESC-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        prescription_data = {
            **data,
            "numero": numero,
            "date_prescription": datetime.utcnow(),
            "statut": "ACTIVE",
            "cree_par": user_username
        }
        
        prescription = self.prescription_repo.create(prescription_data, examens)
        
        return {
            "id": prescription.id,
            "numero": prescription.numero,
            "message": "Prescription créée avec succès"
        }
    
    def update_statut_prescription(self, prescription_id: int, statut: str) -> Optional[dict]:
        """Mettre à jour le statut d'une prescription."""
        valid_statuses = ["ACTIVE", "REALISEE", "ANNULEE"]
        if statut not in valid_statuses:
            raise ValueError(f"Statut invalide. Doit être dans {valid_statuses}")
        
        date_realisation = datetime.utcnow() if statut == "REALISEE" else None
        
        prescription = self.prescription_repo.update_statut(
            prescription_id, statut, date_realisation
        )
        
        if prescription:
            return {"id": prescription.id, "statut": statut}
        return None
    
    def get_stats_prescriptions(self, date_debut: datetime, date_fin: datetime) -> dict:
        """Obtenir des statistiques sur les prescriptions."""
        return self.prescription_repo.get_stats_period(date_debut, date_fin)
    
    def _prescription_to_dict(self, prescription) -> dict:
        """Convertir une prescription ORM en dict."""
        return {
            "id": prescription.id,
            "numero": prescription.numero,
            "patient_id": prescription.patient_id,
            "patient_nom": prescription.patient.nom if prescription.patient else None,
            "patient_prenom": prescription.patient.prenom if prescription.patient else None,
            "prescripteur_id": prescription.prescripteur_id,
            "prescripteur_nom": prescription.prescripteur.nom if prescription.prescripteur else None,
            "date_prescription": prescription.date_prescription.isoformat(),
            "urgence": prescription.urgence,
            "contexte_clinique": prescription.contexte_clinique,
            "traitement_en_cours": prescription.traitement_en_cours,
            "source": prescription.source,
            "reference_externe": prescription.reference_externe,
            "statut": prescription.statut,
            "date_realisation": prescription.date_realisation.isoformat() if prescription.date_realisation else None,
            "examens": [
                {
                    "id": ep.id,
                    "examen_id": ep.examen_id,
                    "examen_nom": ep.examen.nom if ep.examen else None,
                    "priorite": ep.priorite,
                    "instructions": ep.instructions,
                    "statut": ep.statut,
                    "date_prelevement": ep.date_prelevement.isoformat() if ep.date_prelevement else None,
                    "date_resultat": ep.date_resultat.isoformat() if ep.date_resultat else None
                }
                for ep in prescription.examens
            ]
        }


class PrescripteurService:
    """Service métier pour les prescripteurs (wrapper)."""
    
    def __init__(self, session: Session):
        self.session = session
        self.prescription_service = PrescriptionService(session)
    
    def get_all(self, actif_only: bool = True) -> List[dict]:
        """Lister les prescripteurs."""
        return self.prescription_service.list_prescripteurs(actif_only)
    
    def search(self, terme: str) -> List[dict]:
        """Rechercher des prescripteurs."""
        return self.prescription_service.search_prescripteurs(terme)
