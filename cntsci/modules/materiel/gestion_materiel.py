"""
Module de gestion du matériel informatique
Gère l'inventaire, les maintenances et le suivi des équipements
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from core.database import db_manager
from core.security import security_manager, AuditAction, Utilisateur
from core.config import ALERT_CONFIG


class TypeEquipement(Enum):
    """Types d'équipements informatiques"""
    ORDINATEUR = "Ordinateur"
    PORTABLE = "Portable"
    SERVEUR = "Serveur"
    IMPRIMANTE = "Imprimante"
    SCANNER = "Scanner"
    EQUIPEMENT_RESEAU = "Équipement réseau"
    AUTRE = "Autre"


class EtatEquipement(Enum):
    """États possibles d'un équipement"""
    NEUF = "Neuf"
    BON = "Bon"
    MOYEN = "Moyen"
    MAUVAIS = "Mauvais"
    EN_PANNE = "En panne"
    REFORME = "Réformé"


@dataclass
class Materiel:
    """Représente un équipement informatique"""
    id: Optional[int] = None
    reference: str = ""
    type_equipment: str = ""
    marque: str = ""
    modele: str = ""
    numero_serie: str = ""
    date_acquisition: Optional[date] = None
    date_garantie: Optional[date] = None
    etat: str = "NEUF"
    localisation: str = ""
    affecte_a: Optional[int] = None
    date_derniere_maintenance: Optional[date] = None
    notes: str = ""
    
    def est_sous_garantie(self) -> bool:
        """Vérifie si l'équipement est encore sous garantie"""
        if not self.date_garantie:
            return False
        return date.today() <= self.date_garantie
    
    def jours_restant_garantie(self) -> int:
        """Retourne le nombre de jours restants de garantie"""
        if not self.date_garantie:
            return 0
        delta = self.date_garantie - date.today()
        return max(0, delta.days)
    
    def necessite_maintenance(self) -> bool:
        """Vérifie si l'équipement nécessite une maintenance"""
        if not self.date_derniere_maintenance:
            return True
        # Maintenance recommandée tous les 6 mois
        six_mois_avant = date.today() - timedelta(days=180)
        return self.date_derniere_maintenance < six_mois_avant


class GestionnaireMateriel:
    """Gestionnaire des opérations sur le matériel informatique"""
    
    def __init__(self):
        self.db = db_manager
    
    def ajouter_materiel(self, materiel: Materiel, utilisateur: Utilisateur) -> Optional[int]:
        """
        Ajoute un nouvel équipement à l'inventaire
        Retourne l'ID du matériel créé ou None en cas d'échec
        """
        query = """
        INSERT INTO materiel_informatique 
        (reference, type_equipment, marque, modele, numero_serie, 
         date_acquisition, date_garantie, etat, localisation, 
         affecte_a, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            materiel.reference,
            materiel.type_equipment,
            materiel.marque,
            materiel.modele,
            materiel.numero_serie,
            materiel.date_acquisition,
            materiel.date_garantie,
            materiel.etat,
            materiel.localisation,
            materiel.affecte_a,
            materiel.notes,
        )
        
        try:
            result = self.db.executer_requete(query, params, fetch=True, commit=True)
            if result:
                materiel.id = result[0]['id']
                security_manager.enregistrer_audit(
                    utilisateur, AuditAction.CREATE,
                    f"Ajout matériel: {materiel.reference}"
                )
                return materiel.id
        except Exception as e:
            print(f"Erreur ajout matériel: {e}")
        
        return None
    
    def obtenir_tout_materiel(self) -> List[Dict[str, Any]]:
        """Retourne la liste complète du matériel"""
        query = "SELECT * FROM materiel_informatique ORDER BY reference"
        return self.db.executer_requete(query) or []
    
    def obtenir_materiel_par_id(self, materiel_id: int) -> Optional[Dict[str, Any]]:
        """Retourne un équipement par son ID"""
        query = "SELECT * FROM materiel_informatique WHERE id = %s"
        results = self.db.executer_requete(query, (materiel_id,))
        return results[0] if results else None
    
    def mettre_a_jour_materiel(self, materiel: Materiel, utilisateur: Utilisateur) -> bool:
        """Met à jour les informations d'un équipement"""
        query = """
        UPDATE materiel_informatique
        SET type_equipment = %s, marque = %s, modele = %s, 
            numero_serie = %s, date_acquisition = %s, date_garantie = %s,
            etat = %s, localisation = %s, affecte_a = %s, 
            date_derniere_maintenance = %s, notes = %s
        WHERE id = %s
        """
        
        params = (
            materiel.type_equipment,
            materiel.marque,
            materiel.modele,
            materiel.numero_serie,
            materiel.date_acquisition,
            materiel.date_garantie,
            materiel.etat,
            materiel.localisation,
            materiel.affecte_a,
            materiel.date_derniere_maintenance,
            materiel.notes,
            materiel.id,
        )
        
        try:
            self.db.executer_requete(query, params, fetch=False, commit=True)
            security_manager.enregistrer_audit(
                utilisateur, AuditAction.UPDATE,
                f"Mise à jour matériel: {materiel.reference}"
            )
            return True
        except Exception as e:
            print(f"Erreur mise à jour matériel: {e}")
            return False
    
    def supprimer_materiel(self, materiel_id: int, utilisateur: Utilisateur) -> bool:
        """Supprime un équipement de l'inventaire"""
        query = "DELETE FROM materiel_informatique WHERE id = %s"
        
        try:
            self.db.executer_requete(query, (materiel_id,), fetch=False, commit=True)
            security_manager.enregistrer_audit(
                utilisateur, AuditAction.DELETE,
                f"Suppression matériel ID: {materiel_id}"
            )
            return True
        except Exception as e:
            print(f"Erreur suppression matériel: {e}")
            return False
    
    def rechercher_materiel(self, terme: str) -> List[Dict[str, Any]]:
        """Recherche du matériel par référence, marque ou modèle"""
        query = """
        SELECT * FROM materiel_informatique
        WHERE reference ILIKE %s OR marque ILIKE %s OR modele ILIKE %s
        ORDER BY reference
        """
        search_term = f"%{terme}%"
        return self.db.executer_requete(query, (search_term, search_term, search_term)) or []
    
    def obtenir_alertes_garantie(self) -> List[Dict[str, Any]]:
        """Retourne les équipements dont la garantie expire bientôt"""
        jours_avertissement = ALERT_CONFIG['expiration_garantie_jours']
        query = """
        SELECT *, 
               (date_garantie - CURRENT_DATE) as jours_restants
        FROM materiel_informatique
        WHERE date_garantie IS NOT NULL
          AND date_garantie >= CURRENT_DATE
          AND date_garantie <= CURRENT_DATE + INTERVAL '%s days'
        ORDER BY date_garantie
        """
        return self.db.executer_requete(query, (jours_avertissement,)) or []
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le parc informatique"""
        stats = {}
        
        # Nombre total par état
        query_etat = """
        SELECT etat, COUNT(*) as nombre
        FROM materiel_informatique
        GROUP BY etat
        """
        stats['par_etat'] = self.db.executer_requete(query_etat) or []
        
        # Nombre total par type
        query_type = """
        SELECT type_equipment, COUNT(*) as nombre
        FROM materiel_informatique
        GROUP BY type_equipment
        """
        stats['par_type'] = self.db.executer_requete(query_type) or []
        
        # Équipements sous garantie
        query_garantie = """
        SELECT COUNT(*) as nombre
        FROM materiel_informatique
        WHERE date_garantie >= CURRENT_DATE
        """
        result = self.db.executer_requete(query_garantie)
        stats['sous_garantie'] = result[0]['nombre'] if result else 0
        
        # Équipements nécessitant maintenance
        query_maintenance = """
        SELECT COUNT(*) as nombre
        FROM materiel_informatique
        WHERE date_derniere_maintenance IS NULL
           OR date_derniere_maintenance < CURRENT_DATE - INTERVAL '6 months'
        """
        result = self.db.executer_requete(query_maintenance)
        stats['a_maintenir'] = result[0]['nombre'] if result else 0
        
        return stats


@dataclass
class Maintenance:
    """Représente une intervention de maintenance"""
    id: Optional[int] = None
    materiel_id: int = 0
    type_maintenance: str = ""
    description: str = ""
    technicien: str = ""
    cout: float = 0.0
    date_intervention: Optional[date] = None
    date_prochaine_maintenance: Optional[date] = None
    statut: str = "PLANIFIEE"
    
    def enregistrer_maintenance(self, utilisateur: Utilisateur) -> Optional[int]:
        """Enregistre une maintenance dans la base de données"""
        query = """
        INSERT INTO maintenances_materiel
        (materiel_id, type_maintenance, description, technicien, 
         cout, date_intervention, date_prochaine_maintenance, statut)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            self.materiel_id,
            self.type_maintenance,
            self.description,
            self.technicien,
            self.cout,
            self.date_intervention,
            self.date_prochaine_maintenance,
            self.statut,
        )
        
        try:
            result = db_manager.executer_requete(query, params, fetch=True, commit=True)
            if result:
                self.id = result[0]['id']
                security_manager.enregistrer_audit(
                    utilisateur, AuditAction.CREATE,
                    f"Maintenance matériel ID: {self.materiel_id}"
                )
                
                # Mettre à jour la date de dernière maintenance du matériel
                update_materiel = """
                UPDATE materiel_informatique
                SET date_derniere_maintenance = %s
                WHERE id = %s
                """
                db_manager.executer_requete(
                    update_materiel, 
                    (self.date_intervention, self.materiel_id),
                    fetch=False, commit=True
                )
                
                return self.id
        except Exception as e:
            print(f"Erreur enregistrement maintenance: {e}")
        
        return None
    
    @staticmethod
    def obtenir_historique_materiel(materiel_id: int) -> List[Dict[str, Any]]:
        """Retourne l'historique des maintenances d'un équipement"""
        query = """
        SELECT * FROM maintenances_materiel
        WHERE materiel_id = %s
        ORDER BY date_intervention DESC
        """
        return db_manager.executer_requete(query, (materiel_id,)) or []
