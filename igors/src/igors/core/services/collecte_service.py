"""
Service Collecte - Gestion des collectes de sang
Conforme CDC §4.2 - Processus de collecte et tubes
"""
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from igors.infrastructure.repositories.don_repo import DonRepository
from igors.infrastructure.repositories.donneur_repo import DonneurRepository
from igors.infrastructure.repositories.patient_repo import PatientRepository
from igors.core.domain.don import Don


class CollecteService:
    """Service métier pour la gestion des collectes de sang"""
    
    def __init__(self, session: Session):
        self.session = session
        self.don_repo = DonRepository(session)
        self.donneur_repo = DonneurRepository(session)
        self.patient_repo = PatientRepository(session)
    
    def verifier_eligibilite_don(self, donneur_id: int) -> Dict:
        """Vérifier si un donneur est éligible au don"""
        donneur = self.donneur_repo.get_by_id(donneur_id)
        if not donneur:
            return {
                'eligible': False,
                'raison': 'Donneur non trouvé'
            }
        
        # Vérifier le consentement
        if not donneur.consentement_signe:
            return {
                'eligible': False,
                'raison': 'Consentement non signé'
            }
        
        # Vérifier la date du dernier don
        derniers_dons = self.don_repo.get_by_donneur(donneur_id)
        if derniers_dons:
            dernier_don = max(derniers_dons, key=lambda d: d.date_don)
            delai_minimum = self._get_delai_minimum(dernier_don.type_don)
            date_prochain_don = dernier_don.date_don + timedelta(days=delai_minimum)
            
            if datetime.now().date() < date_prochain_don:
                jours_restants = (date_prochain_don - datetime.now().date()).days
                return {
                    'eligible': False,
                    'raison': f'Délai minimum non respecté. Prochain don possible dans {jours_restants} jours',
                    'date_prochain_don': date_prochain_don
                }
        
        # Vérifier les contre-indications médicales
        if donneur.contre_indication_temporaire:
            return {
                'eligible': False,
                'raison': f'Contre-indication temporaire: {donneur.contre_indication_temporaire}'
            }
        
        return {
            'eligible': True,
            'donneur': {
                'id': donneur.id,
                'nom': donneur.nom,
                'prenom': donneur.prenom,
                'groupe_sanguin': donneur.groupe_sanguin,
                'facteur_rhesus': donneur.facteur_rhesus
            }
        }
    
    def _get_delai_minimum(self, type_don: str) -> int:
        """Obtenir le délai minimum entre deux dons selon le type"""
        delais = {
            'sang_total': 56,      # 8 semaines
            'plasma': 7,           # 1 semaine
            'plaquettes': 14,      # 2 semaines
            'double_plasma': 28,   # 4 semaines
            'double_plaquettes': 28  # 4 semaines
        }
        return delais.get(type_don, 56)
    
    def enregistrer_collecte(self, don_data: dict, tubes: List[dict]) -> Dict:
        """Enregistrer une nouvelle collecte avec ses tubes"""
        try:
            # Vérifier l'éligibilité
            eligibilite = self.verifier_eligibilite_don(don_data['donneur_id'])
            if not eligibilite['eligible']:
                return {
                    'success': False,
                    'error': eligibilite['raison']
                }
            
            # Créer le don
            don = Don(
                donneur_id=don_data['donneur_id'],
                type_don=don_data['type_don'],
                lieu_collecte=don_data.get('lieu_collecte', 'CNTS Abidjan'),
                personnel_id=don_data.get('personnel_id'),
                poids_don=don_data.get('poids_don'),
                duree_collecte=don_data.get('duree_collecte'),
                incident=don_data.get('incident', False),
                commentaire=don_data.get('commentaire')
            )
            
            db_don = self.don_repo.create(don)
            
            # Ajouter les tubes
            for tube_data in tubes:
                # Ici on créerait les tubes associés au don
                # Cette logique dépend du modèle Tube qui doit être créé
                pass
            
            return {
                'success': True,
                'don_id': db_don.id,
                'code_barres': db_don.code_barres,
                'message': 'Collecte enregistrée avec succès'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_collectes_du_jour(self) -> List[Dict]:
        """Récupérer toutes les collectes du jour"""
        today = datetime.now().date()
        collects = self.don_repo.get_dons_recents(days=1)
        
        return [
            {
                'id': c.id,
                'donneur_nom': c.donneur.nom if c.donneur else 'Inconnu',
                'donneur_prenom': c.donneur.prenom if c.donneur else 'Inconnu',
                'type_don': c.type_don,
                'date_don': c.date_don,
                'statut': c.statut,
                'lieu': c.lieu_collecte
            }
            for c in collects if c.date_don.date() == today
        ]
    
    def get_statistiques_collectes(self, date_debut: datetime = None, date_fin: datetime = None) -> Dict:
        """Obtenir des statistiques sur les collectes"""
        stats = {
            'total_collectes': 0,
            'par_type': {},
            'par_lieu': {},
            'taux_incidents': 0.0,
            'volume_total': 0.0
        }
        
        # Statistiques par type
        stats['par_type'] = self.don_repo.count_dons_by_type(date_debut, date_fin)
        stats['total_collectes'] = sum(stats['par_type'].values())
        
        # Calculer le taux d'incidents et volume total
        # Cette logique nécessiterait des méthodes supplémentaires dans le repository
        
        return stats
    
    def annuler_collecte(self, don_id: int, raison: str) -> Dict:
        """Annuler une collecte"""
        try:
            db_don = self.don_repo.get_by_id(don_id)
            if not db_don:
                return {
                    'success': False,
                    'error': 'Collecte non trouvée'
                }
            
            if db_don.poches and len(db_don.poches) > 0:
                return {
                    'success': False,
                    'error': 'Impossible d\'annuler: des poches ont déjà été créées'
                }
            
            return self.don_repo.delete(don_id)
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
