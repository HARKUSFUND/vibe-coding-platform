"""
Point d'entrée principal de l'application UI PyQt6.
Initialise l'application, gère le cycle de vie et lance l'écran de connexion.
"""
import sys
import os
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt, QTranslator, QLocale, QTimer
from PyQt6.QtGui import QPixmap, QFont

from igors.config.settings import settings
from igors.ui.splash.splash_screen import SplashScreen
from igors.ui.auth.login_screen import LoginScreen
from igors.infrastructure.database.session import init_database, engine
from igors.infrastructure.security.hashing import get_password_hash
from igors.infrastructure.models.user import UserModel
from sqlalchemy.orm import Session


class IGORSApplication(QApplication):
    """Application principale IGORS."""
    
    def __init__(self):
        super().__init__(sys.argv)
        
        # Configuration de l'application
        self.setApplicationName("IGORS")
        self.setApplicationVersion("2.0.0")
        self.setOrganizationName("CNTS Côte d'Ivoire")
        self.setOrganizationDomain("cntsci.ci")
        
        # Style global
        self.setStyleSheet(self._load_stylesheet())
        
        # Police par défaut
        font = QFont("Segoe UI", 10)
        self.setFont(font)
        
        # Traductions (optionnel)
        self.translator = QTranslator()
        
        # Splash screen
        self.splash = None
        
        # Fenêtre de login
        self.login_window = None
    
    def _load_stylesheet(self) -> str:
        """Charger le stylesheet global depuis theme.py."""
        try:
            from igors.ui.theme import get_stylesheet
            return get_stylesheet()
        except Exception as e:
            print(f"Erreur chargement stylesheet: {e}")
            return ""
    
    def demarrer(self):
        """Démarrer l'application avec splash screen."""
        # Afficher le splash screen
        self.splash = SplashScreen()
        self.splash.show()
        self.processEvents()
        
        # Initialiser la base de données
        self.splash.set_message("Initialisation de la base de données...")
        self.processEvents()
        
        try:
            init_database()
            self.splash.set_message("Base de données prête")
            self.processEvents()
        except Exception as e:
            self.splash.set_message(f"Erreur BDD: {str(e)}")
            self.processEvents()
            import time
            time.sleep(2)
        
        # Créer un utilisateur admin par défaut s'il n'existe pas
        self._creer_admin_defaut()
        
        # Attendre un peu puis afficher le login
        QTimer.singleShot(2000, self.afficher_login)
    
    def _creer_admin_defaut(self):
        """Créer un utilisateur administrateur par défaut."""
        try:
            session = Session(bind=engine)
            
            # Vérifier s'il existe déjà des admins
            admin_existant = session.query(UserModel).filter(
                UserModel.role == 'administrateur'
            ).first()
            
            if not admin_existant:
                # Créer l'admin par défaut
                admin = UserModel(
                    identifiant="admin",
                    nom="Administrateur",
                    prenom="Système",
                    email="admin@cntsci.ci",
                    role="administrateur",
                    mot_de_passe_hash=get_password_hash("admin123"),
                    actif=True,
                    otp_secret=None
                )
                
                session.add(admin)
                session.commit()
                print("Utilisateur admin créé: admin / admin123")
            
            session.close()
        except Exception as e:
            print(f"Erreur création admin: {e}")
    
    def afficher_login(self):
        """Afficher l'écran de connexion."""
        if self.splash:
            self.splash.close()
        
        self.login_window = LoginScreen()
        self.login_window.show()
        
        # Connecter le signal de succès de login
        self.login_window.login_successful.connect(self.on_login_successful)
    
    def on_login_successful(self, user_data: dict):
        """Callback après succès du login."""
        print(f"Login réussi pour: {user_data.get('nom')}")


def main():
    """Point d'entrée principal."""
    os.environ['QT_AUTO_SCREEN_SCALE_FACTOR'] = '1'
    os.environ['QT_ENABLE_HIGHDPI_SCALING'] = '1'
    
    app = IGORSApplication()
    app.demarrer()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
