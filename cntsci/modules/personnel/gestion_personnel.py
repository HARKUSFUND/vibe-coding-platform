"""
Module de gestion du personnel RH
Gère les dossiers employés, congés/absences et suivi RH
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from core.database import db_manager
from core.security import security_manager, AuditAction, Utilisateur


class TypeConge(Enum):
    """Types de congés"""
    ANNUAL = "Congés annuels"
    MALADIE = "Congé maladie"
    MATERNITE = "Congé maternité"
    PATERNITE = "Congé paternité"
    SANS_SOLDE = "Congé sans solde"
    FORMATION = "Formation"
    AUTRE = "Autre"


class StatutConge(Enum):
    """Statuts des demandes de congés"""
    EN_ATTENTE = "En attente"
    APPROUVE = "Approuvé"
    REFUSE = "Refusé"
    ANNULE = "Annulé"


@dataclass
class Employe:
    """Représente un employé du CNTSCI"""
    id: Optional[int] = None
    matricule: str = ""
    nom: str = ""
    prenom: str = ""
    date_naissance: Optional[date] = None
    lieu_naissance: str = ""
    nationalite: str = ""
    adresse: str = ""
    telephone: str = ""
    email: str = ""
    poste: str = ""
    departement: str = ""
    date_embauche: Optional[date] = None
    type_contrat: str = ""
    salaire: float = 0.0
    statut: str = "ACTIF"
    utilisateur_id: Optional[int] = None
    notes: str = ""
    
    def age(self) -> int:
        """Calcule l'âge de l'employé"""
        if not self.date_naissance:
            return 0
        today = date.today()
        age = today.year - self.date_naissance.year
        if (today.month, today.day) < (self.date_naissance.month, self.date_naissance.day):
            age -= 1
        return age
    
    def anciennete_annees(self) -> float:
        """Calcule l'ancienneté en années"""
        if not self.date_embauche:
            return 0.0
        delta = date.today() - self.date_embauche
        return round(delta.days / 365.25, 2)
    
    def est_actif(self) -> bool:
        """Vérifie si l'employé est actif"""
        return self.statut == "ACTIF"


class GestionnairePersonnel:
    """Gestionnaire des opérations sur le personnel"""
    
    def __init__(self):
        self.db = db_manager
    
    def ajouter_employe(self, employe: Employe, utilisateur: Utilisateur) -> Optional[int]:
        """
        Ajoute un nouvel employé
        Retourne l'ID de l'employé créé ou None en cas d'échec
        """
        query = """
        INSERT INTO employes
        (matricule, nom, prenom, date_naissance, lieu_naissance,
         nationalite, adresse, telephone, email, poste, departement,
         date_embauche, type_contrat, salaire, statut, utilisateur_id, notes)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            employe.matricule,
            employe.nom,
            employe.prenom,
            employe.date_naissance,
            employe.lieu_naissance,
            employe.nationalite,
            employe.adresse,
            employe.telephone,
            employe.email,
            employe.poste,
            employe.departement,
            employe.date_embauche,
            employe.type_contrat,
            employe.salaire,
            employe.statut,
            employe.utilisateur_id,
            employe.notes,
        )
        
        try:
            result = self.db.executer_requete(query, params, fetch=True, commit=True)
            if result:
                employe.id = result[0]['id']
                security_manager.enregistrer_audit(
                    utilisateur, AuditAction.CREATE,
                    f"Ajout employé: {employe.matricule} - {employe.nom} {employe.prenom}"
                )
                return employe.id
        except Exception as e:
            print(f"Erreur ajout employé: {e}")
        
        return None
    
    def obtenir_tout_employe(self) -> List[Dict[str, Any]]:
        """Retourne la liste complète des employés"""
        query = "SELECT * FROM employes ORDER BY nom, prenom"
        return self.db.executer_requete(query) or []
    
    def obtenir_employe_par_id(self, employe_id: int) -> Optional[Dict[str, Any]]:
        """Retourne un employé par son ID"""
        query = "SELECT * FROM employes WHERE id = %s"
        results = self.db.executer_requete(query, (employe_id,))
        return results[0] if results else None
    
    def obtenir_employe_par_matricule(self, matricule: str) -> Optional[Dict[str, Any]]:
        """Retourne un employé par son matricule"""
        query = "SELECT * FROM employes WHERE matricule = %s"
        results = self.db.executer_requete(query, (matricule,))
        return results[0] if results else None
    
    def mettre_a_jour_employe(self, employe: Employe, utilisateur: Utilisateur) -> bool:
        """Met à jour les informations d'un employé"""
        query = """
        UPDATE employes
        SET nom = %s, prenom = %s, date_naissance = %s, lieu_naissance = %s,
            nationalite = %s, adresse = %s, telephone = %s, email = %s,
            poste = %s, departement = %s, date_embauche = %s, type_contrat = %s,
            salaire = %s, statut = %s, utilisateur_id = %s, notes = %s
        WHERE id = %s
        """
        
        params = (
            employe.nom,
            employe.prenom,
            employe.date_naissance,
            employe.lieu_naissance,
            employe.nationalite,
            employe.adresse,
            employe.telephone,
            employe.email,
            employe.poste,
            employe.departement,
            employe.date_embauche,
            employe.type_contrat,
            employe.salaire,
            employe.statut,
            employe.utilisateur_id,
            employe.notes,
            employe.id,
        )
        
        try:
            self.db.executer_requete(query, params, fetch=False, commit=True)
            security_manager.enregistrer_audit(
                utilisateur, AuditAction.UPDATE,
                f"Mise à jour employé: {employe.matricule}"
            )
            return True
        except Exception as e:
            print(f"Erreur mise à jour employé: {e}")
            return False
    
    def supprimer_employe(self, employe_id: int, utilisateur: Utilisateur) -> bool:
        """Supprime un employé (soft delete recommandé)"""
        # En production, préférer un soft delete
        query = "DELETE FROM employes WHERE id = %s"
        
        try:
            self.db.executer_requete(query, (employe_id,), fetch=False, commit=True)
            security_manager.enregistrer_audit(
                utilisateur, AuditAction.DELETE,
                f"Suppression employé ID: {employe_id}"
            )
            return True
        except Exception as e:
            print(f"Erreur suppression employé: {e}")
            return False
    
    def rechercher_employe(self, terme: str) -> List[Dict[str, Any]]:
        """Recherche des employés par nom, prénom, matricule ou poste"""
        query = """
        SELECT * FROM employes
        WHERE nom ILIKE %s OR prenom ILIKE %s 
           OR matricule ILIKE %s OR poste ILIKE %s
        ORDER BY nom, prenom
        """
        search_term = f"%{terme}%"
        return self.db.executer_requete(query, (search_term, search_term, search_term, search_term)) or []
    
    def obtenir_statistiques(self) -> Dict[str, Any]:
        """Retourne des statistiques sur le personnel"""
        stats = {}
        
        # Nombre total par statut
        query_statut = """
        SELECT statut, COUNT(*) as nombre
        FROM employes
        GROUP BY statut
        """
        stats['par_statut'] = self.db.executer_requete(query_statut) or []
        
        # Nombre total par département
        query_departement = """
        SELECT departement, COUNT(*) as nombre
        FROM employes
        GROUP BY departement
        ORDER BY nombre DESC
        """
        stats['par_departement'] = self.db.executer_requete(query_departement) or []
        
        # Nombre total par type de contrat
        query_contrat = """
        SELECT type_contrat, COUNT(*) as nombre
        FROM employes
        GROUP BY type_contrat
        """
        stats['par_contrat'] = self.db.executer_requete(query_contrat) or []
        
        # Effectif total
        query_total = """
        SELECT COUNT(*) as nombre
        FROM employes
        WHERE statut = 'ACTIF'
        """
        result = self.db.executer_requete(query_total)
        stats['effectif_total'] = result[0]['nombre'] if result else 0
        
        # Ancienneté moyenne
        query_anciennete = """
        SELECT AVG(EXTRACT(EPOCH FROM (CURRENT_DATE - date_embauche)) / 365.25) as moyenne
        FROM employes
        WHERE statut = 'ACTIF' AND date_embauche IS NOT NULL
        """
        result = self.db.executer_requete(query_anciennete)
        stats['anciennete_moyenne'] = round(result[0]['moyenne'], 2) if result and result[0]['moyenne'] else 0
        
        # Turnover (emplois quittés cette année)
        query_turnover = """
        SELECT COUNT(*) as nombre
        FROM employes
        WHERE statut != 'ACTIF'
          AND EXTRACT(YEAR FROM date_creation) = EXTRACT(YEAR FROM CURRENT_DATE)
        """
        result = self.db.executer_requete(query_turnover)
        stats['turnover_annee'] = result[0]['nombre'] if result else 0
        
        return stats
    
    def obtenir_anniversaires_mois(self, mois: int = None) -> List[Dict[str, Any]]:
        """Retourne les employés ayant un anniversaire ce mois-ci"""
        if mois is None:
            mois = date.today().month
        
        query = """
        SELECT * FROM employes
        WHERE EXTRACT(MONTH FROM date_naissance) = %s
        ORDER BY EXTRACT(DAY FROM date_naissance)
        """
        return self.db.executer_requete(query, (mois,)) or []


@dataclass
class CongesAbsence:
    """Représente une demande de congé ou absence"""
    id: Optional[int] = None
    employe_id: int = 0
    type_conge: str = ""
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    nombre_jours: int = 0
    motif: str = ""
    statut: str = "EN_ATTENTE"
    date_demande: Optional[datetime] = None
    valide_par: Optional[int] = None
    commentaires: str = ""
    
    def calculer_nombre_jours(self) -> int:
        """Calcule le nombre de jours ouvrés entre deux dates"""
        if not self.date_debut or not self.date_fin:
            return 0
        
        delta = self.date_fin - self.date_debut
        jours_total = delta.days + 1
        
        # Soustraire les week-ends (simplifié)
        weekends = 0
        current_date = self.date_debut
        while current_date <= self.date_fin:
            if current_date.weekday() >= 5:  # Samedi ou Dimanche
                weekends += 1
            current_date += timedelta(days=1)
        
        return max(0, jours_total - weekends)
    
    def soumettre_demande(self, utilisateur: Utilisateur) -> Optional[int]:
        """Soumet une demande de congé"""
        self.nombre_jours = self.calculer_nombre_jours()
        self.date_demande = datetime.now()
        
        query = """
        INSERT INTO conges_absences
        (employe_id, type_conge, date_debut, date_fin, nombre_jours,
         motif, statut, commentaires)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
        """
        
        params = (
            self.employe_id,
            self.type_conge,
            self.date_debut,
            self.date_fin,
            self.nombre_jours,
            self.motif,
            self.statut,
            self.commentaires,
        )
        
        try:
            result = db_manager.executer_requete(query, params, fetch=True, commit=True)
            if result:
                self.id = result[0]['id']
                security_manager.enregistrer_audit(
                    utilisateur, AuditAction.CREATE,
                    f"Demande congé employé ID: {self.employe_id} - {self.type_conge}"
                )
                return self.id
        except Exception as e:
            print(f"Erreur soumission demande congé: {e}")
        
        return None
    
    def valider_demande(self, validateur: Utilisateur, approuve: bool, 
                       commentaires: str = "") -> bool:
        """Valide ou refuse une demande de congé"""
        nouveau_statut = "APPROUVE" if approuve else "REFUSE"
        
        query = """
        UPDATE conges_absences
        SET statut = %s, date_validation = %s, valide_par = %s, commentaires = %s
        WHERE id = %s
        """
        
        params = (
            nouveau_statut,
            datetime.now(),
            validateur.id,
            commentaires,
            self.id,
        )
        
        try:
            db_manager.executer_requete(query, params, fetch=False, commit=True)
            self.statut = nouveau_statut
            self.valide_par = validateur.id
            self.commentaires = commentaires
            
            action = AuditAction.APPROUVE if approuve else AuditAction.DELETE
            security_manager.enregistrer_audit(
                validateur, action,
                f"Validation congé ID: {self.id} - {'Approuvé' if approuve else 'Refusé'}"
            )
            return True
        except Exception as e:
            print(f"Erreur validation demande congé: {e}")
            return False
    
    @staticmethod
    def obtenir_demandes_employe(employe_id: int) -> List[Dict[str, Any]]:
        """Retourne l'historique des demandes de congés d'un employé"""
        query = """
        SELECT * FROM conges_absences
        WHERE employe_id = %s
        ORDER BY date_demande DESC
        """
        return db_manager.executer_requete(query, (employe_id,)) or []
    
    @staticmethod
    def obtenir_demandes_en_attente() -> List[Dict[str, Any]]:
        """Retourne toutes les demandes en attente de validation"""
        query = """
        SELECT c.*, e.nom, e.prenom, e.matricule
        FROM conges_absences c
        JOIN employes e ON c.employe_id = e.id
        WHERE c.statut = 'EN_ATTENTE'
        ORDER BY c.date_demande
        """
        return db_manager.executer_requete(query) or []
    
    @staticmethod
    def obtenir_solde_conges(employe_id: int, annee: int = None) -> Dict[str, Any]:
        """Calcule le solde de congés annuels d'un employé"""
        if annee is None:
            annee = date.today().year
        
        # Total des congés acquis (à adapter selon la politique RH)
        conges_acquis = 30  # Exemple: 30 jours par an
        
        query = """
        SELECT COALESCE(SUM(nombre_jours), 0) as total_pris
        FROM conges_absences
        WHERE employe_id = %s
          AND statut = 'APPROUVE'
          AND type_conge = 'Congés annuels'
          AND EXTRACT(YEAR FROM date_debut) = %s
        """
        result = db_manager.executer_requete(query, (employe_id, annee))
        total_pris = result[0]['total_pris'] if result else 0
        
        return {
            'annee': annee,
            'acquis': conges_acquis,
            'pris': total_pris,
            'reste': conges_acquis - total_pris,
        }


class ReportingRH:
    """Génération de rapports RH"""
    
    def __init__(self):
        self.db = db_manager
    
    def generer_rapport_effectifs(self) -> Dict[str, Any]:
        """Génère un rapport complet des effectifs"""
        gestionnaire = GestionnairePersonnel()
        stats = gestionnaire.obtenir_statistiques()
        
        rapport = {
            'date_generation': datetime.now(),
            'type': 'Rapport des effectifs',
            'donnees': stats,
            'synthese': {
                'effectif_total': stats.get('effectif_total', 0),
                'departements': len(stats.get('par_departement', [])),
                'types_contrats': len(stats.get('par_contrat', [])),
            }
        }
        
        return rapport
    
    def generer_rapport_conges(self, annee: int = None) -> Dict[str, Any]:
        """Génère un rapport sur les congés"""
        if annee is None:
            annee = date.today().year
        
        query = """
        SELECT 
            type_conge,
            statut,
            COUNT(*) as nombre,
            SUM(nombre_jours) as total_jours
        FROM conges_absences
        WHERE EXTRACT(YEAR FROM date_debut) = %s
        GROUP BY type_conge, statut
        ORDER BY type_conge, statut
        """
        
        result = self.db.executer_requete(query, (annee,))
        
        rapport = {
            'date_generation': datetime.now(),
            'type': 'Rapport des congés',
            'annee': annee,
            'donnees': result or [],
        }
        
        return rapport
    
    def generer_rapport_turnover(self, annee: int = None) -> Dict[str, Any]:
        """Génère un rapport sur le turnover"""
        if annee is None:
            annee = date.today().year
        
        # Employés ayant quitté cette année
        query_departs = """
        SELECT * FROM employes
        WHERE statut != 'ACTIF'
          AND EXTRACT(YEAR FROM date_creation) = %s
        """
        departs = self.db.executer_requete(query_departs, (annee,))
        
        # Total employés en début d'année
        query_total = """
        SELECT COUNT(*) as nombre
        FROM employes
        WHERE EXTRACT(YEAR FROM date_embauche) < %s
        """
        result = self.db.executer_requete(query_total, (annee,))
        total_debut = result[0]['nombre'] if result else 0
        
        turnover_rate = 0.0
        if total_debut > 0:
            turnover_rate = round((len(departs) / total_debut) * 100, 2)
        
        rapport = {
            'date_generation': datetime.now(),
            'type': 'Rapport de turnover',
            'annee': annee,
            'depars': len(departs),
            'effectif_debut_annee': total_debut,
            'taux_turnover': f"{turnover_rate}%",
        }
        
        return rapport
