"""
Application Bureau CNTSCI - Interface PyQt
Interface principale de l'application avec navigation et modules
"""

import sys
from datetime import datetime
from typing import Optional

# Vérification et import de PyQt5
try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QPushButton, QLabel, QStackedWidget, QFrame, QScrollArea,
        QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
        QFormLayout, QLineEdit, QTextEdit, QComboBox, QDateEdit,
        QSpinBox, QDoubleSpinBox, QFileDialog, QGroupBox, QTabWidget
    )
    from PyQt5.QtCore import Qt, QSize, QTimer
    from PyQt5.QtGui import QFont, QIcon, QColor, QPalette
    PYQT_AVAILABLE = True
except ImportError:
    PYQT_AVAILABLE = False
    print("PyQt5 non installé. Installation requise: pip install PyQt5")


class NavigationPanel(QFrame):
    """Panneau de navigation latéral"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(200)
        self.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                color: white;
            }
            QPushButton {
                background-color: transparent;
                color: white;
                text-align: left;
                padding: 10px;
                border: none;
                border-left: 4px solid transparent;
            }
            QPushButton:hover {
                background-color: #34495e;
            }
            QPushButton:checked {
                background-color: #3498db;
                border-left: 4px solid #2980b9;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 20, 0, 0)
        
        # Logo/Titre
        titre = QLabel("CNTSCI\nGestion")
        titre.setStyleSheet("font-size: 16px; font-weight: bold; padding: 15px;")
        titre.setAlignment(Qt.AlignCenter)
        layout.addWidget(titre)
        
        # Boutons de navigation
        self.boutons = {}
        menus = [
            ('accueil', '📊 Accueil'),
            ('materiel', '💻 Matériel'),
            ('automobile', '🚗 Automobile'),
            ('personnel', '👥 Personnel'),
            ('reporting', '📈 Reporting'),
            ('parametres', '⚙️ Paramètres'),
        ]
        
        for cle, texte in menus:
            btn = QPushButton(texte)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, c=cle: self.selectionner_menu(c))
            layout.addWidget(btn)
            self.boutons[cle] = btn
        
        layout.addStretch()
        self.setLayout(layout)
    
    def selectionner_menu(self, cle: str):
        """Sélectionne un menu et met à jour l'affichage"""
        for k, btn in self.boutons.items():
            btn.setChecked(k == cle)
        
        # Notifier le parent
        if hasattr(self.parent(), 'afficher_page'):
            self.parent().afficher_page(cle)


class PageAccueil(QWidget):
    """Page d'accueil avec tableau de bord"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        titre = QLabel("📊 Tableau de Bord - CNTSCI")
        titre.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(titre)
        
        # Zone de contenu
        contenu = QLabel("Chargement des indicateurs...")
        contenu.setStyleSheet("font-size: 14px; padding: 20px;")
        contenu.setWordWrap(True)
        layout.addWidget(contenu)
        
        self.setLayout(layout)
    
    def actualiser(self, kpis: dict = None):
        """Actualise l'affichage avec les KPIs"""
        if kpis:
            texte = f"""
            <h3>Indicateurs Clés</h3>
            <ul>
                <li><b>Matériel informatique:</b> {kpis.get('total_materiel', 0)} équipements</li>
                <li><b>Véhicules:</b> {kpis.get('total_vehicules', 0)} véhicules</li>
                <li><b>Effectif:</b> {kpis.get('effectif_total', 0)} employés</li>
                <li><b>Alertes critiques:</b> {kpis.get('alertes_critiques', 0)}</li>
            </ul>
            <p style='color: gray; margin-top: 20px;'>
                Dernière mise à jour: {datetime.now().strftime('%d/%m/%Y %H:%M')}
            </p>
            """
            self.findChild(QLabel).setText(texte)


class PageModule(QWidget):
    """Page générique pour un module"""
    
    def __init__(self, titre: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout()
        
        label_titre = QLabel(titre)
        label_titre.setStyleSheet("font-size: 24px; font-weight: bold; margin: 20px;")
        layout.addWidget(label_titre)
        
        contenu = QLabel(f"Module {titre} - En développement")
        contenu.setStyleSheet("font-size: 14px; padding: 20px;")
        layout.addWidget(contenu)
        
        self.setLayout(layout)


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNTSCI - Application de Gestion")
        self.setMinimumSize(1200, 800)
        
        # Widget central
        widget_central = QWidget()
        self.setCentralWidget(widget_central)
        
        # Layout principal
        layout_principal = QHBoxLayout()
        widget_central.setLayout(layout_principal)
        
        # Panneau de navigation
        self.navigation = NavigationPanel(self)
        layout_principal.addWidget(self.navigation)
        
        # Zone de contenu
        self.pile_pages = QStackedWidget()
        layout_principal.addWidget(self.pile_pages)
        
        # Initialisation des pages
        self.initialiser_pages()
        
        # Afficher la page d'accueil
        self.afficher_page('accueil')
        
        # Style global
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ecf0f1;
            }
            QStackedWidget {
                background-color: white;
                border-radius: 10px;
                margin: 10px;
            }
        """)
    
    def initialiser_pages(self):
        """Initialise toutes les pages de l'application"""
        self.pages = {
            'accueil': PageAccueil(self),
            'materiel': PageModule("Matériel Informatique", self),
            'automobile': PageModule("Parc Automobile", self),
            'personnel': PageModule("Gestion du Personnel", self),
            'reporting': PageModule("Reporting & KPIs", self),
            'parametres': PageModule("Paramètres", self),
        }
        
        for page in self.pages.values():
            self.pile_pages.addWidget(page)
    
    def afficher_page(self, cle: str):
        """Affiche une page spécifique"""
        if cle in self.pages:
            index = list(self.pages.keys()).index(cle)
            self.pile_pages.setCurrentIndex(index)
            
            # Actualiser si nécessaire
            if cle == 'accueil' and hasattr(self.pages[cle], 'actualiser'):
                # Ici, charger les vrais KPIs depuis le backend
                self.pages[cle].actualiser()


def lancer_application():
    """Lance l'application PyQt"""
    if not PYQT_AVAILABLE:
        print("Erreur: PyQt5 n'est pas installé.")
        print("Installez-le avec: pip install PyQt5")
        return None
    
    app = QApplication(sys.argv)
    
    # Configuration de la police
    police = QFont("Arial", 10)
    app.setFont(police)
    
    # Création de la fenêtre principale
    fenetre = MainWindow()
    fenetre.show()
    
    return app, fenetre


def main():
    """Point d'entrée principal"""
    print("=" * 60)
    print("CNTSCI - Application de Gestion")
    print("Développé par M. SESS Eddy 2025")
    print("Version 1.0 - Phase V1")
    print("=" * 60)
    
    result = lancer_application()
    
    if result:
        app, fenetre = result
        sys.exit(app.exec_())
    else:
        print("\nMode console disponible pour tests backend.")
        print("Importez les modules pour tester les fonctionnalités.")


if __name__ == "__main__":
    main()
