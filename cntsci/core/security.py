"""
Module de sécurité pour l'application CNTSCI
Gère l'authentification, l'autorisation et le cryptage des données
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from core.config import SECURITY_CONFIG, ROLES


class AuditAction(Enum):
    """Actions auditées pour la traçabilité"""
    LOGIN = "CONNEXION"
    LOGOUT = "DECONNEXION"
    CREATE = "CREATION"
    READ = "LECTURE"
    UPDATE = "MODIFICATION"
    DELETE = "SUPPRESSION"
    EXPORT = "EXPORTATION"
    FAILED_LOGIN = "ECHEC_CONNEXION"
    PERMISSION_DENIED = "ACCES_REFUSE"


@dataclass
class Utilisateur:
    """Représente un utilisateur du système"""
    id: int
    username: str
    email: str
    role: str
    nom_complet: str
    est_actif: bool = True
    date_creation: datetime = field(default_factory=datetime.now)
    derniere_connexion: Optional[datetime] = None
    tentatives_echec: int = 0
    verrouille_jusqu_a: Optional[datetime] = None
    
    def has_permission(self, permission: str) -> bool:
        """Vérifie si l'utilisateur a une permission donnée"""
        if self.role not in ROLES:
            return False
        return permission in ROLES[self.role]['permissions']
    
    def get_role_niveau(self) -> int:
        """Retourne le niveau hiérarchique du rôle"""
        if self.role not in ROLES:
            return 99
        return ROLES[self.role]['niveau']


class SecurityManager:
    """Gestionnaire de sécurité centralisé"""
    
    def __init__(self):
        self.secret_key = SECURITY_CONFIG['secret_key']
        self.utilisateurs_connectes: Dict[int, Utilisateur] = {}
        self.journal_audit: list = []
    
    @staticmethod
    def hasher_mot_de_passe(mot_de_passe: str) -> str:
        """
        Hache un mot de passe avec SHA-256 et un sel
        En production, utiliser bcrypt ou argon2
        """
        sel = secrets.token_hex(16)
        hash_value = hashlib.sha256((sel + mot_de_passe).encode()).hexdigest()
        return f"{sel}${hash_value}"
    
    @staticmethod
    def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
        """Vérifie si un mot de passe correspond au hash stocké"""
        try:
            sel, hash_value = hash_stocke.split('$')
            nouveau_hash = hashlib.sha256((sel + mot_de_passe).encode()).hexdigest()
            return nouveau_hash == hash_value
        except Exception:
            return False
    
    @staticmethod
    def valider_mot_de_passe(mot_de_passe: str) -> tuple[bool, str]:
        """
        Valide la force d'un mot de passe
        Retourne (est_valide, message_erreur)
        """
        min_length = SECURITY_CONFIG['password_min_length']
        
        if len(mot_de_passe) < min_length:
            return False, f"Le mot de passe doit contenir au moins {min_length} caractères"
        
        if not re.search(r'[A-Z]', mot_de_passe):
            return False, "Le mot de passe doit contenir au moins une majuscule"
        
        if not re.search(r'[a-z]', mot_de_passe):
            return False, "Le mot de passe doit contenir au moins une minuscule"
        
        if not re.search(r'\d', mot_de_passe):
            return False, "Le mot de passe doit contenir au moins un chiffre"
        
        return True, ""
    
    @staticmethod
    def generer_token_session() -> str:
        """Génère un token de session sécurisé"""
        return secrets.token_urlsafe(32)
    
    def enregistrer_audit(self, utilisateur: Utilisateur, action: AuditAction, 
                         details: str = "", succes: bool = True) -> None:
        """Enregistre une action dans le journal d'audit"""
        entree_audit = {
            'timestamp': datetime.now(),
            'utilisateur_id': utilisateur.id if utilisateur else None,
            'utilisateur_nom': utilisateur.nom_complet if utilisateur else "Inconnu",
            'action': action.value,
            'details': details,
            'succes': succes,
            'adresse_ip': "",  # À implémenter selon le contexte
        }
        self.journal_audit.append(entree_audit)
        
        # En production, écrire dans un fichier ou base de données
        print(f"[AUDIT] {entree_audit['timestamp']} - {entree_audit['utilisateur_nom']} - {entree_audit['action']} - {'OK' if succes else 'ECHEC'}")
    
    def verifier_verrouillage(self, utilisateur: Utilisateur) -> tuple[bool, str]:
        """Vérifie si un utilisateur est verrouillé"""
        if utilisateur.verrouille_jusqu_a and datetime.now() < utilisateur.verrouille_jusqu_a:
            temps_restant = utilisateur.verrouille_jusqu_a - datetime.now()
            minutes = int(temps_restant.total_seconds() / 60)
            return True, f"Compte verrouillé. Réessayez dans {minutes} minutes"
        return False, ""
    
    def enregistrer_echec_connexion(self, utilisateur: Utilisateur) -> None:
        """Enregistre un échec de connexion et verrouille si nécessaire"""
        utilisateur.tentatives_echec += 1
        
        if utilisateur.tentatives_echec >= SECURITY_CONFIG['max_login_attempts']:
            utilisateur.verrouille_jusqu_a = datetime.now() + SECURITY_CONFIG['lockout_duration']
            utilisateur.tentatives_echec = 0
    
    def reinitialiser_tentatives(self, utilisateur: Utilisateur) -> None:
        """Réinitialise les tentatives d'échec après une connexion réussie"""
        utilisateur.tentatives_echec = 0
        utilisateur.verrouille_jusqu_a = None
        utilisateur.derniere_connexion = datetime.now()
    
    @staticmethod
    def crypter_donnees_sensibles(donnees: str) -> str:
        """
        Crypte des données sensibles
        En production, utiliser Fernet ou un algorithme plus robuste
        """
        # Implémentation simplifiée - à renforcer en production
        cle = secrets.token_bytes(32)
        # Pour une vraie implémentation, utiliser cryptography.fernet
        return hashlib.sha256((donnees + secrets.token_hex(16)).encode()).hexdigest()
    
    def exporter_journal_audit(self, chemin_fichier: str) -> bool:
        """Exporte le journal d'audit vers un fichier"""
        try:
            with open(chemin_fichier, 'w', encoding='utf-8') as f:
                f.write("TIMESTAMP | UTILISATEUR | ACTION | DETAILS | STATUT\n")
                f.write("=" * 80 + "\n")
                for entree in self.journal_audit:
                    ligne = (f"{entree['timestamp']} | "
                           f"{entree['utilisateur_nom']} | "
                           f"{entree['action']} | "
                           f"{entree['details']} | "
                           f"{'SUCCES' if entree['succes'] else 'ECHEC'}\n")
                    f.write(ligne)
            return True
        except Exception as e:
            print(f"Erreur export audit: {e}")
            return False


# Instance globale du gestionnaire de sécurité
security_manager = SecurityManager()
