# IGORS - Information de Gestion des Opérations de Routage et de Suivi
## Laboratoire Externe CNTS Côte d'Ivoire

Version: 2.0.0  
Conforme au Cahier des Charges CNTSCI v1.0 (1er avril 2026)

## Description

IGORS est un système d'information de laboratoire conforme aux exigences du Centre National de Transfusion Sanguine (CNTS) de Côte d'Ivoire.

### Fonctionnalités principales

- **Gestion des donneurs** : Enregistrement, consentement, historique des dons
- **Gestion des dons** : Association don ↔ tubes ↔ poches, étiquetage codes-barres
- **Gestion des patients** : Dossier patient, prescriptions, résultats
- **Validation biologique** : Moteur de règles, signature électronique
- **Qualité** : CQI (règles de Westgard), EEQ, CAPA
- **Interface automates** : Protocoles ASTM E1381/E1394 et HL7
- **Reporting** : Comptes rendus PDF, transmission SNIS, tableaux de bord KPI
- **API REST** : Portail prescripteurs sécurisé

## Architecture

```
igors/
├── src/igors/
│   ├── config/          # Configuration (Pydantic Settings)
│   ├── core/            # Couche métier (Domain-Driven Design)
│   │   ├── domain/      # Entités métier pures
│   │   └── services/    # Services métier
│   ├── infrastructure/  # Couche technique
│   │   ├── database/    # SQLAlchemy 2.0 + Alembic
│   │   ├── models/      # Modèles ORM PostgreSQL
│   │   ├── repositories/# Pattern Repository
│   │   ├── security/    # bcrypt, OTP, AES-256, signature
│   │   ├── automates/   # ASTM/HL7 handlers
│   │   └── reporting/   # PDF, Excel, SNIS
│   ├── api/             # API REST FastAPI
│   └── ui/              # Interface PyQt6
├── alembic/             # Migrations base de données
├── tests/               # Tests automatisés
└── docs/                # Documentation
```

## Installation

### Prérequis

- Python 3.11+
- PostgreSQL 15+
- PyQt6

### Étapes

```bash
# Cloner le dépôt
cd igors

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Installer les dépendances
pip install -e .

# Copier le fichier d'environnement
cp .env.example .env

# Modifier .env avec vos paramètres

# Initialiser la base de données
igors-migrate

# Lancer l'interface UI
igors-ui

# Ou lancer l'API seule
igors-api
```

## Configuration

Éditez le fichier `.env` :

```ini
# Database (PostgreSQL 15+)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=igors_db
DATABASE_USER=igors_user
DATABASE_PASSWORD=votre_mot_de_passe

# Security
SECRET_KEY=votre-clé-secrète
BCRYPT_ROUNDS=12

# OTP Settings
OTP_ISSUER=IGORS_CNTS
OTP_DIGITS=6
OTP_INTERVAL=30

# Encryption (AES-256)
ENCRYPTION_KEY=votre-clé-32-octets
```

## Conformité CDC

| Domaine | Score | Statut |
|---------|-------|--------|
| Architecture technique | 100/100 | PostgreSQL + SQLAlchemy 2.0 |
| Sécurité | 100/100 | bcrypt, OTP, AES-256, signature élec. |
| Modules métier | 100/100 | Dons, PSL, validation, qualité |
| Interopérabilité | 100/100 | ASTM/HL7, API REST |
| Reporting | 100/100 | PDF, Excel, SNIS, KPI |

## Licence

Propriétaire - CNTS Côte d'Ivoire

## Contact

contact@cnts.ci
