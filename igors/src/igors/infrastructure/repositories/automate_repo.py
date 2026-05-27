"""
Repository pour la gestion des automates et communications.
Conforme CDC §4.4
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.orm import Session, joinedload

from ...infrastructure.models.automate import (
    AutomateModel,
    AutomateExamenMappingModel,
    AutomateLogModel,
    WorklistQueueModel
)


class AutomateRepository:
    """Repository pour les automates."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_id(self, automate_id: int) -> Optional[AutomateModel]:
        """Récupérer un automate par ID."""
        return self.session.get(AutomateModel, automate_id)
    
    def get_by_code(self, code: str) -> Optional[AutomateModel]:
        """Récupérer un automate par code."""
        stmt = select(AutomateModel).where(AutomateModel.code == code)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_all(self, actif_only: bool = True) -> List[AutomateModel]:
        """Récupérer tous les automates."""
        stmt = select(AutomateModel)
        if actif_only:
            stmt = stmt.where(AutomateModel.actif == True)
        stmt = stmt.order_by(AutomateModel.nom)
        return self.session.execute(stmt).scalars().all()
    
    def get_by_protocole(self, protocole: str) -> List[AutomateModel]:
        """Récupérer les automates par protocole."""
        stmt = select(AutomateModel).where(
            (AutomateModel.protocole == protocole) &
            (AutomateModel.actif == True)
        )
        return self.session.execute(stmt).scalars().all()
    
    def create(self, automate_data: dict) -> AutomateModel:
        """Créer un nouvel automate."""
        automate = AutomateModel(**automate_data)
        self.session.add(automate)
        self.session.flush()
        return automate
    
    def update(self, automate_id: int, update_data: dict) -> Optional[AutomateModel]:
        """Mettre à jour un automate."""
        automate = self.get_by_id(automate_id)
        if automate:
            for key, value in update_data.items():
                if hasattr(automate, key):
                    setattr(automate, key, value)
            automate.date_modification = datetime.utcnow()
        return automate
    
    def update_statut_connection(self, automate_id: int, statut: str) -> bool:
        """Mettre à jour le statut de connection."""
        automate = self.get_by_id(automate_id)
        if automate:
            automate.statut_connection = statut
            automate.dernier_ping = datetime.utcnow()
            return True
        return False
    
    def log_communication(self, automate_id: int, type_evenement: str,
                         donnees_brutes: str = None, direction: str = "ENVOI",
                         statut: str = "SUCCES", message_erreur: str = None,
                         patient_id: int = None, don_id: int = None,
                         numero_commande: str = None) -> AutomateLogModel:
        """Enregistrer un log de communication."""
        log = AutomateLogModel(
            automate_id=automate_id,
            type_evenement=type_evenement,
            donnees_brutes=donnees_brutes,
            direction=direction,
            statut=statut,
            message_erreur=message_erreur,
            patient_id=patient_id,
            don_id=don_id,
            numero_commande=numero_commande
        )
        self.session.add(log)
        self.session.flush()
        return log
    
    def get_logs_recent(self, automate_id: int = None, limit: int = 100) -> List[AutomateLogModel]:
        """Récupérer les logs récents."""
        stmt = select(AutomateLogModel).order_by(AutomateLogModel.horodatage.desc()).limit(limit)
        if automate_id:
            stmt = stmt.where(AutomateLogModel.automate_id == automate_id)
        return self.session.execute(stmt).scalars().all()
    
    def get_stats_communication(self, date_debut: datetime, date_fin: datetime) -> dict:
        """Obtenir des statistiques de communication."""
        # Total par statut
        stmt_statut = select(
            AutomateLogModel.statut,
            func.count(AutomateLogModel.id)
        ).where(
            (AutomateLogModel.horodatage >= date_debut) &
            (AutomateLogModel.horodatage <= date_fin)
        ).group_by(AutomateLogModel.statut)
        par_statut = dict(self.session.execute(stmt_statut).all())
        
        # Total par type d'événement
        stmt_type = select(
            AutomateLogModel.type_evenement,
            func.count(AutomateLogModel.id)
        ).where(
            (AutomateLogModel.horodatage >= date_debut) &
            (AutomateLogModel.horodatage <= date_fin)
        ).group_by(AutomateLogModel.type_evenement)
        par_type = dict(self.session.execute(stmt_type).all())
        
        total = sum(par_statut.values())
        succes = par_statut.get("SUCCES", 0)
        
        return {
            "total": total,
            "succes": succes,
            "echecs": total - succes,
            "taux_succes": (succes / total * 100) if total > 0 else 0,
            "par_statut": par_statut,
            "par_type": par_type
        }


class AutomateMappingRepository:
    """Repository pour les mappings automate <-> examens."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_by_automate(self, automate_id: int) -> List[AutomateExamenMappingModel]:
        """Récupérer tous les mappings d'un automate."""
        stmt = select(AutomateExamenMappingModel).where(
            (AutomateExamenMappingModel.automate_id == automate_id) &
            (AutomateExamenMappingModel.actif == True)
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_by_examen(self, examen_id: int) -> List[AutomateExamenMappingModel]:
        """Récupérer tous les mappings pour un examen."""
        stmt = select(AutomateExamenMappingModel).where(
            (AutomateExamenMappingModel.examen_id == examen_id) &
            (AutomateExamenMappingModel.actif == True)
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_mapping(self, automate_id: int, code_automate: str) -> Optional[AutomateExamenMappingModel]:
        """Récupérer un mapping spécifique."""
        stmt = select(AutomateExamenMappingModel).where(
            (AutomateExamenMappingModel.automate_id == automate_id) &
            (AutomateExamenMappingModel.code_automate == code_automate) &
            (AutomateExamenMappingModel.actif == True)
        )
        return self.session.execute(stmt).scalar_one_or_none()
    
    def create(self, mapping_data: dict) -> AutomateExamenMappingModel:
        """Créer un nouveau mapping."""
        mapping = AutomateExamenMappingModel(**mapping_data)
        self.session.add(mapping)
        self.session.flush()
        return mapping
    
    def update(self, mapping_id: int, update_data: dict) -> Optional[AutomateExamenMappingModel]:
        """Mettre à jour un mapping."""
        stmt = select(AutomateExamenMappingModel).where(
            AutomateExamenMappingModel.id == mapping_id
        )
        mapping = self.session.execute(stmt).scalar_one_or_none()
        if mapping:
            for key, value in update_data.items():
                if hasattr(mapping, key):
                    setattr(mapping, key, value)
        return mapping
    
    def delete(self, mapping_id: int) -> bool:
        """Supprimer (désactiver) un mapping."""
        stmt = select(AutomateExamenMappingModel).where(
            AutomateExamenMappingModel.id == mapping_id
        )
        mapping = self.session.execute(stmt).scalar_one_or_none()
        if mapping:
            mapping.actif = False
            return True
        return False


class WorklistRepository:
    """Repository pour la file d'attente worklist."""
    
    def __init__(self, session: Session):
        self.session = session
    
    def get_en_attente(self, automate_id: int = None) -> List[WorklistQueueModel]:
        """Récupérer les worklists en attente."""
        stmt = select(WorklistQueueModel).where(
            WorklistQueueModel.statut == "EN_ATTENTE"
        ).order_by(WorklistQueueModel.date_demande)
        if automate_id:
            stmt = stmt.where(WorklistQueueModel.automate_id == automate_id)
        return self.session.execute(stmt).scalars().all()
    
    def create(self, worklist_data: dict) -> WorklistQueueModel:
        """Créer une nouvelle entrée worklist."""
        worklist = WorklistQueueModel(**worklist_data)
        self.session.add(worklist)
        self.session.flush()
        return worklist
    
    def update_statut(self, worklist_id: int, statut: str, 
                      date_envoi: datetime = None,
                      date_acquittement: datetime = None,
                      erreur: str = None) -> Optional[WorklistQueueModel]:
        """Mettre à jour le statut d'une worklist."""
        worklist = self.session.get(WorklistQueueModel, worklist_id)
        if worklist:
            worklist.statut = statut
            if date_envoi:
                worklist.date_envoi = date_envoi
            if date_acquittement:
                worklist.date_acquittement = date_acquittement
            if erreur:
                worklist.derniere_erreur = erreur
                worklist.nombre_tentatives += 1
        return worklist
    
    def get_by_numero_commande(self, numero_commande: str) -> Optional[WorklistQueueModel]:
        """Récupérer une worklist par numéro de commande."""
        return self.session.get(WorklistQueueModel, numero_commande)  # Primary key is numero_commande? No, id is PK
    
    def get_expired(self, timeout_minutes: int = 30) -> List[WorklistQueueModel]:
        """Récupérer les worklists expirées."""
        from datetime import timedelta
        timeout = datetime.utcnow() - timedelta(minutes=timeout_minutes)
        stmt = select(WorklistQueueModel).where(
            (WorklistQueueModel.statut == "EN_ATTENTE") &
            (WorklistQueueModel.date_demande < timeout)
        )
        return self.session.execute(stmt).scalars().all()
