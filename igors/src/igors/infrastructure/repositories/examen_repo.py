"""
Repository Examen - Accès aux données des examens
Conforme CDC §4.1 - Référentiel examens (LOINC)
"""
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from igors.infrastructure.models.examen import ExamenModel, GroupeExamensModel


class ExamenRepository:
    """Repository pour la gestion des examens et référentiels"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, examen_data: dict) -> ExamenModel:
        """Créer un nouvel examen"""
        db_examen = ExamenModel(**examen_data)
        self.session.add(db_examen)
        self.session.commit()
        self.session.refresh(db_examen)
        return db_examen
    
    def get_by_id(self, examen_id: int) -> Optional[ExamenModel]:
        """Récupérer un examen par son ID"""
        return self.session.get(ExamenModel, examen_id)
    
    def get_by_code_loinc(self, code_loinc: str) -> Optional[ExamenModel]:
        """Récupérer un examen par son code LOINC"""
        stmt = select(ExamenModel).where(ExamenModel.code_loinc == code_loinc)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_by_code_local(self, code_local: str) -> Optional[ExamenModel]:
        """Récupérer un examen par son code local"""
        stmt = select(ExamenModel).where(ExamenModel.code_local == code_local)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def search(self, search_term: str) -> List[ExamenModel]:
        """Rechercher des examens par nom ou code"""
        from sqlalchemy import or_
        stmt = select(ExamenModel).where(
            or_(
                ExamenModel.nom.ilike(f"%{search_term}%"),
                ExamenModel.code_loinc.ilike(f"%{search_term}%"),
                ExamenModel.code_local.ilike(f"%{search_term}%")
            )
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[ExamenModel]:
        """Récupérer tous les examens avec pagination"""
        stmt = select(ExamenModel).offset(skip).limit(limit)
        return self.session.execute(stmt).scalars().all()
    
    def get_by_groupe(self, groupe_id: int) -> List[ExamenModel]:
        """Récupérer les examens d'un groupe"""
        stmt = select(ExamenModel).where(ExamenModel.groupe_id == groupe_id)
        return self.session.execute(stmt).scalars().all()
    
    def update(self, examen_id: int, examen_data: dict) -> Optional[ExamenModel]:
        """Mettre à jour un examen"""
        db_examen = self.get_by_id(examen_id)
        if not db_examen:
            return None
        
        for key, value in examen_data.items():
            if hasattr(db_examen, key) and value is not None:
                setattr(db_examen, key, value)
        
        self.session.commit()
        self.session.refresh(db_examen)
        return db_examen
    
    def delete(self, examen_id: int) -> bool:
        """Supprimer un examen"""
        db_examen = self.get_by_id(examen_id)
        if not db_examen:
            return False
        
        self.session.delete(db_examen)
        self.session.commit()
        return True
    
    # === Gestion des groupes d'examens ===
    
    def create_groupe(self, nom: str, description: str = None) -> GroupeExamensModel:
        """Créer un nouveau groupe d'examens"""
        groupe = GroupeExamensModel(nom=nom, description=description)
        self.session.add(groupe)
        self.session.commit()
        self.session.refresh(groupe)
        return groupe
    
    def get_groupe_by_id(self, groupe_id: int) -> Optional[GroupeExamensModel]:
        """Récupérer un groupe par son ID"""
        return self.session.get(GroupeExamensModel, groupe_id)
    
    def get_all_groupes(self) -> List[GroupeExamensModel]:
        """Récupérer tous les groupes d'examens"""
        stmt = select(GroupeExamensModel)
        return self.session.execute(stmt).scalars().all()
    
    def add_examen_to_groupe(self, examen_id: int, groupe_id: int) -> bool:
        """Ajouter un examen à un groupe"""
        db_examen = self.get_by_id(examen_id)
        db_groupe = self.get_groupe_by_id(groupe_id)
        
        if not db_examen or not db_groupe:
            return False
        
        db_examen.groupe_id = groupe_id
        self.session.commit()
        return True
    
    def remove_examen_from_groupe(self, examen_id: int) -> bool:
        """Retirer un examen de son groupe"""
        db_examen = self.get_by_id(examen_id)
        if not db_examen:
            return False
        
        db_examen.groupe_id = None
        self.session.commit()
        return True
    
    # === Fourchettes de référence ===
    
    def get_fourchette_reference(self, examen_id: int, age: int = None, sexe: str = None) -> dict:
        """Obtenir la fourchette de référence pour un examen selon l'âge et le sexe"""
        db_examen = self.get_by_id(examen_id)
        if not db_examen:
            return {}
        
        # Logique simplifiée - à adapter selon les besoins réels
        fourchette = {
            'unite': db_examen.unite,
            'min': db_examen.valeur_min_adulte if sexe == 'M' or sexe == 'F' else db_examen.valeur_min_enfant,
            'max': db_examen.valeur_max_adulte if sexe == 'M' or sexe == 'F' else db_examen.valeur_max_enfant,
            'critique_min': db_examen.valeur_critique_min,
            'critique_max': db_examen.valeur_critique_max
        }
        return fourchette
    
    def count(self) -> int:
        """Compter le nombre total d'examens"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(ExamenModel)
        return self.session.execute(stmt).scalar()
