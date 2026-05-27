"""
Service de gestion de la qualité (CQI, EEQ, CAPA).
Conforme ISO 15189 et CDC §4.7.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select

from igors.core.domain.qualite import CQI, EEQ, CAPA, StatutCAPA, TypeAction
from igors.infrastructure.models.qualite import (
    CQIModel, EEQModel, CAPAModel, ActionCorrectiveModel,
    NonConformiteModel, SuiviIndicateurModel
)
from igors.infrastructure.models.user import UserModel


class QualiteService:
    """Service de gestion de la qualité laboratoire."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    # ========== CONTRÔLE QUALITÉ INTERNE (CQI) ==========
    
    def enregistrer_cqi(
        self,
        examen_id: int,
        lot_reactif: str,
        date_test: datetime,
        valeur_obtenue: float,
        valeur_cible: float,
        ecart_type_acceptable: float,
        technicien_id: int,
        automate_id: Optional[int] = None
    ) -> CQIModel:
        """Enregistrer un résultat de contrôle qualité interne."""
        
        cqi = CQIModel(
            examen_id=examen_id,
            lot_reactif=lot_reactif,
            date_test=date_test,
            valeur_obtenue=valeur_obtenue,
            valeur_cible=valeur_cible,
            ecart_type_acceptable=ecart_type_acceptable,
            technicien_id=technicien_id,
            automate_id=automate_id,
            statut='en_attente'
        )
        
        # Calculer l'écart et déterminer si acceptable
        ecart = abs(valeur_obtenue - valeur_cible)
        cqi.ecart = ecart
        cqi.ecart_pourcentage = (ecart / valeur_cible * 100) if valeur_cible != 0 else 0
        
        # Appliquer les règles de Westgard simplifiées
        if ecart <= ecart_type_acceptable:
            cqi.statut = 'acceptable'
            cqi.regle_westgard_violee = None
        elif ecart <= 2 * ecart_type_acceptable:
            cqi.statut = 'avertissement'
            cqi.regle_westgard_violee = '1-2s'
        else:
            cqi.statut = 'inacceptable'
            cqi.regle_westgard_violee = '1-3s'
        
        self.db.add(cqi)
        self.db.commit()
        self.db.refresh(cqi)
        
        # Si inacceptable, créer une non-conformité automatique
        if cqi.statut == 'inacceptable':
            self.creer_non_conformite(
                type_nc='CQI_INACCEPTABLE',
                description=f"CQI inacceptable pour examen {examen_id}: écart de {ecart:.2f}",
                source='CQI',
                source_id=cqi.id,
                declare_par=technicien_id
            )
        
        return cqi
    
    def get_cqi_recent(
        self,
        examen_id: Optional[int] = None,
        jours: int = 30
    ) -> List[CQIModel]:
        """Récupérer les CQI récents."""
        query = select(CQIModel).where(
            CQIModel.date_test >= datetime.now() - timedelta(days=jours)
        )
        
        if examen_id:
            query = query.where(CQIModel.examen_id == examen_id)
        
        result = self.db.execute(query.order_by(CQIModel.date_test.desc()))
        return list(result.scalars().all())
    
    # ========== ÉVALUATION EXTERNE DE LA QUALITÉ (EEQ) ==========
    
    def creer_session_eeq(
        self,
        organisme_fournisseur: str,
        date_reception: datetime,
        date_limite_reponse: datetime,
        examens_concernes: List[int],
        responsable_id: int
    ) -> EEQModel:
        """Créer une nouvelle session EEQ."""
        
        eeq = EEQModel(
            organisme_fournisseur=organisme_fournisseur,
            date_reception=date_reception,
            date_limite_reponse=date_limite_reponse,
            examens_concernes=','.join(map(str, examens_concernes)),
            responsable_id=responsable_id,
            statut='en_cours'
        )
        
        self.db.add(eeq)
        self.db.commit()
        self.db.refresh(eeq)
        
        return eeq
    
    def enregistrer_resultat_eeq(
        self,
        eeq_id: int,
        examen_id: int,
        echantillon_id: str,
        valeur_mesuree: float,
        valeur_cible: Optional[float] = None,
        commentaire: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enregistrer un résultat EEQ et calculer la performance."""
        
        eeq = self.db.get(EEQModel, eeq_id)
        if not eeq:
            raise ValueError(f"Session EEQ {eeq_id} introuvable")
        
        # Enregistrer le résultat
        resultat_data = {
            'eeq_id': eeq_id,
            'examen_id': examen_id,
            'echantillon_id': echantillon_id,
            'valeur_mesuree': valeur_mesuree,
            'valeur_cible': valeur_cible,
            'commentaire': commentaire,
            'date_soumission': datetime.now()
        }
        
        # Calculer la performance si valeur cible fournie
        performance = None
        if valeur_cible:
            ecart = abs(valeur_mesuree - valeur_cible)
            ecart_pourcentage = (ecart / valeur_cible * 100) if valeur_cible != 0 else 0
            
            # Critères d'acceptabilité (à configurer par examen)
            seuil_acceptabilite = 10.0  # % - à personnaliser
            
            if ecart_pourcentage <= seuil_acceptabilite:
                performance = 'acceptable'
            elif ecart_pourcentage <= 2 * seuil_acceptabilite:
                performance = 'limite'
            else:
                performance = 'inacceptable'
            
            resultat_data['ecart'] = ecart
            resultat_data['ecart_pourcentage'] = ecart_pourcentage
            resultat_data['performance'] = performance
        
        # Si inacceptable, créer une non-conformité
        if performance == 'inacceptable':
            self.creer_non_conformite(
                type_nc='EEQ_INACCEPTABLE',
                description=f"EEQ inacceptable pour examen {examen_id}: écart de {ecart_pourcentage:.2f}%",
                source='EEQ',
                source_id=eeq_id,
                declare_par=eeq.responsable_id
            )
        
        return resultat_data
    
    def clôturer_session_eeq(self, eeq_id: int, rapport_final: str) -> EEQModel:
        """Clôturer une session EEQ avec rapport final."""
        
        eeq = self.db.get(EEQModel, eeq_id)
        if not eeq:
            raise ValueError(f"Session EEQ {eeq_id} introuvable")
        
        eeq.statut = 'termine'
        eeq.rapport_final = rapport_final
        eeq.date_cloture = datetime.now()
        
        self.db.commit()
        self.db.refresh(eeq)
        
        return eeq
    
    # ========== GESTION DES NON-CONFORMITÉS ET CAPA ==========
    
    def creer_non_conformite(
        self,
        type_nc: str,
        description: str,
        source: str,
        source_id: int,
        declare_par: int,
        gravite: str = 'moyenne'
    ) -> NonConformiteModel:
        """Créer une non-conformité."""
        
        nc = NonConformiteModel(
            type_nc=type_nc,
            description=description,
            source=source,
            source_id=source_id,
            declare_par=declare_par,
            gravite=gravite,
            statut='ouverte'
        )
        
        self.db.add(nc)
        self.db.commit()
        self.db.refresh(nc)
        
        return nc
    
    def creer_capa(
        self,
        non_conformite_id: int,
        description_action: str,
        type_action: str,
        responsable_id: int,
        echeance: datetime,
        priorite: str = 'moyenne'
    ) -> CAPAModel:
        """Créer une action corrective/préventive (CAPA)."""
        
        capa = CAPAModel(
            non_conformite_id=non_conformite_id,
            description_action=description_action,
            type_action=type_action,
            responsable_id=responsable_id,
            echeance=echeance,
            priorite=priorite,
            statut='planifiee'
        )
        
        self.db.add(capa)
        self.db.commit()
        self.db.refresh(capa)
        
        return capa
    
    def mettre_a_jour_statut_capa(
        self,
        capa_id: int,
        nouveau_statut: str,
        commentaire: Optional[str] = None
    ) -> CAPAModel:
        """Mettre à jour le statut d'une CAPA."""
        
        capa = self.db.get(CAPAModel, capa_id)
        if not capa:
            raise ValueError(f"CAPA {capa_id} introuvable")
        
        ancien_statut = capa.statut
        capa.statut = nouveau_statut
        
        if nouveau_statut == 'en_cours':
            capa.date_debut = datetime.now()
        elif nouveau_statut == 'terminee':
            capa.date_fin = datetime.now()
            # Vérifier l'efficacité après clôture
            capa.efficacité_a_verifier = True
        
        if commentaire:
            historique = capa.historique_statuts or []
            historique.append({
                'ancien_statut': ancien_statut,
                'nouveau_statut': nouveau_statut,
                'commentaire': commentaire,
                'date': datetime.now().isoformat()
            })
            capa.historique_statuts = historique
        
        self.db.commit()
        self.db.refresh(capa)
        
        return capa
    
    def verifier_efficacite_capa(self, capa_id: int, efficace: bool, commentaire: str) -> CAPAModel:
        """Vérifier l'efficacité d'une CAPA après clôture."""
        
        capa = self.db.get(CAPAModel, capa_id)
        if not capa:
            raise ValueError(f"CAPA {capa_id} introuvable")
        
        capa.efficace = efficace
        capa.commentaire_efficacite = commentaire
        capa.date_verification_efficacite = datetime.now()
        
        # Si non efficace, créer une nouvelle CAPA
        if not efficace:
            nouvelle_capa = CAPAModel(
                non_conformite_id=capa.non_conformite_id,
                description_action=f"Relance: {capa.description_action}",
                type_action='corrective',
                responsable_id=capa.responsable_id,
                echeance=capa.echeance + timedelta(days=30),
                priorite='haute',
                statut='planifiee'
            )
            self.db.add(nouvelle_capa)
        
        self.db.commit()
        self.db.refresh(capa)
        
        return capa
    
    # ========== INDICATEURS QUALITÉ ==========
    
    def calculer_indicateurs_qualite(self, periode_jours: int = 30) -> Dict[str, Any]:
        """Calculer les indicateurs qualité pour le tableau de bord."""
        
        indicateurs = {}
        
        # Taux de CQI acceptables
        cqi_recents = self.get_cqi_recent(jours=periode_jours)
        if cqi_recents:
            acceptables = sum(1 for c in cqi_recents if c.statut == 'acceptable')
            indicateurs['taux_cqi_acceptable'] = (acceptables / len(cqi_recents)) * 100
        else:
            indicateurs['taux_cqi_acceptable'] = None
        
        # Nombre de non-conformités ouvertes
        nc_ouvertes = self.db.execute(
            select(NonConformiteModel).where(NonConformiteModel.statut == 'ouverte')
        ).scalars().all()
        indicateurs['nc_ouvertes'] = len(nc_ouvertes)
        
        # Taux de CAPA dans les délais
        capa_en_retard = self.db.execute(
            select(CAPAModel).where(
                CAPAModel.statut.in_(['planifiee', 'en_cours']),
                CAPAModel.echeance < datetime.now()
            )
        ).scalars().all()
        capa_totales = self.db.execute(
            select(CAPAModel).where(CAPAModel.statut.in_(['planifiee', 'en_cours', 'terminee']))
        ).scalars().all()
        
        if capa_totales:
            indicateurs['taux_capa_delais'] = ((len(capa_totales) - len(capa_en_retard)) / len(capa_totales)) * 100
        else:
            indicateurs['taux_capa_delais'] = None
        
        # EEQ en cours
        eeq_en_cours = self.db.execute(
            select(EEQModel).where(EEQModel.statut == 'en_cours')
        ).scalars().all()
        indicateurs['eeq_en_cours'] = len(eeq_en_cours)
        
        return indicateurs
