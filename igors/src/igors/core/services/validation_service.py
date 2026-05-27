"""
Service de validation biologique des résultats d'analyses.
Implémente les règles de Westgard et la validation assistée.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from igors.core.domain.resultat import Resultat, StatutValidation, RegleWestgard
from igors.infrastructure.models.resultat import ResultatModel
from igors.infrastructure.models.examen import ExamenModel
from igors.infrastructure.models.user import UserModel
from igors.infrastructure.security.signature import SignatureElectronique


class ValidationBiologiqueService:
    """Service de validation biologique avec règles configurables."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.signature_electronique = SignatureElectronique()
    
    def valider_resultat(
        self,
        resultat_id: int,
        validateur_id: int,
        commentaire: Optional[str] = None,
        signature_otp: Optional[str] = None
    ) -> ResultatModel:
        """Valider un résultat avec signature électronique."""
        
        resultat = self.db.get(ResultatModel, resultat_id)
        if not resultat:
            raise ValueError(f"Résultat {resultat_id} introuvable")
        
        validateur = self.db.get(UserModel, validateur_id)
        if not validateur:
            raise ValueError(f"Validateur {validateur_id} introuvable")
        
        # Vérifier que le validateur est un biologiste
        if validateur.role not in ['biologiste', 'medecin', 'administrateur']:
            raise PermissionError("Seul un biologiste peut valider les résultats")
        
        # Appliquer les règles de validation automatique
        regles_violations = self.appliquer_regles_westgard(resultat)
        
        if regles_violations:
            # Bloquer la validation si règles critiques violées
            violations_critiques = [r for r in regles_violations if r['critique']]
            if violations_critiques:
                raise ValueError(
                    f"Validation bloquée - Règles Westgard violées: "
                    f"{', '.join([v['regle'] for v in violations_critiques])}"
                )
        
        # Signer électroniquement
        if signature_otp:
            signature_data = {
                'resultat_id': resultat.id,
                'valeur': resultat.valeur,
                'unite': resultat.unite,
                'validateur_id': validateur_id,
                'timestamp': datetime.now().isoformat()
            }
            signature = self.signature_electronique.signer(signature_data, signature_otp)
            resultat.signature_electronique = signature
            resultat.hash_signature = self.signature_electronique.hacher_contenu(
                f"{resultat.id}:{resultat.valeur}:{datetime.now().isoformat()}"
            )
        
        # Mettre à jour le résultat
        resultat.statut_validation = StatutValidation.VALIDE.value
        resultat.validateur_id = validateur_id
        resultat.date_validation = datetime.now()
        resultat.commentaire_validation = commentaire
        
        self.db.commit()
        self.db.refresh(resultat)
        
        return resultat
    
    def rejeter_resultat(
        self,
        resultat_id: int,
        rejecteur_id: int,
        motif: str
    ) -> ResultatModel:
        """Rejeter un résultat pour re-analyse."""
        
        resultat = self.db.get(ResultatModel, resultat_id)
        if not resultat:
            raise ValueError(f"Résultat {resultat_id} introuvable")
        
        resultat.statut_validation = StatutValidation.REJETE.value
        resultat.rejecteur_id = rejecteur_id
        resultat.date_rejet = datetime.now()
        resultat.motif_rejet = motif
        
        self.db.commit()
        self.db.refresh(resultat)
        
        return resultat
    
    def appliquer_regles_westgard(self, resultat: ResultatModel) -> List[Dict]:
        """
        Appliquer les règles de Westgard pour le contrôle qualité.
        Retourne la liste des violations détectées.
        """
        violations = []
        
        # Récupérer les données de contrôle qualité récentes
        examen_id = resultat.examen_id
        jours_historique = 30
        
        resultats_recents = self.db.execute(
            select(ResultatModel)
            .where(
                ResultatModel.examen_id == examen_id,
                ResultatModel.date_analyse >= datetime.now() - timedelta(days=jours_historique),
                ResultatModel.statut_validation == StatutValidation.VALIDE.value
            )
            .order_by(ResultatModel.date_analyse.desc())
            .limit(100)
        ).scalars().all()
        
        if len(resultats_recents) < 20:
            # Pas assez de données pour appliquer Westgard
            return violations
        
        valeurs = [r.valeur_numerique for r in resultats_recents if r.valeur_numerique is not None]
        
        if not valeurs:
            return violations
        
        # Calculer moyenne et écart-type
        moyenne = sum(valeurs) / len(valeurs)
        variance = sum((x - moyenne) ** 2 for x in valeurs) / len(valeurs)
        ecart_type = variance ** 0.5
        
        valeur_actuelle = resultat.valeur_numerique
        
        # Règle 1-2s: Un point en dehors de ±2SD (avertissement)
        if abs(valeur_actuelle - moyenne) > 2 * ecart_type:
            violations.append({
                'regle': '1-2s',
                'description': 'Un point en dehors de ±2SD',
                'critique': False,
                'valeur': valeur_actuelle,
                'moyenne': moyenne,
                'ecart_type': ecart_type
            })
        
        # Règle 1-3s: Un point en dehors de ±3SD (rejet)
        if abs(valeur_actuelle - moyenne) > 3 * ecart_type:
            violations.append({
                'regle': '1-3s',
                'description': 'Un point en dehors de ±3SD',
                'critique': True,
                'valeur': valeur_actuelle,
                'moyenne': moyenne,
                'ecart_type': ecart_type
            })
        
        # Règle 2-2s: Deux points consécutifs > ±2SD (même côté)
        if len(valeurs) >= 2:
            if (valeurs[0] > moyenne + 2*ecart_type and valeur_actuelle > moyenne + 2*ecart_type) or \
               (valeurs[0] < moyenne - 2*ecart_type and valeur_actuelle < moyenne - 2*ecart_type):
                violations.append({
                    'regle': '2-2s',
                    'description': 'Deux points consécutifs > ±2SD (même côté)',
                    'critique': True,
                    'valeur': valeur_actuelle
                })
        
        # Règle R-4s: Écart > 4SD entre deux points consécutifs
        if len(valeurs) >= 1:
            if abs(valeur_actuelle - valeurs[0]) > 4 * ecart_type:
                violations.append({
                    'regle': 'R-4s',
                    'description': 'Écart > 4SD entre deux points consécutifs',
                    'critique': True,
                    'valeur': valeur_actuelle
                })
        
        # Règle 4-1s: Quatre points consécutifs > ±1SD (même côté)
        if len(valeurs) >= 3:
            count_same_side = sum(1 for v in valeurs[:3] if (v - moyenne) * (valeur_actuelle - moyenne) > 0)
            if count_same_side == 3 and abs(valeur_actuelle - moyenne) > ecart_type:
                violations.append({
                    'regle': '4-1s',
                    'description': 'Quatre points consécutifs > ±1SD (même côté)',
                    'critique': True,
                    'valeur': valeur_actuelle
                })
        
        # Règle 10-x: Dix points consécutifs du même côté de la moyenne
        if len(valeurs) >= 9:
            count_same_side = sum(1 for v in valeurs[:9] if (v - moyenne) > 0)
            if (count_same_side == 9 and valeur_actuelle > moyenne) or \
               (count_same_side == 0 and valeur_actuelle < moyenne):
                violations.append({
                    'regle': '10-x',
                    'description': 'Dix points consécutifs du même côté de la moyenne',
                    'critique': True,
                    'valeur': valeur_actuelle
                })
        
        return violations
    
    def get_resultats_a_valider(self, service_id: Optional[int] = None) -> List[ResultatModel]:
        """Récupérer les résultats en attente de validation."""
        query = select(ResultatModel).where(
            ResultatModel.statut_validation == StatutValidation.EN_ATTENTE.value
        )
        
        if service_id:
            query = query.where(ResultatModel.service_id == service_id)
        
        result = self.db.execute(query.order_by(ResultatModel.date_analyse.desc()))
        return list(result.scalars().all())
    
    def get_tendances_patient(
        self,
        patient_id: int,
        examen_id: int,
        jours: int = 365
    ) -> List[Tuple[datetime, float]]:
        """Récupérer l'historique des résultats pour un patient (tendances)."""
        resultats = self.db.execute(
            select(ResultatModel)
            .where(
                ResultatModel.patient_id == patient_id,
                ResultatModel.examen_id == examen_id,
                ResultatModel.statut_validation == StatutValidation.VALIDE.value,
                ResultatModel.date_analyse >= datetime.now() - timedelta(days=jours)
            )
            .order_by(ResultatModel.date_analyse.asc())
        ).scalars().all()
        
        return [(r.date_analyse, r.valeur_numerique) for r in resultats if r.valeur_numerique]
    
    def detecter_resultats_critiques(
        self,
        resultat_id: Optional[int] = None
    ) -> List[ResultatModel]:
        """Détecter les résultats critiques (valeurs alarmantes)."""
        
        query = select(ResultatModel).where(
            ResultatModel.statut_validation == StatutValidation.VALIDE.value
        )
        
        if resultat_id:
            query = query.where(ResultatModel.id == resultat_id)
        
        resultats = self.db.execute(query).scalars().all()
        resultats_critiques = []
        
        for resultat in resultats:
            examen = self.db.get(ExamenModel, resultat.examen_id)
            if examen and examen.seuil_critique_bas and resultat.valeur_numerique:
                if resultat.valeur_numerique < examen.seuil_critique_bas:
                    resultats_critiques.append(resultat)
            if examen and examen.seuil_critique_haut and resultat.valeur_numerique:
                if resultat.valeur_numerique > examen.seuil_critique_haut:
                    resultats_critiques.append(resultat)
        
        return resultats_critiques
