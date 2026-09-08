# ui/ui_home.py
"""Page d'accueil de l'application Profil Sensoriel."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class HomePage(QWidget):
    """Page d'accueil principale."""

    fetch_requested = Signal()
    settings_requested = Signal()
    open_report_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 50, 60, 50)
        layout.setSpacing(20)

        # --------------------------------------------------
        # Titre
        # --------------------------------------------------

        title = QLabel("Profil Sensoriel")
        title.setStyleSheet(
            """
            QLabel {
                font-size: 32px;
                font-weight: 600;
                color: #1A1916;
            }
            """
        )
        layout.addWidget(title)

        subtitle = QLabel("Consultation et gestion des profils sensoriels.")
        subtitle.setStyleSheet(
            """
            QLabel {
                font-size: 17px;
                color: #6B6860;
            }
            """
        )
        layout.addWidget(subtitle)

        layout.addSpacing(25)

        # --------------------------------------------------
        # Actions
        # --------------------------------------------------

        actions = QHBoxLayout()
        actions.setSpacing(15)

        self.btn_fetch = QPushButton("📥 Récupérer les formulaires")
        self.btn_settings = QPushButton("⚙ Configuration")
        self.btn_reports = QPushButton("📁 Ouvrir le dossier Rapports")

        for button in (
            self.btn_fetch,
            self.btn_settings,
            self.btn_reports,
        ):
            button.setMinimumHeight(55)
            button.setMinimumWidth(220)

        actions.addWidget(self.btn_fetch)
        actions.addWidget(self.btn_settings)
        actions.addWidget(self.btn_reports)

        layout.addLayout(actions)

        # --------------------------------------------------
        # Zone d'information
        # --------------------------------------------------

        info = QFrame()
        info.setStyleSheet(
            """
            QFrame {
                background: #F5F3EE;
                border-radius: 8px;
            }
            """
        )

        info_layout = QVBoxLayout(info)
        info_layout.setContentsMargins(20, 16, 20, 16)

        info_title = QLabel("Bienvenue")
        info_title.setStyleSheet(
            """
            QLabel {
                font-size: 16px;
                font-weight: 600;
                color: #1A1916;
            }
            """
        )

        info_text = QLabel(
            "Utilisez les actions ci-dessus pour récupérer de nouveaux "
            "formulaires, modifier la configuration ou accéder aux "
            "données de l'application."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet(
            """
            QLabel {
                font-size: 14px;
                color: #6B6860;
            }
            """
        )

        info_layout.addWidget(info_title)
        info_layout.addWidget(info_text)

        layout.addWidget(info)

        layout.addStretch()

        # --------------------------------------------------
        # Version
        # --------------------------------------------------

        version = QLabel("Profil Sensoriel · V1.5")
        version.setStyleSheet(
            """
            QLabel {
                font-size: 12px;
                color: #8A8780;
            }
            """
        )
        layout.addWidget(version)

        # --------------------------------------------------
        # Signaux
        # --------------------------------------------------

        self.btn_fetch.clicked.connect(self.fetch_requested)
        self.btn_settings.clicked.connect(self.settings_requested)
        self.btn_reports.clicked.connect(self.open_report_requested)
