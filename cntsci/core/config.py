"""
Configuration centrale de l'application CNTSCI
Gère les paramètres globaux, chemins et constantes
"""

import os
from pathlib import Path
from datetime import timedelta

# Chemin de base de l'application
BASE_DIR = Path(__file__).resolve().parent.parent

# Configuration de la base de données
DATABASE_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5432)),
    'database': os.getenv('DB_NAME', 'cntsci_db'),
    'user': os.getenv('DB_USER', 'cntsci_user'),
    'password': os.getenv('DB_PASSWORD', ''),
}

# Configuration de sécurité
SECURITY_CONFIG = {
    'secret_key': os.getenv('SECRET_KEY', 'cntsci-secret-key-change-in-production'),
    'algorithm': 'HS256',
    'access_token_expire_minutes': 30,
    'refresh_token_expire_days': 7,
    'password_min_length': 8,
    'max_login_attempts': 5,
    'lockout_duration': timedelta(minutes=15),
}

# Rôles utilisateurs
ROLES = {
    'DG': {
        'nom': 'Directeur Général',
        'permissions': ['read_all', 'write_all', 'delete_all', 'export_all', 'admin'],
        'niveau': 1
    },
    'DRH': {
        'nom': 'Directeur RH',
        'permissions': ['read_rh', 'write_rh', 'read_materiel', 'read_automobile', 'export_rh'],
        'niveau': 2
    },
    'ADMIN': {
        'nom': 'Administrateur Système',
        'permissions': ['read_all', 'write_all', 'admin'],
        'niveau': 2
    },
    'GESTIONNAIRE_MATERIEL': {
        'nom': 'Gestionnaire Matériel',
        'permissions': ['read_materiel', 'write_materiel'],
        'niveau': 3
    },
    'GESTIONNAIRE_AUTOMOBILE': {
        'nom': 'Gestionnaire Parc Automobile',
        'permissions': ['read_automobile', 'write_automobile'],
        'niveau': 3
    },
    'EMPLOYE': {
        'nom': 'Employé',
        'permissions': ['read_own', 'write_own'],
        'niveau': 4
    }
}

# Configuration des exports
EXPORT_CONFIG = {
    'formats': ['xlsx', 'csv', 'pdf'],
    'default_format': 'xlsx',
    'max_rows_per_file': 100000,
}

# Configuration des alertes
ALERT_CONFIG = {
    'expiration_assurance_jours': 30,
    'expiration_garantie_jours': 60,
    'maintenance_vehicle_km_seuil': 5000,
    'maintenance_vehicle_mois_seuil': 6,
}

# Chemins de stockage
STORAGE_PATHS = {
    'exports': BASE_DIR / 'data' / 'exports',
    'logs': BASE_DIR / 'data' / 'logs',
    'backups': BASE_DIR / 'data' / 'backups',
    'documents': BASE_DIR / 'data' / 'documents',
}

# S'assurer que les dossiers existent
for path in STORAGE_PATHS.values():
    path.mkdir(parents=True, exist_ok=True)

# Configuration de l'interface
UI_CONFIG = {
    'langue': 'fr',
    'theme': 'light',
    'fenetre_largeur': 1400,
    'fenetre_hauteur': 900,
    'police_principale': 'Arial',
    'taille_police': 10,
}

# Version de l'application
APP_VERSION = "1.0.0"
APP_PHASE = "V1"
