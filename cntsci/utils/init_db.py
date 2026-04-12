#!/usr/bin/env python
"""Script d'initialisation de la base de données CNTSCI"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['DB_PASSWORD'] = 'cntsci2025'

from core.database import db_manager, initialiser_schema
from core.security import SecurityManager
import hashlib
import secrets

def initialiser_db():
    """Initialise la base de données avec les tables et l'admin par défaut"""
    
    print("=" * 60)
    print("INITIALISATION DE LA BASE DE DONNEES CNTSCI")
    print("=" * 60)
    
    # Créer les tables
    print("\n[1/3] Création des tables...")
    initialiser_schema()
    print("Tables créées avec succès")
    
    # Créer l'utilisateur admin par défaut
    print("\n[2/3] Création de l'utilisateur administrateur...")
    
    sel = secrets.token_hex(16)
    pwd_hash = sel + '$' + hashlib.sha256((sel + 'Admin123!').encode()).hexdigest()
    
    try:
        db_manager.executer_requete(
            "INSERT INTO utilisateurs (username, email, mot_de_passe_hash, role, nom_complet) VALUES (%s, %s, %s, %s, %s)",
            ('admin', 'admin@cntsci.ci', pwd_hash, 'DG', 'Administrateur'),
            fetch=False,
            commit=True
        )
        print("Utilisateur admin créé avec succès")
        print("  - Username: admin")
        print("  - Mot de passe: Admin123!")
    except Exception as e:
        if "duplicate" in str(e).lower():
            print("L'utilisateur admin existe déjà")
        else:
            print(f"Erreur: {e}")
    
    # Ajouter des données de test
    print("\n[3/3] Ajout de données de démonstration...")
    
    # Un employé de test
    try:
        db_manager.executer_requete(
            "INSERT INTO employes (matricule, nom, prenom, poste, departement, date_embauche, type_contrat) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ('EMP001', 'KOUAME', 'Jean', 'Développeur', 'Informatique', '2024-01-15', 'CDI'),
            fetch=False,
            commit=True
        )
        print("Employé de test ajouté: Jean KOUAME")
    except Exception as e:
        if "duplicate" not in str(e).lower():
            print(f"Erreur employé: {e}")
    
    # Un véhicule de test
    try:
        db_manager.executer_requete(
            "INSERT INTO vehicules (immatriculation, marque, modele, annee, type_vehicule, date_assurance, date_fin_assurance, compagnie_assurance) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
            ('AB-123-CD', 'Toyota', 'Land Cruiser', 2023, 'SUV', '2024-01-01', '2025-01-01', 'NSIA Assurance'),
            fetch=False,
            commit=True
        )
        print("Véhicule de test ajouté: Toyota Land Cruiser (AB-123-CD)")
    except Exception as e:
        if "duplicate" not in str(e).lower():
            print(f"Erreur véhicule: {e}")
    
    # Un équipement de test
    try:
        db_manager.executer_requete(
            "INSERT INTO materiel_informatique (reference, type_equipment, marque, modele, etat, localisation) VALUES (%s, %s, %s, %s, %s, %s)",
            ('MAT-001', 'Ordinateur', 'Dell', 'Latitude 5520', 'NEUF', 'Bureau DRH'),
            fetch=False,
            commit=True
        )
        print("Équipement de test ajouté: Dell Latitude 5520")
    except Exception as e:
        if "duplicate" not in str(e).lower():
            print(f"Erreur matériel: {e}")
    
    print("\n" + "=" * 60)
    print("INITIALISATION TERMINEE AVEC SUCCES")
    print("=" * 60)
    print("\nVous pouvez maintenant lancer l'application avec:")
    print("  python main.py")
    print("\nIdentifiants par défaut:")
    print("  Username: admin")
    print("  Mot de passe: Admin123!")
    print("=" * 60)

if __name__ == '__main__':
    initialiser_db()
