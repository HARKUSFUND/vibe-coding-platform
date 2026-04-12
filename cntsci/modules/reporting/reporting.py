"""
Module de reporting et tableaux de bord pour l'application CNTSCI
Génération de rapports, KPIs et exports de données
"""

from datetime import datetime, date
from typing import List, Dict, Any, Optional
import csv
import json
from pathlib import Path

from core.database import db_manager
from core.security import security_manager, AuditAction, Utilisateur
from core.config import EXPORT_CONFIG, STORAGE_PATHS


class ReportingManager:
    """Gestionnaire centralisé des rapports et KPIs"""
    
    def __init__(self):
        self.db = db_manager
    
    def obtenir_kpi_generaux(self) -> Dict[str, Any]:
        """Retourne les indicateurs clés globaux"""
        kpis = {}
        
        # Matériel informatique
        try:
            result = self.db.executer_requete("SELECT COUNT(*) as nombre FROM materiel_informatique")
            kpis['total_materiel'] = result[0]['nombre'] if result else 0
            
            result = self.db.executer_requete("""
                SELECT COUNT(*) as nombre 
                FROM materiel_informatique 
                WHERE date_garantie >= CURRENT_DATE
            """)
            kpis['materiel_sous_garantie'] = result[0]['nombre'] if result else 0
            
            result = self.db.executer_requete("""
                SELECT COUNT(*) as nombre 
                FROM materiel_informatique 
                WHERE etat = 'EN_PANNE'
            """)
            kpis['materiel_en_panne'] = result[0]['nombre'] if result else 0
        except Exception as e:
            print(f"Erreur KPI matériel: {e}")
            kpis['total_materiel'] = 0
            kpis['materiel_sous_garantie'] = 0
            kpis['materiel_en_panne'] = 0
        
        # Parc automobile
        try:
            result = self.db.executer_requete("SELECT COUNT(*) as nombre FROM vehicules")
            kpis['total_vehicules'] = result[0]['nombre'] if result else 0
            
            result = self.db.executer_requete("""
                SELECT COUNT(*) as nombre 
                FROM vehicules 
                WHERE date_fin_assurance >= CURRENT_DATE
            """)
            kpis['vehicules_assures'] = result[0]['nombre'] if result else 0
            
            result = self.db.executer_requete("""
                SELECT COUNT(*) as nombre 
                FROM vehicules 
                WHERE date_fin_assurance < CURRENT_DATE OR date_fin_assurance IS NULL
            """)
            kpis['vehicules_non_assures'] = result[0]['nombre'] if result else 0
        except Exception as e:
            print(f"Erreur KPI automobile: {e}")
            kpis['total_vehicules'] = 0
            kpis['vehicules_assures'] = 0
            kpis['vehicules_non_assures'] = 0
        
        # Personnel
        try:
            result = self.db.executer_requete("""
                SELECT COUNT(*) as nombre 
                FROM employes 
                WHERE statut = 'ACTIF'
            """)
            kpis['effectif_total'] = result[0]['nombre'] if result else 0
            
            result = self.db.executer_requete("""
                SELECT COUNT(*) as nombre 
                FROM conges_absences 
                WHERE statut = 'EN_ATTENTE'
            """)
            kpis['conges_en_attente'] = result[0]['nombre'] if result else 0
        except Exception as e:
            print(f"Erreur KPI personnel: {e}")
            kpis['effectif_total'] = 0
            kpis['conges_en_attente'] = 0
        
        # Alertes critiques
        kpis['alertes_critiques'] = (
            kpis.get('materiel_en_panne', 0) +
            kpis.get('vehicules_non_assures', 0) +
            kpis.get('conges_en_attente', 0)
        )
        
        return kpis
    
    def obtenir_rapport_complet(self) -> Dict[str, Any]:
        """Génère un rapport complet de tous les modules"""
        rapport = {
            'date_generation': datetime.now(),
            'type': 'Rapport général CNTSCI',
            'sections': {}
        }
        
        # Section Matériel
        from modules.materiel.gestion_materiel import GestionnaireMateriel
        gestionnaire_materiel = GestionnaireMateriel()
        rapport['sections']['materiel'] = {
            'statistiques': gestionnaire_materiel.obtenir_statistiques(),
            'alertes_garantie': gestionnaire_materiel.obtenir_alertes_garantie(),
        }
        
        # Section Automobile
        from modules.automobile.gestion_automobile import GestionnaireAutomobile
        gestionnaire_auto = GestionnaireAutomobile()
        rapport['sections']['automobile'] = {
            'statistiques': gestionnaire_auto.obtenir_statistiques(),
            'alertes_assurance': gestionnaire_auto.obtenir_alertes_assurance(),
        }
        
        # Section Personnel
        from modules.personnel.gestion_personnel import GestionnairePersonnel, ReportingRH
        gestionnaire_rh = GestionnairePersonnel()
        reporting_rh = ReportingRH()
        rapport['sections']['personnel'] = {
            'statistiques': gestionnaire_rh.obtenir_statistiques(),
            'rapport_conges': reporting_rh.generer_rapport_conges(),
        }
        
        return rapport


class ExportManager:
    """Gestionnaire des exports de données"""
    
    def __init__(self):
        self.storage_path = STORAGE_PATHS['exports']
    
    def exporter_csv(self, donnees: List[Dict[str, Any]], nom_fichier: str,
                    separateur: str = ',') -> Optional[str]:
        """
        Exporte des données au format CSV
        Retourne le chemin du fichier créé ou None en cas d'échec
        """
        if not donnees:
            print("Aucune donnée à exporter")
            return None
        
        try:
            chemin_complet = self.storage_path / f"{nom_fichier}.csv"
            
            with open(chemin_complet, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=donnees[0].keys(), delimiter=separateur)
                writer.writeheader()
                writer.writerows(donnees)
            
            print(f"Export CSV réussi: {chemin_complet}")
            return str(chemin_complet)
        except Exception as e:
            print(f"Erreur export CSV: {e}")
            return None
    
    def exporter_json(self, donnees: Any, nom_fichier: str, 
                     indent: int = 2) -> Optional[str]:
        """
        Exporte des données au format JSON
        Retourne le chemin du fichier créé ou None en cas d'échec
        """
        try:
            chemin_complet = self.storage_path / f"{nom_fichier}.json"
            
            with open(chemin_complet, 'w', encoding='utf-8') as f:
                json.dump(donnees, f, indent=indent, default=str, ensure_ascii=False)
            
            print(f"Export JSON réussi: {chemin_complet}")
            return str(chemin_complet)
        except Exception as e:
            print(f"Erreur export JSON: {e}")
            return None
    
    def exporter_excel_simple(self, donnees: List[Dict[str, Any]], 
                             nom_fichier: str) -> Optional[str]:
        """
        Exporte des données au format Excel (version simplifiée sans dépendance)
        En production, utiliser openpyxl ou xlsxwriter
        Retourne le chemin du fichier créé ou None en cas d'échec
        """
        # Version simplifiée : export CSV avec extension .xlsx
        # Pour un vrai Excel, installer: pip install openpyxl
        try:
            chemin_complet = self.storage_path / f"{nom_fichier}.xlsx"
            
            # Format texte compatible Excel
            with open(chemin_complet, 'w', encoding='utf-8') as f:
                # En-têtes
                if donnees:
                    en_tetes = list(donnees[0].keys())
                    f.write('\t'.join(en_tetes) + '\n')
                    
                    # Données
                    for ligne in donnees:
                        valeurs = [str(ligne.get(col, '')) for col in en_tetes]
                        f.write('\t'.join(valeurs) + '\n')
            
            print(f"Export Excel (simplifié) réussi: {chemin_complet}")
            return str(chemin_complet)
        except Exception as e:
            print(f"Erreur export Excel: {e}")
            return None
    
    def exporter_toutes_donnees(self, utilisateur: Utilisateur) -> Dict[str, str]:
        """
        Exporte toutes les données de l'application
        Retourne un dictionnaire avec les chemins des fichiers créés
        """
        resultats = {}
        
        # Export matériel
        from modules.materiel.gestion_materiel import GestionnaireMateriel
        gestionnaire_materiel = GestionnaireMateriel()
        materiel_data = gestionnaire_materiel.obtenir_tout_materiel()
        
        if materiel_data:
            chemin = self.exporter_csv(materiel_data, 'inventaire_materiel')
            if chemin:
                resultats['materiel_csv'] = chemin
        
        # Export véhicules
        from modules.automobile.gestion_automobile import GestionnaireAutomobile
        gestionnaire_auto = GestionnaireAutomobile()
        vehicules_data = gestionnaire_auto.obtenir_tout_vehicule()
        
        if vehicules_data:
            chemin = self.exporter_csv(vehicules_data, 'parc_automobile')
            if chemin:
                resultats['automobile_csv'] = chemin
        
        # Export employés
        from modules.personnel.gestion_personnel import GestionnairePersonnel
        gestionnaire_rh = GestionnairePersonnel()
        employes_data = gestionnaire_rh.obtenir_tout_employe()
        
        if employes_data:
            chemin = self.exporter_csv(employes_data, 'personnel_rh')
            if chemin:
                resultats['personnel_csv'] = chemin
        
        # Export rapport complet en JSON
        reporting = ReportingManager()
        rapport = reporting.obtenir_rapport_complet()
        chemin = self.exporter_json(rapport, 'rapport_complet')
        if chemin:
            resultats['rapport_json'] = chemin
        
        # Enregistrer l'audit
        security_manager.enregistrer_audit(
            utilisateur, AuditAction.EXPORT,
            f"Export multiple: {len(resultats)} fichiers créés"
        )
        
        return resultats


class TableauDeBord:
    """Générateur de tableaux de bord"""
    
    def __init__(self):
        self.reporting = ReportingManager()
    
    def generer_vue_ensemble(self) -> Dict[str, Any]:
        """Génère une vue d'ensemble pour la direction"""
        kpis = self.reporting.obtenir_kpi_generaux()
        
        vue = {
            'titre': 'Tableau de Bord - Vue Direction',
            'date': datetime.now(),
            'indicateurs': kpis,
            'synthese': {
                'patrimoine_total': kpis.get('total_materiel', 0) + kpis.get('total_vehicules', 0),
                'taux_couverture_assurance': 0,
                'taux_panne_materiel': 0,
            }
        }
        
        # Calcul des taux
        if kpis.get('total_vehicules', 0) > 0:
            vue['synthese']['taux_couverture_assurance'] = round(
                (kpis.get('vehicules_assures', 0) / kpis['total_vehicules']) * 100, 2
            )
        
        if kpis.get('total_materiel', 0) > 0:
            vue['synthese']['taux_panne_materiel'] = round(
                (kpis.get('materiel_en_panne', 0) / kpis['total_materiel']) * 100, 2
            )
        
        return vue
    
    def generer_vue_rh(self) -> Dict[str, Any]:
        """Génère une vue dédiée aux RH"""
        from modules.personnel.gestion_personnel import GestionnairePersonnel, ReportingRH
        
        gestionnaire = GestionnairePersonnel()
        reporting = ReportingRH()
        
        stats = gestionnaire.obtenir_statistiques()
        rapport_conges = reporting.generer_rapport_conges()
        
        vue = {
            'titre': 'Tableau de Bord - Ressources Humaines',
            'date': datetime.now(),
            'effectif': stats.get('effectif_total', 0),
            'repartition': {
                'par_departement': stats.get('par_departement', []),
                'par_contrat': stats.get('par_contrat', []),
                'par_statut': stats.get('par_statut', []),
            },
            'conges': {
                'rapport': rapport_conges.get('donnees', []),
                'en_attente': len(CongesAbsence.obtenir_demandes_en_attente()) if 'CongesAbsence' in globals() else 0,
            },
            'indicateurs': {
                'anciennete_moyenne': stats.get('anciennete_moyenne', 0),
                'turnover_annee': stats.get('turnover_annee', 0),
            }
        }
        
        return vue
    
    def generer_vue_materiel(self) -> Dict[str, Any]:
        """Génère une vue dédiée au matériel informatique"""
        from modules.materiel.gestion_materiel import GestionnaireMateriel
        
        gestionnaire = GestionnaireMateriel()
        stats = gestionnaire.obtenir_statistiques()
        alertes = gestionnaire.obtenir_alertes_garantie()
        
        vue = {
            'titre': 'Tableau de Bord - Matériel Informatique',
            'date': datetime.now(),
            'total': stats.get('sous_garantie', 0) + stats.get('a_maintenir', 0),
            'repartition': {
                'par_etat': stats.get('par_etat', []),
                'par_type': stats.get('par_type', []),
            },
            'alertes': {
                'garanties_expirant_bientot': len(alertes),
                'details_alertes': alertes[:5],  # Top 5 alertes
            },
            'maintenance': {
                'a_maintenir': stats.get('a_maintenir', 0),
            }
        }
        
        return vue
    
    def generer_vue_automobile(self) -> Dict[str, Any]:
        """Génère une vue dédiée au parc automobile"""
        from modules.automobile.gestion_automobile import GestionnaireAutomobile
        
        gestionnaire = GestionnaireAutomobile()
        stats = gestionnaire.obtenir_statistiques()
        alertes = gestionnaire.obtenir_alertes_assurance()
        non_assures = gestionnaire.obtenir_vehicules_non_assures()
        
        vue = {
            'titre': 'Tableau de Bord - Parc Automobile',
            'date': datetime.now(),
            'total_vehicules': stats.get('assures', 0) + stats.get('non_assures', 0),
            'repartition': {
                'par_etat': stats.get('par_etat', []),
                'par_type': stats.get('par_type', []),
            },
            'assurances': {
                'assures': stats.get('assures', 0),
                'non_assures': stats.get('non_assures', 0),
                'expirant_bientot': len(alertes),
                'details_non_assures': non_assures,
            },
            'kilometrage_moyen': stats.get('km_moyen', 0),
        }
        
        return vue


# Import nécessaire pour éviter les références circulaires
def _import_conges():
    from modules.personnel.gestion_personnel import CongesAbsence
    return CongesAbsence


# Patch de la référence dans TableauDeBord
TableauDeBord._import_conges = staticmethod(_import_conges)
