"""
Module de gestion du parc automobile
Gère les véhicules, assurances, maintenances et suivi
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

from core.database import db_manager
from core.security import security_manager, AuditAction, Utilisateur
from core.config import ALERT_CONFIG


@dataclass
class Vehicule:
    """Représente un véhicule du parc automobile"""
    id: Optional[int] = None
    immatriculation: str = ""
    marque: str = ""
    modele: str = ""
    annee: int = 0
    numero_chassis: str = ""
    type_vehicule: str = ""
    kilometrage: int = 0
    date_acquisition: Optional[date] = None
    date_assurance: Optional[date] = None
    date_fin_assurance: Optional[date] = None
    compagnie_assurance: str = ""
    numero_police_assurance: str = ""
    date_derniere_maintenance: Optional[date] = None
    prochaine_maintenance_km: int = 0
    etat: str = "BON"
    affecte_a: Optional[int] = None
    notes: str = ""
    
    def est_assure(self) -> bool:
        """Vérifie si le véhicule est assuré"""
        if not self.date_fin_assurance:
            return False
        return date.today() <= self.date_fin_assurance
    
    def jours_restant_assurance(self) -> int:
        """Retourne le nombre de jours restants d'assurance"""
        if not self.date_fin_assurance:
            return 0
        delta = self.date_fin_assurance - date.today()
        return max(0, delta.days)
    
    def necessite_maintenance(self) -> bool:
        """Vérifie si le véhicule nécessite une maintenance"""
        # Maintenance si km seuil atteint ou 6 mois écoulés
        km_seuil = ALERT_CONFIG['maintenance_vehicle_km_seuil']
        mois_seuil = ALERT_CONFIG['maintenance_vehicle_mois_seuil']
        
        if self.prochaine_maintenance_km > 0 and self.kilometrage >= self.prochaine_maintenance_km:
            return True
        
        if self.date_derniere_maintenance:
            six_mois_avant = date.today() - timedelta(days=mois_seuil * 30)
            return self.date_derniere_maintenance < six_mois_avant
        
        return True
    
    def calculer_consommation(self, litres_consumes: float, kms_parcourus: float) -> float:
        """Calcule la consommation aux 100km"""
        if kms_parcourus == 0:
            return 0.0
        return (litres_consumes / kms_parcourus) * 100


class GestionnaireAutomobile:
    """Gestionnaire des opérations sur le parc automobile"""
    
    def __init__(self):
        self.db = db_manager
    
    def ajouter_vehicule(self, vehicule: Vehicule, utilisateur: Utilisateur) -> Optional[int]:
        """
        Ajoute un nouveau véhicule au parc
        Retourne l'ID du véhicule créé ou None en cas d'échec
        """
        query = """
        INSERT INTO vehicules
        (immatriculation, marque, modele, annee, numero_chassis, 
         type_vehicule, kilometrage, date_acquisition, date_assurance,
         date_fin_assurance, compagnie_assurance, numero_police_assurance,
         prochaine_maintenance_km, etat, affecte_a, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            vehicule.immatriculation,
            vehicule.marque,
            vehicule.modele,
            vehicule.annee,
            vehicule.numero_chassis,
            vehicule.type_vehicule,
            vehicule.kilometrage,
            vehicule.date_acquisition,
            vehicule.date_assurance,
            vehicule.date_fin_assurance,
            vehicule.compagnie_assurance,
            vehicule.numero_police_assurance,
            vehicule.prochaine_maintenance_km,
            vehicule.etat,
            vehicule.affecte_a,
            vehicule.notes,
        )
        
        try:
            result = self.db.executer_requete(query, params, fetch=True, commit=True)
            if result:
                vehicule.id = result[0]['id']
                security_manager.enregistrer_audit(
                    utilisateur, AuditAction.CREATE,
                    f"Ajout véhicule: {vehicule.immatriculation}"
                )
                return vehicule.id
        except Exception as e:
            print(f"Erreur ajout véhicule: {e}")
        
        return None
    
    def obtenir_tout_vehicule(self) -> List[Dict[str, Any]]:
        """Retourne la liste complète des véhicules"""
        query = "SELECT * FROM vehicules ORDER BY immatriculation"
        return self.db.executer_requete(query) or []
    
    def obtenir_vehicule_par_id(self, vehicule_id: int) -> Optional[Dict[str, Any]]:
        """Retourne un véhicule par son ID"""
        query = "SELECT * FROM vehicules WHERE id = %s"
        results = self.db.executer_requete(query, (vehicule_id,))
        return results[0] if results else None
    
    def obtenir_vehicule_par_immatriculation(self, immatriculation: str) -> Optional[Dict[str, Any]]:
        """Retourne un véhicule par son immatriculation"""
        query = "SELECT * FROM vehicules WHERE immatriculation = %s"
        results = self.db.executer_requete(query, (immatriculation,))
        return results[0] if results else None
    
    def mettre_a_jour_vehicule(self, vehicule: Vehicule, utilisateur: Utilisateur) -> bool:
        """Met à jour les informations d'un véhicule"""
        query = """
        UPDATE vehicules
        SET marque = %s, modele = %s, annee = %s, numero_chassis = %s,
            type_vehicule = %s, kilometrage = %s, date_acquisition = %s,
            date_assurance = %s, date_fin_assurance = %s,
            compagnie_assurance = %s, numero_police_assurance = %s,
            date_derniere_maintenance = %s, prochaine_maintenance_km = %s,
            etat = %s, affecte_a = %s, notes = %s
        WHERE id = %s
        """
        
        params = (
            vehicule.marque,
            vehicule.modele,
            vehicule.annee,
            vehicule.numero_chassis,
            vehicule.type_vehicule,
            vehicule.kilometrage,
            vehicule.date_acquisition,
            vehicule.date_assurance,
            vehicule.date_fin_assurance,
            vehicule.compagnie_assurance,
            vehicule.numero_police_assurance,
            vehicule.date_derniere_maintenance,
            vehicule.prochaine_maintenance_km,
            vehicule.etat,
            vehicule.affecte_a,
            vehicule.notes,
            vehicule.id,
        )
        
        try:
            self.db.executer_requete(query, params, fetch=False, commit=True)
            security_manager.enregistrer_audit(
                utilisateur, AuditAction.UPDATE,
                f"Mise à jour véhicule: {vehicule.immatriculation}"
            )
            return True
        except Exception as e:
            print(f"Erreur mise à jour véhicule: {e}")
            return False
    
    def supprimer_vehicule(self, vehicule_id: int, utilisateur: Utilisateur) -> bool:
        """Supprime un véhicule du parc"""
        query = "DELETE FROM vehicules WHERE id = %s"
        
        try:
            self.db.executer_requete(query, (vehicule_id,), fetch=False, commit=True)
            security_manager.enregistrer_audit(
                utilisateur, AuditAction.DELETE,
                f"Suppression véhicule ID: {vehicule_id}"
            )
            return True
        except Exception as e:
            print(f"Erreur suppression véhicule: {e}")
            return False
    
    def rechercher_vehicule(self, terme: str) -> List[Dict[str, Any]]:
        """Recherche des véhicules par immatriculation, marque ou modèle"""
        query = """
        SELECT * FROM vehicules
        WHERE immatriculation ILIKE %s OR marque ILIKE %s OR modele ILIKE %s
        ORDER BY immatriculation
        """
        search_term = f"%{terme}%"
        return self.db.executer_requete(query, (search_term, search_term, search_term)) or []
    
    def obtenir_alertes_assurance(self) -> List[Dict[str, Any]]:
        """Retourne les véhicules dont l'assurance expire bientôt"""
        jours_avertissement = ALERT_CONFIG['expiration_assurance_jours']
        query = """
        SELECT *,
               (date_fin_assurance - CURRENT_DATE) as jours_restants
        FROM vehicules
        WHERE date_fin_assurance IS NOT NULL
          AND date_fin_assurance >= CURRENT_DATE
          AND date_fin_assurance <= CURRENT_DATE + INTERVAL '%s days'
        ORDER BY date_fin_assurance
        """
        return self.db.executer_requete(query, (jours_avertissement,)) or []
    
    def obtenir_vehicules_non_assures(self) -> List[Dict[str, Any]]:
        """Retourne les véhicules non assurés"""
        query = """
        SELECT * FROM vehicules
        WHERE date_fin_assurance IS NULL
           OR date_fin_assurance < CURRENT_DATE
        ORDER BY immatriculation
        """
        return self.db.executer_requete(query) or []
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le parc automobile"""
        stats = {}
        
        # Nombre total par état
        query_etat = """
        SELECT etat, COUNT(*) as nombre
        FROM vehicules
        GROUP BY etat
        """
        stats['par_etat'] = self.db.executer_requete(query_etat) or []
        
        # Nombre total par type
        query_type = """
        SELECT type_vehicule, COUNT(*) as nombre
        FROM vehicules
        GROUP BY type_vehicule
        """
        stats['par_type'] = self.db.executer_requete(query_type) or []
        
        # Véhicules assurés
        query_assures = """
        SELECT COUNT(*) as nombre
        FROM vehicules
        WHERE date_fin_assurance >= CURRENT_DATE
        """
        result = self.db.executer_requete(query_assures)
        stats['assures'] = result[0]['nombre'] if result else 0
        
        # Véhicules non assurés
        result = self.db.executer_requete("SELECT COUNT(*) as nombre FROM vehicules")
        total = result[0]['nombre'] if result else 0
        stats['non_assures'] = total - stats['assures']
        
        # Kilométrage moyen
        query_km = """
        SELECT AVG(kilometrage) as moyenne
        FROM vehicules
        """
        result = self.db.executer_requete(query_km)
        stats['km_moyen'] = round(result[0]['moyenne'], 2) if result and result[0]['moyenne'] else 0
        
        return stats
    
    def mettre_a_jour_kilometrage(self, vehicule_id: int, nouveau_km: int, 
                                  utilisateur: Utilisateur) -> bool:
        """Met à jour le kilométrage d'un véhicule"""
        query = """
        UPDATE vehicules
        SET kilometrage = %s
        WHERE id = %s
        """
        
        try:
            self.db.executer_requete(query, (nouveau_km, vehicule_id), fetch=False, commit=True)
            security_manager.enregistrer_audit(
                utilisateur, AuditAction.UPDATE,
                f"Mise à jour kilométrage véhicule ID: {vehicule_id} - {nouveau_km} km"
            )
            return True
        except Exception as e:
            print(f"Erreur mise à jour kilométrage: {e}")
            return False


@dataclass
class MaintenanceVehicule:
    """Représente une maintenance de véhicule"""
    id: Optional[int] = None
    vehicule_id: int = 0
    type_maintenance: str = ""
    description: str = ""
    garagiste: str = ""
    cout: float = 0.0
    kilometrage_intervention: int = 0
    date_intervention: Optional[date] = None
    prochaine_maintenance_km: int = 0
    prochaine_maintenance_date: Optional[date] = None
    statut: str = "PLANIFIEE"
    
    def enregistrer_maintenance(self, utilisateur: Utilisateur) -> Optional[int]:
        """Enregistre une maintenance dans la base de données"""
        query = """
        INSERT INTO maintenances_vehicules
        (vehicule_id, type_maintenance, description, garagiste,
         cout, kilometrage_intervention, date_intervention,
         prochaine_maintenance_km, prochaine_maintenance_date, statut)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            self.vehicule_id,
            self.type_maintenance,
            self.description,
            self.garagiste,
            self.cout,
            self.kilometrage_intervention,
            self.date_intervention,
            self.prochaine_maintenance_km,
            self.prochaine_maintenance_date,
            self.statut,
        )
        
        try:
            result = db_manager.executer_requete(query, params, fetch=True, commit=True)
            if result:
                self.id = result[0]['id']
                security_manager.enregistrer_audit(
                    utilisateur, AuditAction.CREATE,
                    f"Maintenance véhicule ID: {self.vehicule_id}"
                )
                
                # Mettre à jour le véhicule
                update_vehicule = """
                UPDATE vehicules
                SET date_derniere_maintenance = %s,
                    prochaine_maintenance_km = %s
                WHERE id = %s
                """
                db_manager.executer_requete(
                    update_vehicule,
                    (self.date_intervention, self.prochaine_maintenance_km, self.vehicule_id),
                    fetch=False, commit=True
                )
                
                return self.id
        except Exception as e:
            print(f"Erreur enregistrement maintenance véhicule: {e}")
        
        return None
    
    @staticmethod
    def obtenir_historique_vehicule(vehicule_id: int) -> List[Dict[str, Any]]:
        """Retourne l'historique des maintenances d'un véhicule"""
        query = """
        SELECT * FROM maintenances_vehicules
        WHERE vehicule_id = %s
        ORDER BY date_intervention DESC
        """
        return db_manager.executer_requete(query, (vehicule_id,)) or []


@dataclass
class SuiviCarburant:
    """Suivi de la consommation de carburant"""
    vehicule_id: int = 0
    date_plein: Optional[date] = None
    kilometrage: int = 0
    litres: float = 0.0
    cout_total: float = 0.0
    prix_litre: float = 0.0
    
    def enregistrer_plein(self, utilisateur: Utilisateur) -> bool:
        """Enregistre un plein de carburant"""
        # Cette fonctionnalité sera étendue en V2 avec table dédiée
        security_manager.enregistrer_audit(
            utilisateur, AuditAction.CREATE,
            f"Plein carburant véhicule ID: {self.vehicule_id} - {self.litres}L"
        )
        return True
    
    def calculer_consommation_aux_100km(self, kilometrage_precedent: int) -> float:
        """Calcule la consommation aux 100km"""
        if precedent == 0 or self.kilometrage <= precedent:
            return 0.0
        distance = self.kilometrage - precedent
        return (self.litres / distance) * 100


# Module __init__ pour le package automobile
__all__ = ['Vehicule', 'GestionnaireAutomobile', 'MaintenanceVehicule', 'SuiviCarburant']
