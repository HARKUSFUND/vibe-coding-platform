"""
Service de gestion des dons de sang.
Gère le cycle complet : prélèvement → tubes → poches → qualification.
"""
from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import select

from igors.core.domain.don import Don, Tube, StatutDon
from igors.core.domain.psl import TypePSL, DureeConservation
from igors.infrastructure.models.don import DonModel, TubeModel
from igors.infrastructure.models.poche import PocheModel, QualificationBiologique
from igors.infrastructure.models.donneur import DonneurModel
from igors.infrastructure.security.encryption import encrypt_field, decrypt_field


class DonService:
    """Service métier pour la gestion des dons."""
    
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def creer_don(
        self,
        donneur_id: int,
        type_don: str,
        date_prelevement: datetime,
        volume_preleve: float,
        operateur_id: int
    ) -> DonModel:
        """Créer un nouveau don avec tubes associés."""
        
        # Vérifier éligibilité donneur (délai depuis dernier don)
        dernier_don = self.db.execute(
            select(DonModel).where(
                DonModel.donneur_id == donneur_id,
                DonModel.statut != StatutDon.ANNULE.value
            ).order_by(DonModel.date_prelevement.desc())
        ).scalar_one_or_none()
        
        if dernier_don:
            delai_min = self._get_delai_minimal(type_don)
            if datetime.now() - dernier_don.date_prelevement < delai_min:
                raise ValueError(
                    f"Délai minimum non respecté. "
                    f"Prochain don possible le: {dernier_don.date_prelevement + delai_min}"
                )
        
        # Créer le don
        don = DonModel(
            donneur_id=donneur_id,
            type_don=type_don,
            date_prelevement=date_prelevement,
            volume_preleve=volume_preleve,
            operateur_id=operateur_id,
            statut=StatutDon.EN_COURS.value,
            code_barres=self._generer_code_barres(),
            date_creation=datetime.now()
        )
        
        self.db.add(don)
        self.db.flush()  # Pour obtenir l'ID
        
        # Créer les tubes par défaut selon le type de don
        tubes_config = self._get_tubes_config(type_don)
        for tube_config in tubes_config:
            tube = TubeModel(
                don_id=don.id,
                type_tube=tube_config['type'],
                volume=tube_config['volume'],
                anticoagulant=tube_config.get('anticoagulant'),
                code_barres=self._generer_code_barres()
            )
            self.db.add(tube)
        
        self.db.commit()
        self.db.refresh(don)
        
        return don
    
    def _get_delai_minimal(self, type_don: str) -> timedelta:
        """Retourner le délai minimal entre deux dons selon le type."""
        delais = {
            'sang_total': timedelta(days=56),  # 8 semaines
            'plasma': timedelta(days=14),       # 2 semaines
            'plaquettes': timedelta(days=7),    # 1 semaine
            'globules_rouges': timedelta(days=56)
        }
        return delais.get(type_don, timedelta(days=56))
    
    def _get_tubes_config(self, type_don: str) -> List[dict]:
        """Configuration des tubes selon le type de don."""
        configs = {
            'sang_total': [
                {'type': 'EDTA', 'volume': 4.0, 'anticoagulant': 'K3EDTA'},
                {'type': 'Citrate', 'volume': 3.8, 'anticoagulant': 'Citrate trisodique'},
                {'type': 'Sec', 'volume': 5.0}
            ],
            'plasma': [
                {'type': 'Citrate', 'volume': 3.8, 'anticoagulant': 'Citrate trisodique'}
            ],
            'plaquettes': [
                {'type': 'Citrate', 'volume': 3.8, 'anticoagulant': 'Citrate trisodique'},
                {'type': 'EDTA', 'volume': 4.0, 'anticoagulant': 'K3EDTA'}
            ]
        }
        return configs.get(type_don, configs['sang_total'])
    
    def _generer_code_barres(self) -> str:
        """Générer un code-barres unique ISBT 128 compatible."""
        import random
        prefix = "ISBT"
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        suffix = "".join([str(random.randint(0, 9)) for _ in range(4)])
        return f"{prefix}{timestamp}{suffix}"
    
    def qualifier_poches(
        self,
        don_id: int,
        resultats_vih: bool,
        resultats_vhb: bool,
        resultats_vhc: bool,
        resultats_syphilis: bool,
        biologiste_id: int,
        commentaire: Optional[str] = None
    ) -> PocheModel:
        """Qualifier biologiquement les poches issues du don."""
        
        don = self.db.get(DonModel, don_id)
        if not don:
            raise ValueError(f"Don {don_id} introuvable")
        
        # Déterminer si le don est qualifié ou exclu
        marqueurs_positifs = []
        if resultats_vih:
            marqueurs_positifs.append('VIH')
        if resultats_vhb:
            marqueurs_positifs.append('VHB')
        if resultats_vhc:
            marqueurs_positifs.append('VHC')
        if resultats_syphilis:
            marqueurs_positifs.append('SYPHILIS')
        
        statut_qualification = (
            QualificationBiologique.EXCLU if marqueurs_positifs
            else QualificationBiologique.VALIDE
        )
        
        # Mettre à jour le don
        don.statut = (
            StatutDon.EXCLU if marqueurs_positifs
            else StatutDon.QUALIFIE
        )
        
        # Créer/mettre à jour les poches
        poches = self.db.execute(
            select(PocheModel).where(PocheModel.don_id == don_id)
        ).scalars().all()
        
        for poche in poches:
            poche.statut_qualification = statut_qualification.value
            poche.marqueurs_positifs = ','.join(marqueurs_positifs) if marqueurs_positifs else None
            poche.date_qualification = datetime.now()
            poche.biologiste_id = biologiste_id
            poche.commentaire_qualification = commentaire
            
            # Anonymiser si VIH+ (CDC §4.2)
            if resultats_vih:
                poche.anonymise_vih = True
        
        self.db.commit()
        
        return poches[0] if poches else None
    
    def get_dons_by_donneur(self, donneur_id: int) -> List[DonModel]:
        """Récupérer l'historique des dons d'un donneur."""
        result = self.db.execute(
            select(DonModel)
            .where(DonModel.donneur_id == donneur_id)
            .order_by(DonModel.date_prelevement.desc())
        )
        return list(result.scalars().all())
    
    def get_dons_en_attente_qualification(self) -> List[DonModel]:
        """Récupérer les dons en attente de qualification biologique."""
        result = self.db.execute(
            select(DonModel)
            .where(DonModel.statut == StatutDon.EN_COURS.value)
            .order_by(DonModel.date_prelevement.desc())
        )
        return list(result.scalars().all())
    
    def annuler_don(self, don_id: int, raison: str, operateur_id: int) -> DonModel:
        """Annuler un don avec traçabilité."""
        don = self.db.get(DonModel, don_id)
        if not don:
            raise ValueError(f"Don {don_id} introuvable")
        
        don.statut = StatutDon.ANNULE.value
        don.raison_annulation = raison
        don.operateur_annulation_id = operateur_id
        don.date_annulation = datetime.now()
        
        self.db.commit()
        self.db.refresh(don)
        
        return don
