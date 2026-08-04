# ui_splash.py
"""
Splash screen affiché pendant le démarrage de l'application
(le temps que Qt/WebEngine s'initialisent, que le workspace soit vérifié, etc).
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen


def show_splash(app: QApplication, message: str = "Démarrage...") -> QSplashScreen:
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


def update_splash_message(splash: QSplashScreen, message: str):
    """Met à jour le texte affiché sur le splash (optionnel, pendant le chargement)."""
    splash.showMessage(
        message,
        Qt.AlignBottom | Qt.AlignHCenter,
        QColor("white"),
    )
    QApplication.processEvents()
