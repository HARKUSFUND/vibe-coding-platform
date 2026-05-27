"""
Écran de connexion avec authentification renforcée (OTP).
Conforme CDC §5.4 - Authentification multi-facteurs
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap

from ...infrastructure.database.session import get_db_session
from ...core.services.auth_service import AuthService


class LoginScreen(QWidget):
    """Écran de connexion avec support OTP."""
    
    login_successful = pyqtSignal(dict)  # Émet les infos utilisateur après connexion
    
    def __init__(self):
        super().__init__()
        self.auth_service = None
        self.current_user = None
        self.otp_required = False
        self.temp_token = None  # Token temporaire après MDP valide
        self.init_ui()
    
    def init_ui(self):
        """Initialiser l'interface utilisateur."""
        self.setWindowTitle("IGORS - Connexion")
        self.setFixedSize(450, 550)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #333;
            }
            QLineEdit {
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                padding: 12px 24px;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 30, 40, 30)
        
        # Logo et titre
        logo_label = QLabel("IGORS")
        logo_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("color: #007bff; margin-bottom: 5px;")
        layout.addWidget(logo_label)
        
        subtitle = QLabel("Système de Gestion de Laboratoire\nCNTS Côte d'Ivoire")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #666; font-size: 12px; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Séparateur
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        separator.setFixedHeight(1)
        layout.addWidget(separator)
        
        # Formulaire de connexion
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Identifiant")
        self.username_input.returnPressed.connect(self.attempt_login)
        layout.addWidget(QLabel("Identifiant:"))
        layout.addWidget(self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Mot de passe")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.returnPressed.connect(self.attempt_login)
        layout.addWidget(QLabel("Mot de passe:"))
        layout.addWidget(self.password_input)
        
        # Champ OTP (caché par défaut)
        self.otp_frame = QFrame()
        self.otp_frame.setVisible(False)
        otp_layout = QVBoxLayout()
        
        self.otp_label = QLabel("Code OTP:")
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("Entrez le code à 6 chiffres")
        self.otp_input.setMaxLength(6)
        self.otp_input.returnPressed.connect(self.verify_otp)
        
        otp_layout.addWidget(self.otp_label)
        otp_layout.addWidget(self.otp_input)
        self.otp_frame.setLayout(otp_layout)
        layout.addWidget(self.otp_frame)
        
        # Bouton de connexion
        self.login_button = QPushButton("Se connecter")
        self.login_button.clicked.connect(self.attempt_login)
        self.login_button.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        layout.addWidget(self.login_button)
        
        # Lien mot de passe oublié
        forgot_password = QPushButton("Mot de passe oublié ?")
        forgot_password.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #007bff;
                text-decoration: underline;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: transparent;
                color: #0056b3;
            }
        """)
        forgot_password.clicked.connect(self.forgot_password)
        layout.addWidget(forgot_password, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Message d'état
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("color: #dc3545; font-size: 12px;")
        layout.addWidget(self.status_label)
        
        # Pied de page
        footer = QLabel("© 2026 CNTS - Tous droits réservés")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #999; font-size: 10px; margin-top: 20px;")
        layout.addWidget(footer)
        
        self.setLayout(layout)
    
    def attempt_login(self):
        """Tenter une connexion avec identifiants."""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            self.status_label.setText("Veuillez remplir tous les champs")
            return
        
        try:
            db = next(get_db_session())
            self.auth_service = AuthService(db)
            
            # Première étape: vérifier mot de passe
            result = self.auth_service.authentifier_user(username, password)
            
            if result is None:
                self.status_label.setText("Identifiant ou mot de passe incorrect")
                return
            
            user_data = result if isinstance(result, dict) else {
                'id': result.id,
                'identifiant': result.identifiant,
                'nom': result.nom,
                'role': result.role,
                'otp_actif': getattr(result, 'otp_actif', False),
                'otp_secret': getattr(result, 'otp_secret', None)
            }
            
            # Vérifier si OTP est requis
            if user_data.get('otp_actif'):
                self.otp_required = True
                self.temp_token = user_data  # Stocker temporairement
                self.show_otp_field()
                self.status_label.setText("Entrez le code OTP")
                self.otp_input.setFocus()
            else:
                # Connexion directe sans OTP
                self.login_successful.emit(user_data)
                
        except Exception as e:
            self.status_label.setText(f"Erreur de connexion: {str(e)}")
        finally:
            db.close()
    
    def show_otp_field(self):
        """Afficher le champ OTP."""
        self.otp_frame.setVisible(True)
        self.login_button.setText("Vérifier OTP")
        self.login_button.clicked.disconnect()
        self.login_button.clicked.connect(self.verify_otp)
        self.password_input.setEnabled(False)
        self.username_input.setEnabled(False)
    
    def verify_otp(self):
        """Vérifier le code OTP."""
        otp_code = self.otp_input.text().strip()
        
        if not otp_code:
            self.status_label.setText("Veuillez entrer le code OTP")
            return
        
        try:
            db = next(get_db_session())
            auth_service = AuthService(db)
            
            # Vérifier l'OTP avec le secret stocké
            user_id = self.temp_token.get('id')
            otp_secret = self.temp_token.get('otp_secret')
            
            if auth_service.verifier_otp(user_id, otp_code):
                # OTP valide - connexion réussie
                self.login_successful.emit(self.temp_token)
            else:
                self.status_label.setText("Code OTP invalide ou expiré")
                
        except Exception as e:
            self.status_label.setText(f"Erreur de vérification OTP: {str(e)}")
        finally:
            db.close()
    
    def forgot_password(self):
        """Gérer la demande de réinitialisation de mot de passe."""
        QMessageBox.information(
            self,
            "Mot de passe oublié",
            "Veuillez contacter l'administrateur système pour réinitialiser votre mot de passe."
        )
    
    def clear_fields(self):
        """Effacer tous les champs."""
        self.username_input.clear()
        self.password_input.clear()
        self.otp_input.clear()
        self.status_label.clear()
        self.otp_frame.setVisible(False)
        self.login_button.setText("Se connecter")
        self.login_button.clicked.disconnect()
        self.login_button.clicked.connect(self.attempt_login)
        self.username_input.setEnabled(True)
        self.password_input.setEnabled(True)
