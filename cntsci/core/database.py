"""
Module de base de données pour l'application CNTSCI
Gère les connexions et opérations PostgreSQL
"""

import psycopg2
from psycopg2 import pool, extras
from typing import Optional, List, Dict, Any, Tuple
from contextlib import contextmanager
import logging

from core.config import DATABASE_CONFIG

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gestionnaire de connexions à la base de données PostgreSQL"""
    
    _instance: Optional['DatabaseManager'] = None
    _pool: Optional[pool.ThreadedConnectionPool] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._pool is None:
            self._initialiser_pool()
    
    def _initialiser_pool(self) -> None:
        """Initialise le pool de connexions"""
        try:
            self._pool = pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=10,
                host=DATABASE_CONFIG['host'],
                port=DATABASE_CONFIG['port'],
                database=DATABASE_CONFIG['database'],
                user=DATABASE_CONFIG['user'],
                password=DATABASE_CONFIG['password'],
            )
            logger.info("Pool de connexions initialisé avec succès")
        except Exception as e:
            logger.error(f"Erreur initialisation pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Context manager pour obtenir une connexion"""
        conn = None
        try:
            conn = self._pool.getconn()
            yield conn
        finally:
            if conn:
                self._pool.putconn(conn)
    
    @contextmanager
    def get_cursor(self, commit: bool = False):
        """Context manager pour obtenir un curseur"""
        with self.get_connection() as conn:
            cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Erreur transaction: {e}")
                raise
            finally:
                cursor.close()
    
    def executer_requete(self, query: str, params: tuple = (), 
                        fetch: bool = True, commit: bool = False) -> Any:
        """
        Exécute une requête SQL
        :param query: Requête SQL avec placeholders %s
        :param params: Paramètres de la requête
        :param fetch: Si True, retourne les résultats
        :param commit: Si True, valide la transaction
        :return: Résultats ou nombre de lignes affectées
        """
        try:
            with self.get_cursor(commit=commit) as cursor:
                cursor.execute(query, params)
                
                if fetch:
                    result = cursor.fetchall()
                    return result
                else:
                    return cursor.rowcount
        except Exception as e:
            logger.error(f"Erreur exécution requête: {e}")
            raise
    
    def executer_transaction(self, operations: List[Tuple[str, tuple]]) -> bool:
        """
        Exécute une série d'opérations dans une transaction
        :param operations: Liste de tuples (query, params)
        :return: True si succès
        """
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                try:
                    for query, params in operations:
                        cursor.execute(query, params)
                    conn.commit()
                    logger.info("Transaction réussie")
                    return True
                except Exception as e:
                    conn.rollback()
                    logger.error(f"Échec transaction: {e}")
                    raise
                finally:
                    cursor.close()
        except Exception as e:
            logger.error(f"Erreur gestion transaction: {e}")
            return False
    
    def fermer_connexions(self) -> None:
        """Ferme toutes les connexions du pool"""
        if self._pool:
            self._pool.closeall()
            logger.info("Toutes les connexions fermées")


# Instance singleton
db_manager = DatabaseManager()


def initialiser_schema() -> None:
    """Initialise le schéma de la base de données"""
    
    # Table utilisateurs
    create_utilisateurs = """
    CREATE TABLE IF NOT EXISTS utilisateurs (
        id SERIAL PRIMARY KEY,
        username VARCHAR(50) UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        mot_de_passe_hash VARCHAR(255) NOT NULL,
        role VARCHAR(50) NOT NULL,
        nom_complet VARCHAR(100) NOT NULL,
        est_actif BOOLEAN DEFAULT TRUE,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        derniere_connexion TIMESTAMP,
        tentatives_echec INTEGER DEFAULT 0,
        verrouille_jusqu_a TIMESTAMP
    );
    """
    
    # Table matériel informatique
    create_materiel = """
    CREATE TABLE IF NOT EXISTS materiel_informatique (
        id SERIAL PRIMARY KEY,
        reference VARCHAR(50) UNIQUE NOT NULL,
        type_equipment VARCHAR(50) NOT NULL,
        marque VARCHAR(50),
        modele VARCHAR(100),
        numero_serie VARCHAR(100),
        date_acquisition DATE,
        date_garantie DATE,
        etat VARCHAR(20) DEFAULT 'NEUF',
        localisation VARCHAR(100),
        affecte_a INTEGER,
        date_derniere_maintenance DATE,
        notes TEXT,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (affecte_a) REFERENCES utilisateurs(id)
    );
    """
    
    # Table maintenances matériel
    create_maintenances_materiel = """
    CREATE TABLE IF NOT EXISTS maintenances_materiel (
        id SERIAL PRIMARY KEY,
        materiel_id INTEGER NOT NULL,
        type_maintenance VARCHAR(50) NOT NULL,
        description TEXT,
        technicien VARCHAR(100),
        cout DECIMAL(10, 2),
        date_intervention DATE,
        date_prochaine_maintenance DATE,
        statut VARCHAR(20) DEFAULT 'PLANIFIEE',
        FOREIGN KEY (materiel_id) REFERENCES materiel_informatique(id)
    );
    """
    
    # Table véhicules
    create_vehicules = """
    CREATE TABLE IF NOT EXISTS vehicules (
        id SERIAL PRIMARY KEY,
        immatriculation VARCHAR(20) UNIQUE NOT NULL,
        marque VARCHAR(50),
        modele VARCHAR(100),
        annee INTEGER,
        numero_chassis VARCHAR(50),
        type_vehicule VARCHAR(50),
        kilometrage INTEGER DEFAULT 0,
        date_acquisition DATE,
        date_assurance DATE,
        date_fin_assurance DATE,
        compagnie_assurance VARCHAR(100),
        numero_police_assurance VARCHAR(50),
        date_derniere_maintenance DATE,
        prochaine_maintenance_km INTEGER,
        etat VARCHAR(20) DEFAULT 'BON',
        affecte_a INTEGER,
        notes TEXT,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (affecte_a) REFERENCES utilisateurs(id)
    );
    """
    
    # Table maintenances véhicules
    create_maintenances_vehicules = """
    CREATE TABLE IF NOT EXISTS maintenances_vehicules (
        id SERIAL PRIMARY KEY,
        vehicule_id INTEGER NOT NULL,
        type_maintenance VARCHAR(50) NOT NULL,
        description TEXT,
        garagiste VARCHAR(100),
        cout DECIMAL(10, 2),
        kilometrage_intervention INTEGER,
        date_intervention DATE,
        prochaine_maintenance_km INTEGER,
        prochaine_maintenance_date DATE,
        statut VARCHAR(20) DEFAULT 'PLANIFIEE',
        FOREIGN KEY (vehicule_id) REFERENCES vehicules(id)
    );
    """
    
    # Table employés
    create_employes = """
    CREATE TABLE IF NOT EXISTS employes (
        id SERIAL PRIMARY KEY,
        matricule VARCHAR(20) UNIQUE NOT NULL,
        nom VARCHAR(50) NOT NULL,
        prenom VARCHAR(50) NOT NULL,
        date_naissance DATE,
        lieu_naissance VARCHAR(100),
        nationalite VARCHAR(50),
        adresse TEXT,
        telephone VARCHAR(20),
        email VARCHAR(100),
        poste VARCHAR(100),
        departement VARCHAR(100),
        date_embauche DATE,
        type_contrat VARCHAR(50),
        salaire DECIMAL(10, 2),
        statut VARCHAR(20) DEFAULT 'ACTIF',
        utilisateur_id INTEGER,
        notes TEXT,
        date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
    );
    """
    
    # Table congés/absences
    create_conges = """
    CREATE TABLE IF NOT EXISTS conges_absences (
        id SERIAL PRIMARY KEY,
        employe_id INTEGER NOT NULL,
        type_conge VARCHAR(50) NOT NULL,
        date_debut DATE NOT NULL,
        date_fin DATE NOT NULL,
        nombre_jours INTEGER,
        motif TEXT,
        statut VARCHAR(20) DEFAULT 'EN_ATTENTE',
        date_demande TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        date_validation TIMESTAMP,
        valide_par INTEGER,
        commentaires TEXT,
        FOREIGN KEY (employe_id) REFERENCES employes(id),
        FOREIGN KEY (valide_par) REFERENCES utilisateurs(id)
    );
    """
    
    # Table journal audit
    create_journal_audit = """
    CREATE TABLE IF NOT EXISTS journal_audit (
        id SERIAL PRIMARY KEY,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        utilisateur_id INTEGER,
        utilisateur_nom VARCHAR(100),
        action VARCHAR(50) NOT NULL,
        details TEXT,
        succes BOOLEAN DEFAULT TRUE,
        adresse_ip VARCHAR(45),
        FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
    );
    """
    
    # Exécuter la création des tables
    tables = [
        create_utilisateurs,
        create_materiel,
        create_maintenances_materiel,
        create_vehicules,
        create_maintenances_vehicules,
        create_employes,
        create_conges,
        create_journal_audit,
    ]
    
    db_manager = DatabaseManager()
    
    for table_query in tables:
        try:
            db_manager.executer_requete(table_query, fetch=False, commit=True)
            logger.info(f"Table créée: {table_query.split()[3]}")
        except Exception as e:
            logger.error(f"Erreur création table: {e}")
