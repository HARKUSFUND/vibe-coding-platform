"""IGORS UI Application Entry Point."""

import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QTranslator, QLocale
from loguru import logger

from ...config.settings import get_settings
from .splash.splash_screen import SplashScreen


def setup_application() -> QApplication:
    """Configure and return the Qt application."""
    # Enable High DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("IGORS")
    app.setOrganizationName("CNTS CI")
    app.setStyle("Fusion")

    # Set application font
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    return app


def main():
    """Main entry point for IGORS UI."""
    # Configure logging
    logger.add(
        "logs/igors_ui_{time}.log",
        rotation="1 day",
        retention="30 days",
        level="INFO",
    )

    settings = get_settings()
    logger.info(f"Starting IGORS UI v{settings.app_version}")

    # Create application
    app = setup_application()

    # Show splash screen
    splash = SplashScreen()
    splash.show()

    # Continue with login after splash
    # This will be implemented in subsequent files
    # from .auth.login_screen import LoginScreen
    # login = LoginScreen()
    # login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
