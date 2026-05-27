"""
Repository Poche - Accès aux données des poches de sang
Conforme CDC §4.2 - Gestion des produits sanguins labiles
"""
from typing import Optional, List
from datetime import datetime, timedelta
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload

from igors.infrastructure.models.poche import PocheModel, TypePSLModel


class PocheRepository:
    """Repository pour la gestion des poches de sang"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, poche_data: dict) -> PocheModel:
        """Créer une nouvelle poche"""
        db_poche = PocheModel(**poche_data)
        self.session.add(db_poche)
        self.session.commit()
        self.session.refresh(db_poche)
        return db_poche
    
    def get_by_id(self, poche_id: int) -> Optional[PocheModel]:
        """Récupérer une poche par son ID"""
        stmt = select(PocheModel).options(
            joinedload(PocheModel.don)
        ).where(PocheModel.id == poche_id)
        return self.session.execute(stmt).unique().scalar_one_or_none()
    
    def get_by_code_barres(self, code_barres: str) -> Optional[PocheModel]:
        """Récupérer une poche par son code-barres"""
        stmt = select(PocheModel).where(PocheModel.code_barres == code_barres)
        return self.session.execute(stmt).scalar_one_or_none()
    
    def get_by_don(self, don_id: int) -> List[PocheModel]:
        """Récupérer toutes les poches d'un don"""
        stmt = select(PocheModel).where(PocheModel.don_id == don_id)
        return self.session.execute(stmt).scalars().all()
    
    def get_stock(self, type_psl: str = None, groupe_sanguin: str = None, 
                  facteur_rhesus: str = None) -> List[PocheModel]:
        """Obtenir le stock actuel avec filtres optionnels"""
        stmt = select(PocheModel).where(PocheModel.statut == 'disponible')
        
        if type_psl:
            stmt = stmt.where(PocheModel.type_psl == type_psl)
        if groupe_sanguin:
            stmt = stmt.where(PocheModel.groupe_sanguin == groupe_sanguin)
        if facteur_rhesus:
            stmt = stmt.where(PocheModel.facteur_rhesus == facteur_rhesus)
        
        return self.session.execute(stmt).scalars().all()
    
    def get_poches_a_qualifier(self) -> List[PocheModel]:
        """Récupérer les poches en attente de qualification"""
        stmt = select(PocheModel).where(
            PocheModel.statut == 'en_attente_qualification'
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_poches_bientot_expirees(self, jours_avertissement: int = 7) -> List[PocheModel]:
        """Récupérer les poches qui expirent bientôt"""
        date_limite = datetime.now() + timedelta(days=jours_avertissement)
        stmt = select(PocheModel).where(
            and_(
                PocheModel.statut == 'disponible',
                PocheModel.date_expiration <= date_limite
            )
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_poches_expirees(self) -> List[PocheModel]:
        """Récupérer les poches expirées"""
        stmt = select(PocheModel).where(
            and_(
                PocheModel.statut.in_(['disponible', 'reserve']),
                PocheModel.date_expiration < datetime.now()
            )
        )
        return self.session.execute(stmt).scalars().all()
    
    def update_statut(self, poche_id: int, statut: str, 
                      qualification_data: dict = None) -> Optional[PocheModel]:
        """Mettre à jour le statut d'une poche"""
        db_poche = self.get_by_id(poche_id)
        if not db_poche:
            return None
        
        db_poche.statut = statut
        
        # Mettre à jour les résultats de qualification
        if qualification_data:
            for key, value in qualification_data.items():
                if hasattr(db_poche, key):
                    setattr(db_poche, key, value)
        
        self.session.commit()
        self.session.refresh(db_poche)
        return db_poche
    
    def reserver(self, poche_id: int, patient_id: int, utilisateur_id: int) -> Optional[PocheModel]:
        """Réserver une poche pour un patient"""
        db_poche = self.get_by_id(poche_id)
        if not db_poche:
            return None
        
        if db_poche.statut != 'disponible':
            return None
        
        db_poche.statut = 'reserve'
        db_poche.patient_id = patient_id
        db_poche.utilisateur_reservation_id = utilisateur_id
        db_poche.date_reservation = datetime.now()
        
        self.session.commit()
        self.session.refresh(db_poche)
        return db_poche
    
    def sortir(self, poche_id: int, motif: str, utilisateur_id: int) -> Optional[PocheModel]:
        """Sortir une poche du stock"""
        db_poche = self.get_by_id(poche_id)
        if not db_poche:
            return None
        
        db_poche.statut = 'sortie'
        db_poche.motif_sortie = motif
        db_poche.utilisateur_sortie_id = utilisateur_id
        db_poche.date_sortie = datetime.now()
        
        self.session.commit()
        self.session.refresh(db_poche)
        return db_poche
    
    def detruire(self, poche_id: int, raison: str, utilisateur_id: int) -> Optional[PocheModel]:
        """Détruire une poche (périmée, non-conforme, etc.)"""
        db_poche = self.get_by_id(poche_id)
        if not db_poche:
            return None
        
        db_poche.statut = 'detruit'
        db_poche.raison_destruction = raison
        db_poche.utilisateur_destruction_id = utilisateur_id
        db_poche.date_destruction = datetime.now()
        
        self.session.commit()
        self.session.refresh(db_poche)
        return db_poche
    
    def count_by_type(self) -> dict:
        """Compter les poches disponibles par type"""
        from sqlalchemy import func
        
        query = self.session.query(
            PocheModel.type_psl,
            func.count(PocheModel.id).label('count')
        ).where(
            PocheModel.statut == 'disponible'
        ).group_by(PocheModel.type_psl)
        
        results = query.all()
        return {row.type_psl: row.count for row in results}
    
    def count_by_groupe_sanguin(self) -> dict:
        """Compter les poches disponibles par groupe sanguin"""
        from sqlalchemy import func
        
        query = self.session.query(
            PocheModel.groupe_sanguin,
            PocheModel.facteur_rhesus,
            func.count(PocheModel.id).label('count')
        ).where(
            PocheModel.statut == 'disponible'
        ).group_by(PocheModel.groupe_sanguin, PocheModel.facteur_rhesus)
        
        results = query.all()
        return {f"{row.groupe_sanguin}{row.facteur_rhesus}": row.count for row in results}
    
    def count(self) -> int:
        """Compter le nombre total de poches"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(PocheModel)
        return self.session.execute(stmt).scalar()
    
    def delete(self, poche_id: int) -> bool:
        """Supprimer une poche (seulement si jamais utilisée)"""
        db_poche = self.get_by_id(poche_id)
        if not db_poche:
            return False
        
        if db_poche.statut not in ['en_attente_qualification', 'qualifie_non_conforme']:
            return False  # Ne peut supprimer que les poches non utilisées
        
        self.session.delete(db_poche)
        self.session.commit()
        return True
