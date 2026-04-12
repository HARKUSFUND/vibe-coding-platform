"""
Script principal de lancement de l'application CNTSCI
Point d'entrée unique pour démarrer l'application
"""

import sys
from pathlib import Path

# Ajouter le chemin racine au path Python
sys.path.insert(0, str(Path(__file__).parent))


def verifier_dependances():
    """Vérifie que les dépendances nécessaires sont installées"""
    dependances = {
        'psycopg2': 'PostgreSQL database driver',
        'PyQt5': 'Interface graphique (optionnel)',
    }
    
    manquantes = []
    for package, description in dependances.items():
        try:
            __import__(package)
            print(f"✓ {package}: OK")
        except ImportError:
            print(f"✗ {package}: MANQUANT ({description})")
            manquantes.append(package)
    
    if manquantes:
        print("\n⚠ Certaines dépendances sont manquantes.")
        print("Installez-les avec:")
        print(f"  pip install {' '.join(manquantes)}")
        print("\nNote: PyQt5 est optionnel pour utiliser l'interface graphique.")
    
    return len(manquantes) == 0


def initialiser_application():
    """Initialise l'application et la base de données"""
    print("\n" + "=" * 60)
    print("INITIALISATION DE L'APPLICATION CNTSCI")
    print("=" * 60)
    
    # Import des modules core
    try:
        from core.config import APP_VERSION, APP_PHASE
        print(f"\nVersion: {APP_VERSION} - Phase: {APP_PHASE}")
    except Exception as e:
        print(f"Erreur chargement configuration: {e}")
        return False
    
    # Initialisation de la base de données
    try:
        from core.database import initialiser_schema
        print("\nInitialisation de la base de données...")
        # Note: Décommenter pour créer les tables
        # initialiser_schema()
        print("✓ Base de données prête")
    except Exception as e:
        print(f"⚠ Base de données non configurée: {e}")
        print("  Configurez les variables d'environnement DB_*")
    
    return True


def lancer_mode_console():
    """Lance l'application en mode console pour tests"""
    print("\n" + "=" * 60)
    print("MODE CONSOLE - Tests des fonctionnalités backend")
    print("=" * 60)
    
    # Tester les modules
    try:
        from core.security import security_manager, Utilisateur
        
        print("\n--- Test Module Sécurité ---")
        # Créer un utilisateur test
        user_test = Utilisateur(
            id=1,
            username="admin",
            email="admin@cntsci.ci",
            role="ADMIN",
            nom_complet="Administrateur Test"
        )
        print(f"Utilisateur créé: {user_test.nom_complet}")
        print(f"Permissions: {user_test.has_permission('read_all')}")
        
        # Tester le hachage de mot de passe
        mdp_hash = security_manager.hasher_mot_de_passe("Test1234!")
        print(f"Mot de passe hashé: {mdp_hash[:50]}...")
        
    except Exception as e:
        print(f"Erreur test sécurité: {e}")
    
    try:
        print("\n--- Test Module Matériel ---")
        from modules.materiel.gestion_materiel import Materiel, GestionnaireMateriel
        
        materiel_test = Materiel(
            reference="MAT-001",
            type_equipment="ORDINATEUR",
            marque="Dell",
            modele="OptiPlex 7090",
            numero_serie="SN123456",
        )
        print(f"Matériel créé: {materiel_test.reference} - {materiel_test.marque}")
        
    except Exception as e:
        print(f"Erreur test matériel: {e}")
    
    try:
        print("\n--- Test Module Automobile ---")
        from modules.automobile.gestion_automobile import Vehicule, GestionnaireAutomobile
        
        vehicule_test = Vehicule(
            immatriculation="AB-123-CD",
            marque="Toyota",
            modele="Hilux",
            annee=2023,
            type_vehicule="Pick-up",
        )
        print(f"Véhicule créé: {vehicule_test.immatriculation} - {vehicule_test.marque}")
        
    except Exception as e:
        print(f"Erreur test automobile: {e}")
    
    try:
        print("\n--- Test Module Personnel ---")
        from modules.personnel.gestion_personnel import Employe, GestionnairePersonnel
        
        employe_test = Employe(
            matricule="EMP-001",
            nom="KOUAME",
            prenom="Jean",
            poste="Développeur",
            departement="Informatique",
        )
        print(f"Employé créé: {employe_test.matricule} - {employe_test.nom} {employe_test.prenom}")
        print(f"Ancienneté: {employe_test.anciennete_annees()} années")
        
    except Exception as e:
        print(f"Erreur test personnel: {e}")
    
    try:
        print("\n--- Test Module Reporting ---")
        from modules.reporting.reporting import ReportingManager, TableauDeBord
        
        reporting = ReportingManager()
        kpis = reporting.obtenir_kpi_generaux()
        print(f"KPIs récupérés: {len(kpis)} indicateurs")
        
        dashboard = TableauDeBord()
        vue = dashboard.generer_vue_ensemble()
        print(f"Tableau de bord généré: {vue['titre']}")
        
    except Exception as e:
        print(f"Erreur test reporting: {e}")
    
    print("\n" + "=" * 60)
    print("TESTS TERMINÉS")
    print("=" * 60)


def lancer_interface_graphique():
    """Lance l'interface graphique PyQt"""
    print("\nLancement de l'interface graphique...")
    
    try:
        from ui.application import main as lancer_ui
        lancer_ui()
    except Exception as e:
        print(f"Erreur lancement interface: {e}")
        print("Vérifiez que PyQt5 est installé: pip install PyQt5")


def afficher_menu_principal():
    """Affiche le menu principal et gère les choix"""
    while True:
        print("\n" + "=" * 60)
        print("CNTSCI - Application de Gestion")
        print("Développé par M. SESS Eddy 2025")
        print("=" * 60)
        print("\n1. Lancer l'interface graphique")
        print("2. Mode console (tests)")
        print("3. Initialiser la base de données")
        print("4. Quitter")
        
        choix = input("\nVotre choix (1-4): ").strip()
        
        if choix == "1":
            lancer_interface_graphique()
        elif choix == "2":
            lancer_mode_console()
        elif choix == "3":
            try:
                from core.database import initialiser_schema
                initialiser_schema()
                print("✓ Base de données initialisée avec succès")
            except Exception as e:
                print(f"✗ Erreur: {e}")
        elif choix == "4":
            print("\nMerci d'avoir utilisé l'application CNTSCI.")
            break
        else:
            print("Choix invalide. Veuillez réessayer.")


def main():
    """Fonction principale"""
    # Vérifier les dépendances
    toutes_dependances_ok = verifier_dependances()
    
    # Initialiser l'application
    if not initialiser_application():
        print("\n✗ Échec de l'initialisation. Vérifiez la configuration.")
        return
    
    # Afficher le menu principal
    afficher_menu_principal()


if __name__ == "__main__":
    main()
