"""Splash screen for IGORS application."""

from PyQt6.QtWidgets import QSplashScreen, QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QFont


class SplashScreen(QSplashScreen):
    """IGORS Application Splash Screen."""

    def __init__(self):
        # Create a custom splash with logo and info
        super().__init__()

        # Set dimensions
        self.setFixedSize(600, 400)

        # Create central widget
        central_widget = QWidget(self)
        layout = QVBoxLayout(central_widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Title label
        title = QLabel("IGORS")
        title.setFont(QFont("Arial", 36, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: #1a5f7a; margin: 20px;")

        # Subtitle
        subtitle = QLabel("Information de Gestion des Opérations\nde Routage et de Suivi")
        subtitle.setFont(QFont("Arial", 14))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: #555; margin: 10px;")

        # Organization
        org_label = QLabel("CNTS Côte d'Ivoire")
        org_label.setFont(QFont("Arial", 12))
        org_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        org_label.setStyleSheet("color: #333; margin: 10px;")

        # Version
        version_label = QLabel("Version 2.0.0")
        version_label.setFont(QFont("Arial", 10))
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #888;")

        # Add to layout
        layout.addWidget(title)
        layout.addWidget(subtitle)
        layout.addWidget(org_label)
        layout.addWidget(version_label)

        # Set window flags
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint
        )

        # Auto-close after 2 seconds
        QTimer.singleShot(2000, self.close)

    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.showMessage(
            "Chargement des modules...",
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            Qt.GlobalColor.white,
        )
