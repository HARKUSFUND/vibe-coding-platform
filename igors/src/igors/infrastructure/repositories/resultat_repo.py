"""
Repository Résultat - Accès aux données des résultats d'analyses
Conforme CDC §4.5 - Validation biologique et transmission
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import Session, joinedload

from igors.infrastructure.models.resultat import ResultatModel, HistoriqueResultatModel


class ResultatRepository:
    """Repository pour la gestion des résultats d'analyses"""
    
    def __init__(self, session: Session):
        self.session = session
    
    def create(self, resultat_data: dict) -> ResultatModel:
        """Créer un nouveau résultat"""
        db_resultat = ResultatModel(**resultat_data)
        self.session.add(db_resultat)
        self.session.commit()
        self.session.refresh(db_resultat)
        return db_resultat
    
    def get_by_id(self, resultat_id: int) -> Optional[ResultatModel]:
        """Récupérer un résultat par son ID"""
        stmt = select(ResultatModel).options(
            joinedload(ResultatModel.historique_validations)
        ).where(ResultatModel.id == resultat_id)
        return self.session.execute(stmt).unique().scalar_one_or_none()
    
    def get_by_prescription(self, prescription_id: int) -> List[ResultatModel]:
        """Récupérer tous les résultats d'une prescription"""
        stmt = select(ResultatModel).where(
            ResultatModel.prescription_id == prescription_id
        )
        return self.session.execute(stmt).scalars().all()
    
    def get_by_patient(self, patient_id: int, skip: int = 0, limit: int = 100) -> List[ResultatModel]:
        """Récupérer l'historique des résultats d'un patient"""
        from igors.infrastructure.models.prescription import PrescriptionModel
        
        # Sous-requête pour obtenir les prescriptions du patient
        stmt_prescriptions = select(PrescriptionModel.id).where(
            PrescriptionModel.patient_id == patient_id
        )
        
        stmt = select(ResultatModel).where(
            ResultatModel.prescription_id.in_(stmt_prescriptions)
        ).offset(skip).limit(limit).order_by(ResultatModel.date_prelevement.desc())
        
        return self.session.execute(stmt).scalars().all()
    
    def get_by_examen(self, examen_id: int, date_debut: datetime = None, date_fin: datetime = None) -> List[ResultatModel]:
        """Récupérer les résultats pour un examen donné sur une période"""
        stmt = select(ResultatModel).where(ResultatModel.examen_id == examen_id)
        
        if date_debut:
            stmt = stmt.where(ResultatModel.date_prelevement >= date_debut)
        if date_fin:
            stmt = stmt.where(ResultatModel.date_prelevement <= date_fin)
        
        return self.session.execute(stmt).scalars().all()
    
    def get_resultats_a_valider(self, biologiste_id: int = None) -> List[ResultatModel]:
        """Récupérer les résultats en attente de validation"""
        stmt = select(ResultatModel).where(
            ResultatModel.statut_validation == 'en_attente'
        )
        if biologiste_id:
            stmt = stmt.where(ResultatModel.biologiste_validateur_id == biologiste_id)
        
        return self.session.execute(stmt).scalars().all()
    
    def get_resultats_valides(self, date_debut: datetime = None, date_fin: datetime = None) -> List[ResultatModel]:
        """Récupérer les résultats validés sur une période"""
        stmt = select(ResultatModel).where(
            ResultatModel.statut_validation == 'valide'
        )
        
        if date_debut:
            stmt = stmt.where(ResultatModel.date_validation >= date_debut)
        if date_fin:
            stmt = stmt.where(ResultatModel.date_validation <= date_fin)
        
        return self.session.execute(stmt).scalars().all()
    
    def update_statut_validation(self, resultat_id: int, statut: str, 
                                  biologiste_id: int = None, commentaire: str = None) -> Optional[ResultatModel]:
        """Mettre à jour le statut de validation d'un résultat"""
        db_resultat = self.get_by_id(resultat_id)
        if not db_resultat:
            return None
        
        # Enregistrer dans l'historique avant modification
        historique = HistoriqueResultatModel(
            resultat_id=resultat_id,
            ancienne_valeur=db_resultat.valeur_numerique,
            nouvelle_valeur=db_resultat.valeur_numerique,
            ancien_statut=db_resultat.statut_validation,
            nouveau_statut=statut,
            utilisateur_id=biologiste_id,
            commentaire=commentaire,
            date_modification=datetime.now()
        )
        self.session.add(historique)
        
        # Mettre à jour le résultat
        db_resultat.statut_validation = statut
        if biologiste_id:
            db_resultat.biologiste_validateur_id = biologiste_id
        if statut == 'valide':
            db_resultat.date_validation = datetime.now()
        elif statut == 'rejete':
            db_resultat.date_rejet = datetime.now()
        
        self.session.commit()
        self.session.refresh(db_resultat)
        return db_resultat
    
    def update_valeur(self, resultat_id: int, nouvelle_valeur: str, 
                      valeur_numerique: float = None, utilisateur_id: int = None,
                      commentaire: str = None) -> Optional[ResultatModel]:
        """Mettre à jour la valeur d'un résultat avec traçabilité"""
        db_resultat = self.get_by_id(resultat_id)
        if not db_resultat:
            return None
        
        # Enregistrer dans l'historique
        historique = HistoriqueResultatModel(
            resultat_id=resultat_id,
            ancienne_valeur=db_resultat.valeur_numerique,
            nouvelle_valeur=valeur_numerique,
            ancien_statut=db_resultat.statut_validation,
            nouveau_statut='modifie',
            utilisateur_id=utilisateur_id,
            commentaire=commentaire,
            date_modification=datetime.now()
        )
        self.session.add(historique)
        
        db_resultat.valeur_texte = nouvelle_valeur
        db_resultat.valeur_numerique = valeur_numerique
        db_resultat.statut_validation = 'en_attente'  # Re-passser en attente de validation
        
        self.session.commit()
        self.session.refresh(db_resultat)
        return db_resultat
    
    def get_resultats_critiques(self, date_debut: datetime = None, date_fin: datetime = None) -> List[ResultatModel]:
        """Récupérer les résultats critiques (en dehors des valeurs de référence)"""
        stmt = select(ResultatModel).where(
            or_(
                ResultatResultatModel.est_critique == True,
                ResultatModel.statut_validation == 'critique'
            )
        )
        
        if date_debut:
            stmt = stmt.where(ResultatModel.date_prelevement >= date_debut)
        if date_fin:
            stmt = stmt.where(ResultatModel.date_prelevement <= date_fin)
        
        return self.session.execute(stmt).scalars().all()
    
    def search(self, search_term: str) -> List[ResultatModel]:
        """Rechercher des résultats par valeur ou commentaire"""
        stmt = select(ResultatModel).where(
            or_(
                ResultatModel.valeur_texte.ilike(f"%{search_term}%"),
                ResultatModel.commentaire.ilike(f"%{search_term}%")
            )
        )
        return self.session.execute(stmt).scalars().all()
    
    def count_by_statut(self) -> dict:
        """Compter les résultats par statut de validation"""
        from sqlalchemy import func
        
        query = self.session.query(
            ResultatModel.statut_validation,
            func.count(ResultatModel.id).label('count')
        ).group_by(ResultatModel.statut_validation)
        
        results = query.all()
        return {row.statut_validation: row.count for row in results}
    
    def count(self) -> int:
        """Compter le nombre total de résultats"""
        from sqlalchemy import func
        stmt = select(func.count()).select_from(ResultatModel)
        return self.session.execute(stmt).scalar()
    
    def delete(self, resultat_id: int) -> bool:
        """Supprimer un résultat (seulement si non validé)"""
        db_resultat = self.get_by_id(resultat_id)
        if not db_resultat:
            return False
        
        if db_resultat.statut_validation == 'valide':
            return False  # Ne peut pas supprimer un résultat validé
        
        self.session.delete(db_resultat)
        self.session.commit()
        return True
