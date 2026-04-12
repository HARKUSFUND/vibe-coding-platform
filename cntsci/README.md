# CNTSCI - Application de Gestion

## Centre National de Transfusion Sanguine de Côte d'Ivoire

**Développé par M. SESS Eddy 2025**  
**Version:** 1.0.0 - Phase V1

---

## 📋 Description

Application bureau centralisée pour la gestion du:
- **Matériel informatique** (inventaire, maintenance, garanties)
- **Parc automobile** (véhicules, assurances, maintenances)
- **Personnel** (dossiers RH, congés/absences, reporting)

---

## 🚀 Installation

### Prérequis
- Python 3.8 ou supérieur
- PostgreSQL 12+ (pour la base de données)
- PyQt5 (optionnel, pour l'interface graphique)

### Installation des dépendances

```bash
# Dépendances principales
pip install psycopg2-binary

# Interface graphique (optionnel)
pip install PyQt5

# Pour les exports Excel avancés (V2)
pip install openpyxl xlsxwriter

# Pour les rapports PDF (V2)
pip install reportlab
```

### Configuration de la base de données

1. Créez une base de données PostgreSQL:
```sql
CREATE DATABASE cntsci_db;
CREATE USER cntsci_user WITH PASSWORD 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON DATABASE cntsci_db TO cntsci_user;
```

2. Configurez les variables d'environnement:
```bash
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=cntsci_db
export DB_USER=cntsci_user
export DB_PASSWORD=votre_mot_de_passe
export SECRET_KEY=votre_cle_secrete_production
```

---

## 💻 Utilisation

### Lancer l'application

```bash
cd cntsci_app
python main.py
```

### Menu principal

1. **Interface graphique** - Lance l'application PyQt
2. **Mode console** - Tests des fonctionnalités backend
3. **Initialiser la base de données** - Crée les tables nécessaires
4. **Quitter**

---

## 📁 Structure du projet

```
cntsci_app/
├── __init__.py              # Package initialization
├── main.py                  # Point d'entrée principal
├── core/                    # Modules centraux
│   ├── config.py           # Configuration globale
│   ├── security.py         # Sécurité et authentification
│   └── database.py         # Gestion de la base de données
├── modules/                 # Modules métier
│   ├── materiel/           # Gestion du matériel informatique
│   │   └── gestion_materiel.py
│   ├── automobile/         # Gestion du parc automobile
│   │   └── gestion_automobile.py
│   ├── personnel/          # Gestion des ressources humaines
│   │   └── gestion_personnel.py
│   └── reporting/          # Reporting et tableaux de bord
│       └── reporting.py
├── ui/                      # Interface utilisateur
│   └── application.py      # Interface PyQt
├── utils/                   # Utilitaires
└── data/                    # Données et exports
    ├── exports/
    ├── logs/
    ├── backups/
    └── documents/
```

---

## 🔐 Sécurité

- Authentification forte avec hachage des mots de passe
- Gestion des rôles et permissions (DG, DRH, Admin, etc.)
- Journal d'audit complet pour traçabilité
- Cryptage des données sensibles
- Verrouillage des comptes après échecs multiples

---

## 📊 Fonctionnalités V1

### Matériel Informatique
- ✅ Inventaire complet
- ✅ Suivi des maintenances
- ✅ Alertes garanties
- ✅ Statistiques par état/type

### Parc Automobile
- ✅ Gestion des véhicules
- ✅ Suivi des assurances
- ✅ Planification maintenances
- ✅ Alertes expiration

### Personnel
- ✅ Dossiers employés complets
- ✅ Gestion des congés/absences
- ✅ Validation hiérarchique
- ✅ Rapports RH (effectifs, turnover)

### Reporting
- ✅ Tableaux de bord multi-vues
- ✅ KPIs en temps réel
- ✅ Exports CSV/JSON
- ✅ Rapports personnalisés

---

## 🔄 Roadmap

### Phase 2 (V2)
- [ ] Licences logicielles
- [ ] Alertes automatiques avancées
- [ ] Consommation carburant détaillée
- [ ] Formations et évaluations
- [ ] Audits de sécurité
- [ ] Exports Excel/PDF natifs

### Phase 3 (V3)
- [ ] Localisation GPS véhicules
- [ ] Personnalisation des exports
- [ ] Optimisations graphiques
- [ ] Mobile companion app

---

## 🛠️ Développement

### Ajouter un nouveau module

1. Créer le dossier dans `modules/`
2. Implémenter les classes métier
3. Ajouter les tables dans `core/database.py`
4. Intégrer dans l'interface `ui/application.py`

### Bonnes pratiques

- Noms de variables et fonctions explicites (en français)
- Commentaires détaillés
- Gestion propre des exceptions
- Respect des normes de confidentialité

---

## 📞 Support

Pour toute question ou assistance:
- Email: support@cntsci.ci
- Documentation complète disponible dans `/docs`

---

## ©️ Licence

**Genie Logiciel CNTSCI - Développé par M. SESS Eddy 2025**

Tous droits réservés. Usage interne CNTSCI uniquement.
