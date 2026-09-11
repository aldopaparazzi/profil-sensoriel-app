# ui_splash.py
"""
Splash screen affiché pendant le démarrage de l'application
(le temps que Qt/WebEngine s'initialisent, que le workspace soit vérifié, etc).
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from ui import APP_BUILD, APP_NAME, APP_VERSION


def show_splash_old(app: QApplication, message: str = "Démarrage...") -> QSplashScreen:
    """
    Crée et affiche un splash screen simple (pas besoin d'image externe).
    Retourne l'objet splash : à fermer avec splash.finish(main_window).
    """
    pixmap = QPixmap(480, 280)
    pixmap.fill(QColor("#2c3e50"))

    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))

    title_font = QFont("Segoe UI", 22, QFont.Bold)
    painter.setFont(title_font)
    painter.drawText(
        pixmap.rect().adjusted(0, -30, 0, 0), Qt.AlignCenter, "Profil Sensoriel"
    )

    subtitle_font = QFont("Segoe UI", 11)
    painter.setFont(subtitle_font)
    painter.drawText(pixmap.rect().adjusted(0, 40, 0, 0), Qt.AlignCenter, message)

    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()  # force l'affichage immédiat
    return splash

def show_splash(
    app: QApplication,
    message: str = "Démarrage...",
    version: str = APP_VERSION,
    build: str = APP_BUILD,
) -> QSplashScreen:
    """
    Crée et affiche un splash screen simple.
    Retourne l'objet splash : à fermer avec splash.finish(main_window).
    """
    pixmap = QPixmap(480, 280)
    pixmap.fill(QColor("#2c3e50"))

    painter = QPainter(pixmap)
    painter.setPen(QColor("white"))

    # Titre
    title_font = QFont("Segoe UI", 22, QFont.Bold)
    painter.setFont(title_font)
    painter.drawText(
        pixmap.rect().adjusted(0, -30, 0, 0),
        Qt.AlignCenter,
        APP_NAME,
    )

    # Message
    subtitle_font = QFont("Segoe UI", 11)
    painter.setFont(subtitle_font)
    painter.drawText(
        pixmap.rect().adjusted(0, 40, 0, 0),
        Qt.AlignCenter,
        message,
    )

    # Version / Build — discret, en bas à droite
    version_font = QFont("Segoe UI", 8)
    painter.setFont(version_font)
    painter.setPen(QColor("#95a5a6"))

    version_text = f"v{version} • build {build}"

    painter.drawText(
        pixmap.rect().adjusted(0, 0, -12, -8),
        Qt.AlignRight | Qt.AlignBottom,
        version_text,
    )

    painter.end()

    splash = QSplashScreen(pixmap)
    splash.setWindowFlag(Qt.WindowStaysOnTopHint)
    splash.show()
    app.processEvents()

    return splash


def update_splash_message(splash: QSplashScreen, message: str):
    """Met à jour le texte affiché sur le splash (optionnel, pendant le chargement)."""
    splash.showMessage(
        message,
        Qt.AlignBottom | Qt.AlignHCenter,
        QColor("white"),
    )
    QApplication.processEvents()
