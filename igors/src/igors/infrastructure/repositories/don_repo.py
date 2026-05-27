"""
Repository Don - Accès aux données des dons
Conforme CDC §4.2 - Gestion des dons et PSL
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.orm import Session, joinedload

from igors.infrastructure.models.don import DonModel, TypePSLModel
from igors.infrastructure.models.poche import PocheModel
from igors.core.domain.don import Don


class DonRepository:
    """Repository pour la gestion des dons"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, don: Don) -> DonModel:
        """Créer un nouveau don"""
        db_don = DonModel(
            donneur_id=don.donneur_id,
            date_don=don.date_don,
            type_don=don.type_don,
            lieu_collecte=don.lieu_collecte,
            personnel_id=don.personnel_id,
            poids_don=don.poids_don,
            duree_collecte=don.duree_collecte,
            incident=don.incident,
            commentaire=don.commentaire,
            statut=don.statut
        )
        self.session.add(db_don)
        self.session.commit()
        self.session.refresh(db_don)
        return db_don
    
    def get_by_id(self, don_id: int) -> Optional[DonModel]:
        """Récupérer un don par son ID avec poches associées"""
        stmt = select(DonModel).options(
            joinedload(DonModel.tubes),
            joinedload(DonModel.poches)
        ).where(DonModel.id == don_id)
        return self.session.execute(stmt).unique().scalar_one_or_none()
    
    def get_by_donneur(self, donneur_id: int) -> List[DonModel]:
        """Récupérer tous les dons d'un donneur"""
        stmt = select(DonModel).where(DonModel.donneur_id == donneur_id)
        return self.session.execute(stmt).scalars().all()
    
    def get_dons_recents(self, days: int = 30) -> List[DonModel]:
        """Récupérer les dons récents"""
        from datetime import timedelta
        date_limite = datetime.now() - timedelta(days=days)
        stmt = select(DonModel).where(DonModel.date_don >= date_limite)
        return self.session.execute(stmt).scalars().all()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[DonModel]:
        """Récupérer tous les dons avec pagination"""
        stmt = select(DonModel).offset(skip).limit(limit)
        return self.session.execute(stmt).scalars().all()
    
    def update_statut(self, don_id: int, statut: str) -> Optional[DonModel]:
        """Mettre à jour le statut d'un don"""
        db_don = self.get_by_id(don_id)
        if not db_don:
            return None
        
        db_don.statut = statut
        self.session.commit()
        self.session.refresh(db_don)
        return db_don
    
    def add_poches(self, don_id: int, poches_data: List[dict]) -> List[PocheModel]:
        """Ajouter des poches à un don"""
        db_don = self.get_by_id(don_id)
        if not db_don:
            return []
        
        created_poches = []
        for poche_data in poches_data:
            poche = PocheModel(
                don_id=don_id,
                code_barres=pochette_data.get('code_barres'),
                type_psl=pochette_data.get('type_psl'),
                volume=pochette_data.get('volume'),
                date_expiration=pochette_data.get('date_expiration'),
                statut='en_attente_qualification',
                qualification_vih=None,
                qualification_vhb=None,
                qualification_vhc=None,
                qualification_htlv=None,
                qualification_syphilis=None
            )
            self.session.add(poche)
            created_poches.append(poche)
        
        self.session.commit()
        for poche in created_poches:
            self.session.refresh(poche)
        return created_poches
    
    def count_dons_by_type(self, start_date: datetime = None, end_date: datetime = None) -> dict:
        """Compter les dons par type sur une période"""
        from sqlalchemy import func
        
        query = self.session.query(
            DonModel.type_don,
            func.count(DonModel.id).label('count')
        )
        
        if start_date:
            query = query.filter(DonModel.date_don >= start_date)
        if end_date:
            query = query.filter(DonModel.date_don <= end_date)
        
        query = query.group_by(DonModel.type_don)
        results = query.all()
        
        return {row.type_don: row.count for row in results}
    
    def get_next_don_date(self, donneur_id: int) -> Optional[datetime]:
        """Calculer la date du prochain don autorisé"""
        # Délais minimum entre dons selon le type
        delais_minimum = {
            'sang_total': 56,  # 8 semaines
            'plasma': 7,       # 1 semaine
            'plaquettes': 14,  # 2 semaines
            'double_plasma': 28  # 4 semaines
        }
        
        derniers_dons = self.get_by_donneur(donneur_id)
        if not derniers_dons:
            return None
        
        # Trouver le don le plus récent
        dernier_don = max(derniers_dons, key=lambda d: d.date_don)
        delai = delais_minimum.get(dernier_don.type_don, 56)
        
        from datetime import timedelta
        return dernier_don.date_don + timedelta(days=delai)
    
    def delete(self, don_id: int) -> bool:
        """Supprimer un don (seulement si pas de poches associées)"""
        db_don = self.get_by_id(don_id)
        if not db_don:
            return False
        
        if db_don.poches:
            return False  # Ne peut pas supprimer un don avec poches
        
        self.session.delete(db_don)
        self.session.commit()
        return True
    
    def count(self) -> int:
        """Compter le nombre total de dons"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(DonModel)
        return self.session.execute(stmt).scalar()
